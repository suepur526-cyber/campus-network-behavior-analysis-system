# Campus Network User Behavior Analysis System

A Flask-based campus network user behavior analysis system. The system provides a complete workflow for log ingestion, data cleaning, behavior statistics, anomaly detection, visualization, log query, CSV export, directory collection, and test reporting.

This project is designed as a graduation/student project, so the business logic is complete but kept clear and maintainable. It can run locally with SQLite by default, and it can also be switched to MySQL through `DATABASE_URL`.

## Features

- User login, logout, and protected pages.
- Default administrator account creation.
- CSV, JSON, TXT, and syslog-like log parsing.
- Log cleaning, deduplication, timestamp normalization, numeric field correction, and unified field storage.
- Manual file upload and import.
- Validation data generation and import.
- Directory-based log collection from `data/ingest`.
- File hash and file name deduplication for directory collection.
- Dashboard metrics:
  - total logs
  - total users
  - traffic volume
  - anomaly count
- User behavior analysis:
  - traffic trend
  - access heatmap
  - protocol distribution
  - access category distribution
  - user type distribution
  - application distribution
  - user behavior profiles
  - top traffic users
- Anomaly detection:
  - rule-based detection for high-frequency connections, abnormal high traffic, port scanning, and suspicious access
  - machine learning detection with KMeans and Isolation Forest
- Alert list with pagination.
- Log query with keyword, user type, protocol, and anomaly status filters.
- CSV export for current query result.
- System status and test report page.
- Automated tests for core backend and API workflows.
- Browser QA verified for key pages, buttons, forms, pagination, export, layout, and console/network health.

## Technology Stack

- Python 3.11
- Flask 3
- Flask-SQLAlchemy
- SQLite by default
- MySQL support through `DATABASE_URL`
- Pandas
- NumPy
- scikit-learn
- Matplotlib
- ECharts
- HTML / CSS / JavaScript
- pytest

## Project Structure

```text
.
+-- app/
|   +-- __init__.py
|   +-- config.py
|   +-- models.py
|   +-- routes.py
|   +-- services/
|   |   +-- analytics.py
|   |   +-- anomaly.py
|   |   +-- auth.py
|   |   +-- cleaning.py
|   |   +-- collector.py
|   |   +-- importer.py
|   |   +-- log_parser.py
|   |   +-- sample_data.py
|   |   +-- status.py
|   +-- static/
|   |   +-- css/styles.css
|   |   +-- js/
|   +-- templates/
+-- data/
|   +-- ingest/
+-- docs/
+-- tests/
+-- conftest.py
+-- requirements.txt
+-- run.py
```

## Quick Start

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Initialize the database:

```powershell
$env:FLASK_APP = "run.py"
flask init-db
```

Optional: add sample data and run anomaly detection:

```powershell
flask seed-data
flask detect-anomalies
```

Start the system:

```powershell
python run.py
```

Open:

```text
http://127.0.0.1:5000/login
```

Default administrator:

```text
Username: admin
Password: admin123
```

## Main Pages

- Dashboard: `/`
- Log ingestion: `/import`
- Log query: `/logs`
- Behavior analysis: `/analysis`
- Anomaly detection: `/anomalies`
- Test report and system status: `/report`

## Database Configuration

The system uses SQLite by default:

```text
campus_network.db
```

For MySQL, create a database first:

```sql
CREATE DATABASE campus_network CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then configure:

```powershell
$env:DATABASE_URL = "mysql+pymysql://root:your_password@127.0.0.1:3306/campus_network?charset=utf8mb4"
$env:SECRET_KEY = "replace-with-a-random-secret"
$env:FLASK_APP = "run.py"
flask init-db
flask seed-data
flask detect-anomalies
python run.py
```

If `DATABASE_URL` is not set, the system automatically uses SQLite.

## Testing

Run automated tests:

```powershell
pytest -q
```

Latest local verification:

```text
17 passed
```

The test suite covers:

- route rendering
- health endpoint
- login and logout
- protected page redirects
- sample data generation
- CSV / JSON / TXT parsing
- data cleaning and deduplication
- database import
- analytics API
- log filtering
- CSV export
- anomaly detection
- directory collection
- system status report

## Browser QA Result

The system was also tested with real browser interactions. The final deep QA report includes:

```text
53 checks
0 failures
0 console problems
0 page errors
0 bad HTTP responses
```

Verified browser workflows:

- login with valid and invalid credentials
- protected page redirect
- every main navigation page
- desktop layout overflow check
- mobile layout overflow check
- file upload import
- validation data generation
- log keyword search
- log empty state
- log pagination
- CSV export
- behavior analysis chart rendering
- anomaly detection execution
- anomaly pagination
- directory collection
- system status and test report rendering
- logout

## Defense Demonstration Flow

Recommended demonstration order:

1. Login as administrator.
2. Open the dashboard and introduce the overall metrics and charts.
3. Open the log ingestion page and import validation data.
4. Open the log query page and demonstrate filtering, pagination, and CSV export.
5. Open the behavior analysis page and explain the traffic, protocol, category, user type, application, and ranking charts.
6. Open the anomaly detection page and run detection.
7. Explain rule-based detection and machine learning detection.
8. Open the report page and show runtime status, quality metrics, performance metrics, and test cases.
9. Run `pytest -q` to show automated test results if needed.

## Notes For Real Deployment

- Use a strong `SECRET_KEY`.
- Use MySQL or another production database for multi-user or long-running deployment.
- Place real or exported device logs into a secured ingestion directory.
- Avoid committing real user logs or sensitive network data.
- Add HTTPS and reverse proxy configuration for public deployment.
