Project Overview

1. Introduction
The Cold Chain Management System is a web-based application developed using Python Flask to monitor shipment conditions, verify temperature compliance and manage temperature-related deviations.
The application provides a centralized interface for viewing shipment information, monitoring compliance status, managing deviations and generating reports.

2. Objectives
Monitor temperature conditions associated with shipments.
Identify temperature deviations from configured compliance conditions.
Provide shipment-level compliance information.
Manage deviations through a structured workflow.
Maintain an event history for deviation-related activities.
Generate downloadable PDF reports.

3. Main Features
a.User Authentication and Role-Based Access
Secure login functionality.
Four user roles: ADMIN, QUALITY_MANAGER, QUALITY_ANALYST and VIEWER.
Access to application functionality based on user roles.

b. Shipment Monitoring
View shipment information and details.
Monitor temperature readings.
Display shipment compliance information.

c. Deviation Management
Record and manage temperature deviations.
Track deviation status through the following stages:
  Open
  Under investigation
  Corrective action
  colsed
Maintain an event history of deviation-related activities.

d. Dashboard
Centralized view of shipment and compliance information.
Access to relevant shipment and deviation details.

e. PDF Report Generation
Generate and download shipment-related PDF reports.

4. Technology Stack
Backend - Python, Flask
Frontend - HTML, CSS, JavaScript
Database - SQLite
Authentication - Flask-Login
Form Security - Flask-WTF
PDF Generation - ReportLab

5. Project Structure

app.py – Main Flask application.
auth.py – Authentication and user management.
deviation_manager.py – Deviation management and event history.
report_generator.py – PDF report generation.
create_admin.py – Administrative user creation.
templates/ – HTML pages.
static/ – CSS and JavaScript files.
tests/ – Application test files.
output/ – Location for the shipment database.

6. Expected Outcome
The application provides a structured way to monitor cold chain shipments, review temperature compliance, manage deviations and maintain supporting records through a web-based interface.