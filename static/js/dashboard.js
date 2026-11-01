function formatDisplayText(value) {
    if (value === null || value === undefined || value === "") {
        return "--";
    }

    return String(value)
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, char => char.toUpperCase());
}
function formatIssueTypes(value) {
    if (!value || value === "[]") {
        return "None";
    }

    let issues = value;

    if (typeof issues === "string") {
        try {
            issues = JSON.parse(issues);
        } catch (error) {
            // Handle comma-separated issue types
        }
    }

    if (Array.isArray(issues)) {
        return issues.length
            ? issues.map(formatDisplayText).join(", ")
            : "None";
    }

    return String(issues)
        .split(",")
        .map(formatDisplayText)
        .join(", ");
}
let currentPage = 1;
let totalPages = 1;

async function fetchJSON(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error("Request failed: " + response.status);
    }

    return await response.json();
}

async function loadDashboard() {
    try {
        const data = await fetchJSON("/api/dashboard");

        document.getElementById("shipments").textContent =
            data.shipments.toLocaleString();

        document.getElementById("readings").textContent =
            data.readings.toLocaleString();

        document.getElementById("loggers").textContent =
            data.loggers.toLocaleString();

        document.getElementById("passRate").textContent =
            data.pass_rate + "%";

        document.getElementById("passed").textContent =
            data.decisions.PASS;

        document.getElementById("review").textContent =
            data.decisions.REVIEW;

        document.getElementById("failed").textContent =
            data.decisions.FAIL;

        new Chart(
            document.getElementById("complianceChart"),
            {
                type: "doughnut",
                data: {
                    labels: ["PASS", "REVIEW", "FAIL"],
                    datasets: [{
                        data: [
                            data.decisions.PASS,
                            data.decisions.REVIEW,
                            data.decisions.FAIL
                        ],
                        backgroundColor: [
                            "#198754",
                            "#ffc107",
                            "#dc3545"
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            }
        );

    } catch (error) {
        console.error(error);
        alert("Unable to load dashboard: " + error.message);
    }
}

async function loadShipments(page = 1) {
    try {
        const search =
            document.getElementById("search").value;

        const status =
            document.getElementById("status").value;

        const params = new URLSearchParams({
            search: search,
            status: status,
            page: page
        });

        const data = await fetchJSON(
            "/api/shipments?" + params.toString()
        );

        currentPage = data.page;
        totalPages = data.pages;

        const tbody =
            document.getElementById("shipmentTable");

        tbody.replaceChildren();

        for (const shipment of data.shipments) {
            const tr = document.createElement("tr");

            const values = [
    shipment.shipment_id,
    shipment.product,
    shipment.route,
    formatDisplayText(shipment.decision),
    shipment.excursion_minutes,
    formatIssueTypes(shipment.issue_types)
];

            
values.forEach((value, index) => {
    const td = document.createElement("td");

    if (index === 0) {
        const link = document.createElement("a");

        link.href = "/shipment/" +
            encodeURIComponent(shipment.shipment_id);

        link.textContent = shipment.shipment_id;
        link.className = "fw-semibold text-decoration-none";

        td.appendChild(link);
    } else {
        td.textContent = value ?? "--";
    }

    tr.appendChild(td);
});


            tbody.appendChild(tr);
        }

        if (data.shipments.length === 0) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 6;
            td.textContent = "No shipments found";
            tr.appendChild(td);
            tbody.appendChild(tr);
        }

        document.getElementById("pageInfo").textContent =
            `Page ${currentPage} of ${totalPages} (${data.total} shipments)`;

        document.getElementById("previous").disabled =
            currentPage <= 1;

        document.getElementById("next").disabled =
            currentPage >= totalPages;

    } catch (error) {
        console.error(error);
        alert("Unable to load shipments: " + error.message);
    }
}

document.getElementById("search").addEventListener(
    "input", () => loadShipments(1)
);

document.getElementById("status").addEventListener(
    "change", () => loadShipments(1)
);

document.getElementById("previous").addEventListener(
    "click", () => loadShipments(currentPage - 1)
);

document.getElementById("next").addEventListener(
    "click", () => loadShipments(currentPage + 1)
);

loadDashboard();
loadShipments();
