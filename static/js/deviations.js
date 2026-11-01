function formatDateTime(value) {
    if (!value) return "--";

    const date = new Date(value);

    if (isNaN(date.getTime())) return value;

    return new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
        timeZoneName: "short"
    }).format(date);
}
function formatDisplayText(value) {
    if (value === null || value === undefined || value === "") {
        return "--";
    }

    return String(value)
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, char => char.toUpperCase());
}
let selectedDeviation = null;

// Current role is provided by deviations.html
const userRole = currentRole;

const allowedTransitions = {
    OPEN: ["UNDER_INVESTIGATION"],
    UNDER_INVESTIGATION: ["CORRECTIVE_ACTION"],
    CORRECTIVE_ACTION: ["CLOSED", "UNDER_INVESTIGATION"],
    CLOSED: []
};


// -----------------------------------------
// 1. DISPLAY MESSAGES
// -----------------------------------------

function showMessage(message, type = "success") {
    const box = document.getElementById("message");

    box.className = `alert alert-${type}`;
    box.textContent = message;
}


// -----------------------------------------
// 2. API REQUESTS
// -----------------------------------------

async function api(url, options = {}) {
    const response = await fetch(url, options);

    const contentType = response.headers.get("content-type") || "";

    if (!contentType.includes("application/json")) {
        if (response.status === 401 || response.redirected) {
            window.location.href = "/login";
            throw new Error("Login required");
        }

        throw new Error(`Request failed: ${response.status}`);
    }

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || `Request failed: ${response.status}`);
    }

    return data;
}


async function postJSON(url, data) {
    const token = document.querySelector(
        'meta[name="csrf-token"]'
    ).content;

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": token
        },
        credentials: "same-origin",
        body: JSON.stringify(data)
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || "Request failed");
    }

    return result;
}


// -----------------------------------------
// 3. TABLE HELPER
// -----------------------------------------

function cell(row, value) {
    const td = document.createElement("td");

    td.textContent = value ?? "--";
    row.appendChild(td);
}


// -----------------------------------------
// 4. LOAD DEVIATIONS
// -----------------------------------------

async function loadDeviations() {
    const records = await api("/api/deviations");

    const tbody = document.getElementById("deviationTable");
    tbody.replaceChildren();

    if (!records.length) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");

        td.colSpan = 6;
        td.textContent = "No investigations created yet";

        tr.appendChild(td);
        tbody.appendChild(tr);

        return;
    }

    for (const item of records) {
        const tr = document.createElement("tr");

        cell(tr, item.deviation_id);
        cell(tr, item.shipment_id);
        cell(tr, formatDisplayText(item.original_decision));
        cell(tr, formatDisplayText(item.status));
        cell(tr, formatDateTime(item.updated_at));

        const td = document.createElement("td");
        const button = document.createElement("button");

        button.type = "button";
        button.className = "btn btn-sm btn-outline-primary";
        button.textContent = "View";

        button.addEventListener("click", () => {
            openDeviation(item.deviation_id);
        });

        td.appendChild(button);
        tr.appendChild(td);

        tbody.appendChild(tr);
    }
}


// -----------------------------------------
// 5. ROLE-BASED TRANSITIONS
// -----------------------------------------

function getAllowedStatuses(status) {
    if (userRole === "VIEWER") {
        return [];
    }

    const transitions = allowedTransitions[status] || [];

    if (userRole === "QUALITY_ANALYST") {
        return transitions.filter(next => next !== "CLOSED");
    }

    return transitions;
}


// -----------------------------------------
// 6. OPEN DEVIATION DETAILS
// -----------------------------------------

async function openDeviation(id) {
    try {
        const data = await api(`/api/deviations/${id}`);

        selectedDeviation = id;
        const downloadButton =
    document.getElementById("downloadDeviationReport");

if (downloadButton) {
    downloadButton.href =
        `/api/deviations/${encodeURIComponent(id)}/report`;

    downloadButton.style.display = "inline-block";
}
const auditButton =
    document.getElementById("downloadAuditReport");

if (auditButton) {
    auditButton.href =
        `/api/deviations/${encodeURIComponent(id)}/audit-report`;

    auditButton.style.display = "inline-block";
}
        const d = data.deviation;

        document.getElementById("investigationPanel")
            .classList.remove("d-none");

        document.getElementById("selectedTitle").textContent =
            `Deviation #${id} — ${d.shipment_id}`;

        document.getElementById("currentStatus").textContent =
    `Original decision: ${formatDisplayText(d.original_decision)} | Status: ${formatDisplayText(d.status)}`;

        const statuses = getAllowedStatuses(d.status);

        // Viewer accounts do not have an update form
        const select = document.getElementById("newStatus");

        if (select) {
            select.replaceChildren();

            for (const status of statuses) {
                const option = document.createElement("option");

                option.value = status;
                option.textContent = formatDisplayText(status);

                select.appendChild(option);
            }
        }

        const updateButton = document.querySelector(
            "#updateForm button[type='submit']"
        );

        if (updateButton) {
            updateButton.disabled = statuses.length === 0;
        }

        // Display audit history
        const history = document.getElementById("auditHistory");
        history.replaceChildren();

        for (const event of data.events) {
            const box = document.createElement("div");
            box.className = "border-bottom py-3";

            const title = document.createElement("strong");

            title.textContent =
            `${formatDisplayText(event.action)}: ${formatDisplayText(event.old_status || "NEW")} → ${formatDisplayText(event.new_status)}`;

            const info = document.createElement("p");
            info.className = "mb-1 text-muted";

            info.textContent =
                `${event.actor} | ${formatDateTime(event.created_at)}`;

            const notes = document.createElement("p");
            notes.className = "mb-1";

            notes.textContent = event.notes || "--";

            const extra = document.createElement("p");
            extra.className = "small mb-0";

            extra.textContent = [
                event.root_cause &&
                    `Cause: ${event.root_cause}`,

                event.corrective_action &&
                    `Action: ${event.corrective_action}`,

                event.owner &&
                    `Owner: ${event.owner}`,

                event.due_date &&
                    `Due: ${event.due_date}`
            ].filter(Boolean).join(" | ");

            box.append(title, info, notes, extra);
            history.appendChild(box);
        }

    } catch (error) {
        showMessage(error.message, "danger");
    }
}


// -----------------------------------------
// 7. CREATE INVESTIGATION
// -----------------------------------------

const createForm = document.getElementById("createForm");

if (createForm) {
    createForm.addEventListener("submit", async event => {
        event.preventDefault();

        const shipmentId = document.getElementById("shipmentId")
            .value.trim();

        if (!shipmentId) {
            showMessage("Please enter a shipment ID", "warning");
            return;
        }

        try {
            const result = await postJSON("/api/deviations", {
                shipment_id: shipmentId
            });

            showMessage("Investigation opened successfully");

            createForm.reset();

            await loadDeviations();
            await openDeviation(result.deviation_id);

        } catch (error) {
            showMessage(error.message, "danger");
        }
    });
}


// -----------------------------------------
// 8. UPDATE INVESTIGATION
// -----------------------------------------

const updateForm = document.getElementById("updateForm");

if (updateForm) {
    updateForm.addEventListener("submit", async event => {
        event.preventDefault();

        if (selectedDeviation === null) {
            showMessage("Select a deviation first", "warning");
            return;
        }

        const status = document.getElementById("newStatus").value;

        const data = {
            status: status,

            notes: document.getElementById("notes")
                .value.trim(),

            root_cause: document.getElementById("rootCause")
                .value.trim(),

            corrective_action: document.getElementById("correctiveAction")
                .value.trim(),

            owner: document.getElementById("owner")
                .value.trim(),

            due_date: document.getElementById("dueDate")
                .value || null
        };

        if (!data.notes) {
            showMessage("Investigation notes are required", "warning");
            return;
        }

        if (status === "CORRECTIVE_ACTION") {
            if (!data.corrective_action ||
                !data.owner ||
                !data.due_date) {

                showMessage(
                    "Corrective action, owner and due date are required",
                    "warning"
                );

                return;
            }
        }

        if (status === "CLOSED" && !data.root_cause) {
            showMessage(
                "Root cause is required for closure",
                "warning"
            );

            return;
        }

        try {
            await postJSON(
                `/api/deviations/${selectedDeviation}/status`,
                data
            );

            showMessage("Investigation updated successfully");

            updateForm.reset();

            await loadDeviations();
            await openDeviation(selectedDeviation);

        } catch (error) {
            showMessage(error.message, "danger");
        }
    });
}


// -----------------------------------------
// 9. INITIAL PAGE LOAD
// -----------------------------------------

loadDeviations().catch(error => {
    showMessage(error.message, "danger");
});
