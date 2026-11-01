from zoneinfo import ZoneInfo
from io import BytesIO
from datetime import datetime
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from xml.sax.saxutils import escape
def format_display(value):
    if value is None or value == "":
        return "--"

    return str(value).replace("_", " ").title()
def format_datetime(value):
    if value is None or str(value).strip() in ("", "--", "-"):
        return "--"

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        return str(value)

    if dt.tzinfo is not None:
        dt = dt.astimezone(ZoneInfo("Asia/Kolkata"))
        return dt.strftime("%d %b %Y, %I:%M %p IST")

    return dt.strftime("%d %b %Y, %I:%M %p")
def format_issue_types(value):
    if not value or value == "[]":
        return "None"

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            value = value.split(",")

    if isinstance(value, list):
        return (
            ", ".join(format_display(item) for item in value)
            if value else "None"
        )

    return format_display(value)

def generate_shipment_pdf(shipment_id, details):
    """
    Generate a PDF from shipment details retrieved
    by the Flask application.

    details must be a dictionary.
    Returns a BytesIO PDF file.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#174A7E"),
        fontSize=17,
        spaceAfter=14
    )

    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    elements = []

    elements.append(
        Paragraph(
            "COLD CHAIN COMPLIANCE SYSTEM",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "Shipment Compliance Report",
            heading_style
        )
    )

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            f"<b>Shipment ID:</b> {escape(str(shipment_id))}",
            normal_style
        )
    )

    elements.append(
    Paragraph(
        f"<b>Generated:</b> "
        f"{datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y, %I:%M %p IST')}",
        normal_style
    )
)

    elements.append(Spacer(1, 20))

    def add_section(title, records):
        elements.append(
            Paragraph(escape(str(title)), heading_style)
        )

        if not records:
            elements.append(
                Paragraph("No records available.", normal_style)
            )
            elements.append(Spacer(1, 12))
            return

        if isinstance(records, dict):

            label_style = ParagraphStyle(
                "LabelStyle",
                parent=normal_style,
                fontName="Helvetica-Bold",
                fontSize=9
            )

            value_style = ParagraphStyle(
                "ValueStyle",
                parent=normal_style,
                fontSize=9
            )

            rows = [
                [
                    Paragraph("<b>Field</b>", normal_style),
                    Paragraph("<b>Value</b>", normal_style)
                ]
            ]
            for key, value in records.items():
                if value is None or value == "":
                    value = "--"

                key_lower = str(key).lower()

                if key_lower == "issue_types":
                    display_value = format_issue_types(value)

                elif key_lower in ("decision", "state", "status"):
                    display_value = format_display(value)

                elif key_lower in ("min_c", "max_c"):
                    display_value = f"{value} °C"

                elif key_lower in (
                    "planned_departure",
                    "planned_arrival",
                    "generated_at",
                    "effective_from",
                    "effective_to"
                ):
                    display_value = format_datetime(value)

                else:
                    display_value = str(value)

                display_label = {
                    "min_c": "Minimum Allowed Temperature",
                    "max_c": "Maximum Allowed Temperature"
                }.get(
                    key_lower,
                    str(key).replace("_", " ").title()
                )

                rows.append([
                    Paragraph(
                        escape(display_label),
                        label_style
                    ),
                    Paragraph(
                        escape(str(display_value)),
                        value_style
                    )
                ])

            table = Table(
                rows,
                colWidths=[220, 285],
                repeatRows=1,
                hAlign="LEFT"
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0),
                colors.HexColor("#174A7E")),

                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                [colors.white, colors.whitesmoke]),

                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),

                ("VALIGN", (0, 0), (-1, -1), "TOP"),

                ("TOPPADDING", (0, 0), (-1, -1), 8),

                ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
            ]))

            elements.append(table)

        else:
            elements.append(
            Paragraph(
                escape(str(records)),
                normal_style
            )
        )

    elements.append(Spacer(1, 18))
    # SHIPMENT DETAILS
    for key, value in details.items():

        if key in ("readings", "temperature_readings"):
            if isinstance(value, list):
                add_section(
                    "Temperature Readings Summary",
                    {
                        "Readings returned by API": len(value)
                    }
                )
            continue

        if isinstance(value, dict):

            if key == "shipment":
                value = {
                    k: v
                    for k, v in value.items()
                    if k != "evidence_json"
                }

            add_section(
                key.replace("_", " ").title(),
                value
            )

        elif isinstance(value, list):
            add_section(
                key.replace("_", " ").title(),
                {
                    "Number of records": len(value)
                }
            )

        else:
            add_section(
                key.replace("_", " ").title(),
                {
                    "Value": value
                }
            )
    # COMPLIANCE EVIDENCE SUMMARY
    shipment = details.get("shipment", {})

    raw_evidence = (
        shipment.get("evidence_json")
        if isinstance(shipment, dict)
        else None
    )

    try:
        evidence = (
            json.loads(raw_evidence)
            if isinstance(raw_evidence, str)
            else raw_evidence
        )
    except (json.JSONDecodeError, TypeError):
        evidence = None

    if isinstance(evidence, dict):

        reading_ids = evidence.get("reading_ids")
        custody_ids = evidence.get("custody_event_ids")
        excursions = evidence.get("excursions")

        add_section(
            "Compliance Evidence Summary",
            {
                "Policy ID":
                    evidence.get("policy_id", "--"),

                "Expected Readings":
                    evidence.get("expected_readings", "--"),

                "Evidence Reading IDs":
                    len(reading_ids)
                    if isinstance(reading_ids, list)
                    else "--",

                "Temperature Excursions":
                    len(excursions)
                    if isinstance(excursions, list)
                    else "--",

                "Custody Events":
                    len(custody_ids)
                    if isinstance(custody_ids, list)
                    else "--",

                "Logger Assignment":
                    evidence.get("assignment_id", "--")
            }
        )

    elif raw_evidence:
        elements.append(
            Paragraph(
                "Compliance evidence summary unavailable.",
                normal_style
            )
        )

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            "Report generated from the Cold Chain Compliance System.",
            normal_style
        )
    )

    document.build(elements)
    buffer.seek(0)

    return buffer


def generate_deviation_pdf(deviation_data):
    """
    Generate a PDF containing deviation details
    and its audit history.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    deviation = deviation_data["deviation"]
    events = deviation_data.get("events", [])

    def safe(value):
        return escape(
            str(value if value is not None else "--")
        )

    elements.append(
        Paragraph(
            "Cold Chain Compliance System",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "Deviation Investigation Report",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 15))

    fields = [
        ("Deviation ID", deviation.get("deviation_id")),
        ("Shipment ID", deviation.get("shipment_id")),
        ("Original Decision", deviation.get("original_decision")),
        ("Current Status", deviation.get("status")),
        ("Root Cause", deviation.get("root_cause")),
        ("Corrective Action", deviation.get("corrective_action")),
        ("Action Owner", deviation.get("owner")),
        ("Due Date", deviation.get("due_date")),
        ("Created At", format_datetime(deviation.get("created_at"))),
        ("Updated At", format_datetime(deviation.get("updated_at"))),
    ]

    rows = [
        [
            Paragraph("<b>Field</b>", styles["BodyText"]),
            Paragraph("<b>Value</b>", styles["BodyText"])
        ]
    ]

    for label, value in fields:
        if label in ("Original Decision", "Current Status"):
            value = format_display(value)

        rows.append([
        Paragraph(safe(label), styles["BodyText"]),
        Paragraph(safe(value), styles["BodyText"])
    ])

    table = Table(
        rows,
        colWidths=[160, 345],
        repeatRows=1
    )

    table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.lightblue
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.grey
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP"
        ),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [colors.white, colors.whitesmoke]
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            8
        )
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Audit History",
            styles["Heading2"]
        )
    )

    if not events:
        elements.append(
            Paragraph(
                "No audit events available.",
                styles["BodyText"]
            )
        )

    for event in events:

        elements.append(
            Paragraph(
                f"<b>{safe(format_display(event.get('action')))}</b> — "
                f"{safe(format_datetime(event.get('created_at')))}",
                styles["BodyText"]
            )
        )

        elements.append(
            Paragraph(
                f"Actor: {safe(event.get('actor'))}",
                styles["BodyText"]
            )
        )

        elements.append(
            Paragraph(
                f"Status: {safe(format_display(event.get('old_status')))} "
                f"to {safe(format_display(event.get('new_status')))}",
                styles["BodyText"]
            )
        )

        for label, key in [
            ("Notes", "notes"),
            ("Root Cause", "root_cause"),
            ("Corrective Action", "corrective_action"),
            ("Owner", "owner"),
            ("Due Date", "due_date")
        ]:
            if event.get(key):
                elements.append(
                    Paragraph(
                        f"<b>{label}:</b> {safe(event[key])}",
                        styles["BodyText"]
                    )
                )

        elements.append(Spacer(1, 12))

    document.build(elements)
    buffer.seek(0)

    return buffer


def generate_audit_history_pdf(deviation_data):
    """
    Generate a standalone PDF containing the complete
    audit event history for one deviation.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    elements = []

    deviation = deviation_data["deviation"]
    events = deviation_data.get("events", [])

    def safe(value):
        if value is None or value == "":
            return "--"

        return escape(str(value))

    elements.append(
        Paragraph(
            "COLD CHAIN COMPLIANCE SYSTEM",
            styles["Title"]
        )
    )

    elements.append(
        Paragraph(
            "Deviation Audit History Report",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 15))

    summary = [
        ("Deviation ID", deviation.get("deviation_id")),
        ("Shipment ID", deviation.get("shipment_id")),
        ("Original Decision", deviation.get("original_decision")),
        ("Current Status", deviation.get("status")),
        ("Created At", format_datetime(deviation.get("created_at"))),
        ("Last Updated", format_datetime(deviation.get("updated_at"))),
        ("Total Audit Events", len(events))
    ]

    rows = [
        [
            Paragraph("<b>Field</b>", styles["BodyText"]),
            Paragraph("<b>Value</b>", styles["BodyText"])
        ]
    ]

    for label, value in summary:
        if label in ("Original Decision", "Current Status"):
            value = format_display(value)

        rows.append([
            Paragraph(safe(label), styles["BodyText"]),
            Paragraph(safe(value), styles["BodyText"])
        ])

    summary_table = Table(
        rows,
        colWidths=[160, 345],
        repeatRows=1
    )

    summary_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.lightblue
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.grey
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP"
        ),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [colors.white, colors.whitesmoke]
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            8
        )
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Chronological Audit Events",
            styles["Heading2"]
        )
    )

    if not events:
        elements.append(
            Paragraph(
                "No audit events available.",
                styles["BodyText"]
            )
        )

    for event in events:

        elements.append(Spacer(1, 10))

        elements.append(
            Paragraph(
                f"Event #{safe(event.get('event_id'))} — "
               f"{safe(format_display(event.get('action')))}",
                styles["Heading3"]
            )
        )

        event_fields = [
           ("Timestamp", format_datetime(event.get("created_at"))),
            ("Performed By", event.get("actor")),
            ("Previous Status", event.get("old_status")),
            ("New Status", event.get("new_status")),
            ("Notes", event.get("notes")),
            ("Root Cause", event.get("root_cause")),
            ("Corrective Action", event.get("corrective_action")),
            ("Action Owner", event.get("owner")),
            ("Due Date", event.get("due_date"))
        ]

        event_rows = []

        for label, value in event_fields:
            if label in ("Previous Status", "New Status"):
                value = format_display(value)

            event_rows.append([
                Paragraph(
                    f"<b>{safe(label)}</b>",
                    styles["BodyText"]
                ),
                Paragraph(
                    safe(value),
                    styles["BodyText"]
                    )
                    ])

        event_table = Table(
            event_rows,
            colWidths=[160, 345],
            hAlign="LEFT"
        )

        event_table.setStyle(TableStyle([
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "ROWBACKGROUNDS",
                (0, 0),
                (-1, -1),
                [colors.white, colors.whitesmoke]
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ]))

        elements.append(event_table)

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Generated from the append-only DeviationEvent "
            "audit history.",
            styles["BodyText"]
        )
    )

    document.build(elements)
    buffer.seek(0)

    return buffer