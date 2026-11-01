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
function displayValue(value) {
    return value === null || value === undefined || value === ""
        ? "--" : String(value);
}


// -----------------------------------------
// 1. ADD SHIPMENT INFORMATION
// -----------------------------------------

function addInfo(tableId, label, value) {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    const td = document.createElement("td");

    th.textContent = label;
    td.textContent = displayValue(value);

    tr.append(th, td);

    document.getElementById(tableId).appendChild(tr);
}


// -----------------------------------------
// 2. POPULATE DATA TABLES
// -----------------------------------------

function populateTable(tableId, records, fields) {
    const tbody = document.getElementById(tableId);
    tbody.replaceChildren();

    if (!records.length) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");

        td.colSpan = fields.length;
        td.textContent = "No records available";

        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }

    for (const record of records) {
        const tr = document.createElement("tr");

        for (const field of fields) {
            const td = document.createElement("td");
            const dateFields = [
    "assigned_at",
    "unassigned_at",
    "event_at",
    "arrived_at",
    "departed_at"
];

if (dateFields.includes(field)) {
    td.textContent = formatDateTime(record[field]);
} else if (field === "state" || field === "event_type") {
    td.textContent = formatDisplayText(record[field]);
} else {
    td.textContent = displayValue(record[field]);
}
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    }
}


// -----------------------------------------
// 3. LOAD SHIPMENT DETAILS
// -----------------------------------------

async function loadShipmentDetails() {
    try {
        const response = await fetch(
            "/api/shipments/" +
            encodeURIComponent(shipmentId) +
            "/details"
        );

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {
            throw new Error("Unable to load shipment details");
        }

        const data = await response.json();
        const s = data.shipment;


        // ---------------------------------
        // SHIPMENT SUMMARY
        // ---------------------------------

        document.getElementById("shipmentId").textContent =
            s.shipment_id;

        document.getElementById("product").textContent =
            displayValue(s.product_name);

        const decision = document.getElementById("decision");

        decision.textContent = displayValue(s.decision);

        decision.className =
            s.decision === "PASS" ? "text-success" :
            s.decision === "FAIL" ? "text-danger" :
            "text-warning";

        document.getElementById("excursion").textContent =
            displayValue(s.excursion_minutes) + " min";

        document.getElementById("missing").textContent =
            displayValue(s.missing_intervals);


        // ---------------------------------
        // SHIPMENT INFORMATION
        // ---------------------------------

        document.getElementById("shipmentInfo").replaceChildren();

        [
            ["Shipment ID", s.shipment_id],
            ["Lot ID", s.lot_id],
            ["Product", s.product_name],
            ["Packaging ID", s.packaging_id],
            ["Route", s.route],
            ["State", formatDisplayText(s.state)],
            ["Planned Departure", formatDateTime(s.planned_departure)],
            ["Planned Arrival", formatDateTime(s.planned_arrival)]
        ].forEach(item => addInfo("shipmentInfo", ...item));


        // ---------------------------------
        // TEMPERATURE POLICY
        // ---------------------------------

        document.getElementById("policyInfo").replaceChildren();

        [
            ["Policy ID", s.policy_id],
            ["Minimum Temperature",
                displayValue(s.min_c) + " °C"],
            ["Maximum Temperature",
                displayValue(s.max_c) + " °C"],
            ["Allowed Excursion",
                displayValue(s.allowed_excursion_min) + " min"],
            ["Maximum Data Gap",
                displayValue(s.max_gap_min) + " min"],
            ["Maximum Custody Gap",
                displayValue(s.max_custody_gap_min) + " min"],
            ["Effective From", formatDateTime(s.effective_from)],
            ["Effective To", formatDateTime(s.effective_to)]
        ].forEach(item => addInfo("policyInfo", ...item));

        document.getElementById("thresholdInfo").textContent =
            `Allowed temperature range: ${s.min_c}°C to ${s.max_c}°C`;


        // ---------------------------------
        // TEMPERATURE CHART
        // ---------------------------------

        const readings = data.readings || [];

        const labels = readings.map(r =>
    formatDateTime(r.recorded_at)
);

        // Get valid measured temperature values
        const temperatures = readings.map(r =>
            r.quality === "MEASURED" &&
            r.temperature_c !== null &&
            r.temperature_c !== undefined &&
            r.temperature_c !== "" &&
            Number.isFinite(Number(r.temperature_c))
                ? Number(r.temperature_c)
                : null
        );

        // Minimum and maximum temperature thresholds
        const lower = readings.map(() => Number(s.min_c));
        const upper = readings.map(() => Number(s.max_c));

        // Get chart element
        const chartElement =
            document.getElementById("temperatureChart");

        // Destroy existing chart if present
        const existingChart = Chart.getChart(chartElement);

        if (existingChart) {
            existingChart.destroy();
        }

        // Create temperature monitoring chart
        new Chart(chartElement, {
            type: "line",

            data: {
                labels: labels,

                datasets: [
                    {
                        label: "Temperature (°C)",
                        data: temperatures,
                        borderColor: "#0d6efd",
                        backgroundColor: "rgba(13, 110, 253, 0.1)",
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.2,
                        spanGaps: false
                    },
                    {
                        label: "Minimum Threshold",
                        data: lower,
                        borderColor: "#198754",
                        borderWidth: 2,
                        pointRadius: 0,
                        borderDash: [6, 4]
                    },
                    {
                        label: "Maximum Threshold",
                        data: upper,
                        borderColor: "#dc3545",
                        borderWidth: 2,
                        pointRadius: 0,
                        borderDash: [6, 4]
                    }
                ]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                interaction: {
                    mode: "index",
                    intersect: false
                },

                plugins: {
                    tooltip: {
                        enabled: true
                    },
                    legend: {
                        display: true,
                        position: "top"
                    }
                },

                scales: {
                    x: {
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },

                    y: {
                        title: {
                            display: true,
                            text: "Temperature (°C)"
                        }
                    }
                }
            }
        });


        // ---------------------------------
        // LOGGER ASSIGNMENTS
        // ---------------------------------

        populateTable(
            "loggerTable",
            data.assignments || [],
            ["logger_id", "assigned_at", "unassigned_at", "state"]
        );


        // ---------------------------------
        // CUSTODY EVENTS
        // ---------------------------------

        populateTable(
            "custodyTable",
            data.custody || [],
            ["event_at", "actor", "event_type", "location"]
        );


        // ---------------------------------
        // ROUTE STOPS
        // ---------------------------------

        populateTable(
            "routeTable",
            data.stops || [],
            [
                "sequence_no",
                "location",
                "arrived_at",
                "departed_at",
                "dwell_min"
            ]
        );


        // ---------------------------------
        // ISSUES AND EVIDENCE
        // ---------------------------------

         const issuesElement = document.getElementById("issues");
        const evidenceElement = document.getElementById("evidence");

        // Display issue types
        let issueTypes = s.issue_types;

        if (typeof issueTypes === "string") {
            try {
                issueTypes = JSON.parse(issueTypes);
            } catch (error) {
                // Keep original value
            }
        }

       
        if (Array.isArray(issueTypes)) {
            issuesElement.textContent = issueTypes.length
                ? issueTypes.map(formatDisplayText).join(", ")
                : "No issues detected";
        } else {
            issuesElement.textContent =
                issueTypes && issueTypes !== "[]"
                    ? String(issueTypes)
                        .split(",")
                        .map(formatDisplayText)
                        .join(", ")
                    : "No issues detected";
        }

        // Clear previous evidence
        evidenceElement.replaceChildren();

        let evidence = s.evidence_json;

        try {
            if (typeof evidence === "string") {
                evidence = JSON.parse(evidence);
            }
        } catch (error) {
            evidenceElement.textContent =
                "Evidence data is not in valid JSON format.";
            evidence = null;
        }

        if (evidence && typeof evidence === "object" &&
            !Array.isArray(evidence)) {

            const readingIds = Array.isArray(evidence.reading_ids)
                ? evidence.reading_ids : [];

            const custodyIds = Array.isArray(evidence.custody_event_ids)
                ? evidence.custody_event_ids : [];

            const excursions = Array.isArray(evidence.excursions)
                ? evidence.excursions : [];

            // Summary table
            const summaryTable = document.createElement("table");
            summaryTable.className =
                "table table-bordered table-striped table-sm";

            const summaryBody = document.createElement("tbody");
            summaryTable.appendChild(summaryBody);

            function addEvidenceRow(label, value) {
                const row = document.createElement("tr");
                const heading = document.createElement("th");
                const cell = document.createElement("td");

                heading.textContent = label;
                cell.textContent = displayValue(value);

                row.append(heading, cell);
                summaryBody.appendChild(row);
            }

            addEvidenceRow("Policy ID", evidence.policy_id);
            addEvidenceRow(
                "Expected Temperature Readings",
                evidence.expected_readings
            );
            addEvidenceRow(
                "Evidence Reading IDs",
                readingIds.length
            );
            addEvidenceRow(
                "Temperature Excursions",
                excursions.length
            );
            addEvidenceRow(
                "Custody Events",
                custodyIds.length
            );
            addEvidenceRow(
                "Logger Assignment",
                evidence.assignment_id
            );

            evidenceElement.appendChild(summaryTable);

            // Expandable details helper
            function addExpandableSection(title, records) {
                if (!records.length) {
                    return;
                }

                const details = document.createElement("details");
                details.className = "mt-3";

                const summary = document.createElement("summary");
                summary.className = "fw-semibold";
                summary.textContent =
                    `${title} (${records.length})`;

                const list = document.createElement("ol");
                list.className = "mt-2";

                for (const record of records) {
                    const item = document.createElement("li");

                    item.textContent =
                        typeof record === "object" && record !== null
                            ? JSON.stringify(record)
                            : String(record);

                    item.style.overflowWrap = "anywhere";
                    list.appendChild(item);
                }

                details.append(summary, list);
                evidenceElement.appendChild(details);
            }

            addExpandableSection(
                "Temperature Reading IDs",
                readingIds
            );

            addExpandableSection(
                "Custody Event IDs",
                custodyIds
            );

            addExpandableSection(
                "Temperature Excursion Details",
                excursions
            );

        } else if (!evidence) {
            evidenceElement.textContent =
                "No compliance evidence available.";
        } else {
            evidenceElement.textContent =
                displayValue(evidence);
        }


        // ---------------------------------
        // STEP 6: PDF DOWNLOAD BUTTON
        // ---------------------------------

        const downloadButton =
            document.getElementById("downloadReport");

        if (downloadButton) {
            downloadButton.href =
                "/api/shipments/" +
                encodeURIComponent(s.shipment_id) +
                "/report";

            downloadButton.style.display = "inline-block";
        }

    } catch (error) {
        const message = document.getElementById("errorMessage");

        message.textContent = error.message;
        message.classList.remove("d-none");

        console.error(error);
    }
}


// -----------------------------------------
// 4. INITIAL PAGE LOAD
// -----------------------------------------

loadShipmentDetails();
