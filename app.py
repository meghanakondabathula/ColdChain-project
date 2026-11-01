from datetime import timedelta
from flask_wtf.csrf import CSRFProtect, CSRFError
import os
import sqlite3
from pathlib import Path

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    flash,
    send_file
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from auth import (
    init_auth_db,
    get_user,
    authenticate,
    create_user,
    list_users,
    ROLES,
    roles_required
)

from deviation_manager import (
    init_db,
    create_deviation,
    update_deviation,
    list_deviations,
    get_deviation
)

from report_generator import (
    generate_shipment_pdf,
    generate_deviation_pdf,
    generate_audit_history_pdf
)


# 1. FLASK APPLICATION SETUP

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "output" / "coldchain.sqlite"

if not DB_PATH.is_file():
    raise FileNotFoundError(
        f"Database not found: {DB_PATH}"
    )

# Initialize separate databases
init_db()
init_auth_db()

app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY"
)

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "Set FLASK_SECRET_KEY before starting Flask"
    )

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # Local HTTP development only
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_TIME_LIMIT=3600
)

csrf = CSRFProtect(app)


@app.before_request
def configure_session():
    from flask import session

    if current_user.is_authenticated:
        session.permanent = True


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "CSRF validation failed",
            "details": error.description
        }), 400

    return (
        f"CSRF validation failed: {error.description}",
        400
    )


# 2. FLASK-LOGIN CONFIGURATION
login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)


@login_manager.unauthorized_handler
def unauthorized():

    if request.path.startswith("/api/"):
        return jsonify({
            "error": "Login required"
        }), 401

    return redirect(url_for("login"))


# 3. DATABASE CONNECTION
def get_db_connection():

    conn = sqlite3.connect(
        DB_PATH.as_uri() + "?mode=ro",
        uri=True
    )

    conn.row_factory = sqlite3.Row

    return conn


# 4. MAIN DASHBOARD
@app.route("/")
@login_required
def dashboard():

    return render_template("dashboard.html")

# 5. DASHBOARD STATISTICS API
@app.route("/api/dashboard")
@login_required
def dashboard_data():

    with get_db_connection() as conn:

        shipments = conn.execute("""
            SELECT COUNT(*)
            FROM Shipment
        """).fetchone()[0]

        loggers = conn.execute("""
            SELECT COUNT(*)
            FROM Logger
        """).fetchone()[0]

        readings = conn.execute("""
            SELECT COUNT(*)
            FROM TemperatureReading
        """).fetchone()[0]

        results = conn.execute("""
            SELECT
                decision,
                COUNT(*) AS total
            FROM ExcursionReport
            GROUP BY decision
        """).fetchall()

    decisions = {
        "PASS": 0,
        "REVIEW": 0,
        "FAIL": 0
    }

    for row in results:
        decisions[row["decision"]] = row["total"]

    pass_rate = (
        round(
            decisions["PASS"] / shipments * 100,
            2
        )
        if shipments else 0
    )

    return jsonify({
        "shipments": shipments,
        "loggers": loggers,
        "readings": readings,
        "decisions": decisions,
        "pass_rate": pass_rate
    })

# 6. SHIPMENT LIST API
@app.route("/api/shipments")
@login_required
def get_shipments():

    search = request.args.get(
        "search", ""
    ).strip()

    status = request.args.get(
        "status", ""
    ).strip().upper()

    page = request.args.get(
        "page", 1, type=int
    )

    page = max(1, min(page, 100000))

    limit = 20
    offset = (page - 1) * limit

    conditions = []
    params = []

    # Shipment ID search
    if search:
        conditions.append(
            "s.shipment_id LIKE ?"
        )
        params.append(f"%{search}%")

    # Compliance decision filter
    if status in ("PASS", "REVIEW", "FAIL"):
        conditions.append(
            "e.decision = ?"
        )
        params.append(status)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    from_clause = """
        FROM Shipment s

        JOIN ExcursionReport e
            ON s.shipment_id = e.shipment_id

        JOIN Lot l
            ON s.lot_id = l.lot_id

        JOIN Product p
            ON l.product_id = p.product_id
    """

    with get_db_connection() as conn:

        total = conn.execute(
            "SELECT COUNT(*) "
            + from_clause
            + where_clause,
            params
        ).fetchone()[0]

        rows = conn.execute("""
            SELECT
                s.shipment_id,
                p.name AS product,
                s.route,
                s.state,
                e.decision,
                e.issue_types,
                e.excursion_minutes,
                e.missing_intervals
        """
        + from_clause
        + where_clause
        + """
            ORDER BY s.shipment_id
            LIMIT ? OFFSET ?
        """,
        params + [limit, offset]
        ).fetchall()

    return jsonify({
        "shipments": [
            dict(row) for row in rows
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    })

# 7. SHIPMENT DETAILS PAGE
@app.route("/shipment/<shipment_id>")
@login_required
def shipment_details(shipment_id):

    return render_template(
        "shipment_details.html",
        shipment_id=shipment_id
    )

# 8. SHIPMENT DETAILS DATA HELPER
def fetch_shipment_details(shipment_id):
    """
    Retrieve shipment information from the
    original read-only coldchain database.

    Returns a dictionary or None.
    """

    with get_db_connection() as conn:

        # Shipment, product, policy and report
        shipment = conn.execute("""
            SELECT
                s.*,
                l.product_id,
                p.name AS product_name,

                e.report_id,
                e.decision,
                e.issue_types,
                e.excursion_minutes,
                e.missing_intervals,
                e.evidence_json,
                e.generated_at,

                tp.min_c,
                tp.max_c,
                tp.allowed_excursion_min,
                tp.max_gap_min,
                tp.max_custody_gap_min,
                tp.effective_from,
                tp.effective_to

            FROM Shipment s

            JOIN Lot l
                ON s.lot_id = l.lot_id

            JOIN Product p
                ON l.product_id = p.product_id

            LEFT JOIN ExcursionReport e
                ON s.shipment_id = e.shipment_id

            LEFT JOIN ThresholdPolicy tp
                ON s.policy_id = tp.policy_id

            WHERE s.shipment_id = ?
        """, (shipment_id,)).fetchone()

        if shipment is None:
            return None

        # Temperature readings
        readings = conn.execute("""
            SELECT
                reading_id,
                logger_id,
                recorded_at,
                temperature_c,
                quality

            FROM TemperatureReading

            WHERE shipment_id = ?

            ORDER BY recorded_at, reading_id
        """, (shipment_id,)).fetchall()

        # Logger assignments
        assignments = conn.execute("""
            SELECT
                assignment_id,
                logger_id,
                assigned_at,
                unassigned_at,
                state

            FROM ShipmentLogger

            WHERE shipment_id = ?

            ORDER BY assigned_at
        """, (shipment_id,)).fetchall()

        # Custody events
        custody = conn.execute("""
            SELECT
                custody_id,
                event_at,
                actor,
                event_type,
                location

            FROM CustodyEvent

            WHERE shipment_id = ?

            ORDER BY event_at
        """, (shipment_id,)).fetchall()

        # Route stops
        stops = conn.execute("""
            SELECT
                stop_id,
                sequence_no,
                location,
                arrived_at,
                departed_at,
                dwell_min

            FROM RouteStop

            WHERE shipment_id = ?

            ORDER BY sequence_no
        """, (shipment_id,)).fetchall()

        return {
            "shipment": dict(shipment),

            "readings": [
                dict(row) for row in readings
            ],

            "assignments": [
                dict(row) for row in assignments
            ],

            "custody": [
                dict(row) for row in custody
            ],

            "stops": [
                dict(row) for row in stops
            ]
        }


# --------------------------------------------------
# 9. SHIPMENT DETAILS API
# --------------------------------------------------

@app.route("/api/shipments/<shipment_id>/details")
@login_required
def shipment_details_api(shipment_id):

    details = fetch_shipment_details(shipment_id)

    if details is None:
        return jsonify({
            "error": "Shipment not found"
        }), 404

    return jsonify(details)

# 10. SHIPMENT COMPLIANCE PDF DOWNLOAD
@app.route("/api/shipments/<shipment_id>/report")
@login_required
def download_shipment_report(shipment_id):

    # Retrieve shipment information
    details = fetch_shipment_details(shipment_id)

    if details is None:
        return jsonify({
            "error": "Shipment not found"
        }), 404

    # Generate PDF report
    pdf_buffer = generate_shipment_pdf(
        shipment_id,
        details
    )

    # Return PDF for download
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=(
            f"Shipment_{shipment_id}_Compliance_Report.pdf"
        )
    )

# 11. DEVIATION MANAGEMENT PAGE
@app.route("/deviations")
@login_required
def deviations_page():

    return render_template("deviations.html")

# 12. LIST DEVIATIONS API
@app.route("/api/deviations", methods=["GET"])
@login_required
def deviations_list_api():

    return jsonify(list_deviations())

# 13. CREATE DEVIATION API
@app.route("/api/deviations", methods=["POST"])
@login_required
@roles_required(
    "ADMIN",
    "QUALITY_MANAGER",
    "QUALITY_ANALYST"
)
def deviations_create_api():

    data = request.get_json(silent=True) or {}

    shipment_id = str(
        data.get("shipment_id", "")
    ).strip()

    actor = current_user.username

    if not shipment_id:
        return jsonify({
            "error": "Shipment ID is required"
        }), 400

    with get_db_connection() as conn:

        report = conn.execute("""
            SELECT
                report_id,
                shipment_id,
                decision

            FROM ExcursionReport

            WHERE shipment_id = ?
        """, (shipment_id,)).fetchone()

    if report is None:
        return jsonify({
            "error": "Compliance report not found"
        }), 404

    if report["decision"] not in ("FAIL", "REVIEW"):
        return jsonify({
            "error": (
                "Only FAIL or REVIEW shipments "
                "can be investigated"
            )
        }), 400

    try:
        result = create_deviation(
            report["shipment_id"],
            report["report_id"],
            report["decision"],
            actor
        )

        return jsonify(result), 201

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

# 14. DEVIATION DETAILS API
@app.route("/api/deviations/<int:deviation_id>")
@login_required
def deviation_details_api(deviation_id):

    result = get_deviation(deviation_id)

    if result is None:
        return jsonify({
            "error": "Deviation not found"
        }), 404

    return jsonify(result)

# DEVIATION INVESTIGATION PDF DOWNLOAD
@app.route("/api/deviations/<int:deviation_id>/report")
@login_required
def download_deviation_report(deviation_id):

    result = get_deviation(deviation_id)

    if result is None:
        return jsonify({
            "error": "Deviation not found"
        }), 404

    pdf_buffer = generate_deviation_pdf(result)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=(
            f"Deviation_{deviation_id}_Investigation_Report.pdf"
        )
    )

# DEVIATION AUDIT HISTORY PDF DOWNLOAD
@app.route("/api/deviations/<int:deviation_id>/audit-report")
@login_required
def download_audit_history_report(deviation_id):

    result = get_deviation(deviation_id)

    if result is None:
        return jsonify({
            "error": "Deviation not found"
        }), 404

    pdf_buffer = generate_audit_history_pdf(result)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=(
            f"Deviation_{deviation_id}_Audit_History.pdf"
        )
    )

# 15. UPDATE DEVIATION STATUS API
@app.route(
    "/api/deviations/<int:deviation_id>/status",
    methods=["POST"]
)
@login_required
@roles_required(
    "ADMIN",
    "QUALITY_MANAGER",
    "QUALITY_ANALYST"
)
def deviation_status_api(deviation_id):

    data = request.get_json(silent=True) or {}

    new_status = str(
        data.get("status", "")
    ).strip().upper()

    # Only Admin and Quality Manager can close
    if new_status == "CLOSED":

        if current_user.role not in (
            "ADMIN",
            "QUALITY_MANAGER"
        ):
            return jsonify({
                "error": (
                    "Only an administrator or "
                    "quality manager can close deviations"
                )
            }), 403

    try:
        result = update_deviation(
            deviation_id=deviation_id,
            new_status=new_status,
            actor=current_user.username,
            notes=str(data.get("notes", "")),
            root_cause=data.get("root_cause"),
            corrective_action=data.get("corrective_action"),
            owner=data.get("owner"),
            due_date=data.get("due_date")
        )

        return jsonify(result)

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except LookupError as error:
        return jsonify({
            "error": str(error)
        }), 404

# 16. LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get(
            "password", ""
        )

        user = authenticate(
            username,
            password
        )

        if user:
            login_user(user)

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password",
            "danger"
        )

    return render_template("login.html")


# --------------------------------------------------
# 17. LOGOUT
# --------------------------------------------------

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )

# 18. USER MANAGEMENT PAGE
@app.route("/users")
@login_required
@roles_required("ADMIN")
def users_page():

    return render_template(
        "users.html",
        users=list_users(),
        roles=ROLES
    )

# 19. CREATE USER
@app.route("/users/create", methods=["POST"])
@login_required
@roles_required("ADMIN")
def users_create():

    username = request.form.get(
        "username", ""
    )

    password = request.form.get(
        "password", ""
    )

    role = request.form.get(
        "role", ""
    )

    try:
        create_user(
            username,
            password,
            role
        )

        flash(
            "User created successfully",
            "success"
        )

    except ValueError as error:
        flash(
            str(error),
            "danger"
        )

    return redirect(
        url_for("users_page")
    )
# 20. RUN FLASK APPLICATION
if __name__ == "__main__":
    app.run(debug=True)