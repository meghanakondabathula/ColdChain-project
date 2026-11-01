# Cold Chain Management System

## 1. Project Overview

The Cold Chain Management System is a web-based application developed using Python Flask. It helps monitor shipment information, review temperature compliance, manage temperature-related deviations and generate PDF reports.

The application provides role-based access and maintains separate databases for shipment information, user authentication and deviation records.

## 2. Key Features

- User authentication and role-based access.
- Shipment monitoring and compliance information.
- Temperature deviation management.
- Deviation status tracking and event history.
- Dashboard for viewing shipment information.
- User management for administrators.
- Downloadable PDF reports.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| Authentication | Flask-Login |
| Form Security | Flask-WTF |
| PDF Generation | ReportLab |

## 4. Project Structure

```text
ColdChain-project/
│
├── app.py
├── auth.py
├── deviation_manager.py
├── report_generator.py
├── create_admin.py
│
├── output/
│   └── coldchain.sqlite
│
├── templates/
├── static/
├── tests/
│
├── docs/
│   ├── PROMPT_HISTORY.md
│   ├── PROJECT_OVERVIEW.md
│   ├── SYSTEM_ARCHITECTURE.md
│   └── SYSTEM_WORKFLOW.md
│
├── requirements.txt
├── DATA_DICTIONARY.md
└── README.md
```

## 5. Environment Requirements

- Python 3.10 or later.
- pip package manager.
- SQLite database.
- A web browser.
- Git (for cloning the repository).

## 6. Installation and Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/meghanakondabathula/ColdChain-project.git
cd ColdChain-project
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Flask secret key

Set the required environment variable in Windows PowerShell:

```powershell
$env:FLASK_SECRET_KEY="replace-with-a-secure-random-secret"
```

Use a private secret value. Do not commit it to GitHub.

### Step 5: Check the shipment database

Ensure that the following database file is available:

```text
output/coldchain.sqlite
```

The application requires this database to access shipment information.

## 7. Running the Application

Start the Flask application:

```bash
python app.py
```

Open the following address in your browser:

```text
http://127.0.0.1:5000/
```

## 8. Testing and Verification

The project includes automated tests in the `tests/` directory.

Run the test suite using:

```bash
pytest
```

Core functionality to verify:

- User login and authentication.
- Role-based access restrictions.
- Dashboard and shipment information.
- Deviation creation and status management.
- Deviation event history.
- PDF report generation.
- Administrative user management.

## 9. Database Information

The application uses SQLite databases:

| Database | Purpose |
|---|---|
| `output/coldchain.sqlite` | Shipment and temperature-related information |
| `auth.sqlite` | User authentication information |
| `deviations.sqlite` | Deviation records and event history |

Database files are excluded from Git version control. The required shipment database must be provided separately when setting up the application.

## 10. Limitations

- The application requires the shipment database to be available locally.
- SQLite database files are not included in the public Git repository.
- The Flask development server is intended for local development, not production hosting.
- The application depends on its configured environment variables and Python packages.
- Temperature policies and compliance conditions should be interpreted according to the project's configured rules.

## 11. Project Documentation

Additional documentation is available in the `docs/` directory:

- `PROJECT_OVERVIEW.md` – Project objectives and features.
- `SYSTEM_ARCHITECTURE.md` – Application components and their connections.
- `SYSTEM_WORKFLOW.md` – Application workflow.
- `PROMPT_HISTORY.md` – Selected development prompts and instructions.

## Testing

The project includes automated tests using pytest.

Run the test suite with:

```bash
python -m pytest


## Database Setup

The main shipment database is not included in this repository because of its large file size.

Download it from Google Drive:

[Download coldchain.sqlite](https://drive.google.com/file/d/1k51FrxrN2dinFuOBNLDcXECCTC901opP/view?usp=drive_link)

After downloading, place the file inside the "output" folder:

cold_chain_complete_project/
└── output/
    └── coldchain.sqlite

Make sure the database filename is exactly "coldchain.sqlite".
Data base setup is mandatory

#Additional Information
The project also contains two more database files such as 
1. "auth.sqlite" which stores user accounts and authentication data.
2. "deviations.sqlite" which tores deviation-management data. 
which are sensitive and cannot be shared