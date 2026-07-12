# EcoSphere ESG Management Platform

EcoSphere is a local-first Odoo Community addon named `ecosphere_esg`. It connects operational Odoo data to ESG transactions, verification, scoring, dashboards, corrective actions, reports, and an audit trail.

The standard local URL is:

```text
http://localhost:8069
```

## What Is Included

- Odoo-native Python models, XML views, ORM logic, ACLs, record rules, scheduled actions, chatter, QWeb PDF report, and Odoo tests.
- Environmental workflows: emission factors, product ESG profiles, carbon transactions, Scope 1/2/3 reporting, verification, goals, and source record drill-down.
- Social workflows: CSR activities, challenge participation, proof review, XP ledger, badges, rewards, and employee dashboard entry points.
- Governance workflows: policies, acknowledgements, audits, compliance issues, overdue checks, reminders, and auditor access.
- Scoring engine: environmental/social/governance scores from 0 to 100, weighted department total, score history, and score explanation.
- Demo data for departments, employees, factors, transactions, goals, CSR, challenges, policies, audits, compliance issues, rewards, badges, and score history.

## Dependencies

Target version: Odoo Community 19.0.

Required Odoo modules:

```text
base, web, mail, hr, product, purchase, mrp, fleet, hr_expense
```

Required system services:

```text
Python 3.11+ or the Python version required by your Odoo checkout
PostgreSQL 14+
```

## 1. Install Python And PostgreSQL Dependencies

Install PostgreSQL from your OS package manager or from the official installer.

Clone Odoo Community locally, then install its Python requirements from the Odoo source directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install wheel
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install wheel
pip install -r requirements.txt
```

Install OS libraries required by Odoo for PDF/reporting according to your Odoo platform guide, including PostgreSQL client headers and `wkhtmltopdf` if your Odoo version still uses it for PDF rendering.

## 2. Create The PostgreSQL User

Create a local PostgreSQL role for Odoo:

```bash
createuser --createdb --username postgres --no-createrole --no-superuser --pwprompt odoo
```

Use this password for local development:

```text
odoo
```

Equivalent SQL:

```sql
CREATE ROLE odoo WITH LOGIN CREATEDB PASSWORD 'odoo';
```

## 3. Configure Odoo

Copy the example config:

```bash
cp odoo.conf.example odoo.conf
```

Update `addons_path` so it includes both your Odoo core addons and this repository addon path. Example:

```ini
addons_path = /path/to/odoo/odoo/addons,/path/to/egs/addons
http_port = 8069
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
logfile = /path/to/odoo.log
```

On Windows, use absolute Windows paths, for example:

```ini
addons_path = C:\odoo\odoo\addons,C:\Users\Anuraag S\Downloads\egs\addons
```

## 4. Start The Odoo Server

From your Odoo source directory:

```bash
python odoo-bin -c /path/to/egs/odoo.conf
```

On Windows:

```powershell
python odoo-bin -c "C:\Users\Anuraag S\Downloads\egs\odoo.conf"
```

Open:

```text
http://localhost:8069
```

## 5. Create The Database

In the Odoo database manager at `http://localhost:8069/web/database/manager`:

1. Create a new database, for example `ecosphere_demo`.
2. Enable demo data if you want the hackathon walkthrough records.
3. Set the admin password for the local database.

## 6. Install The EcoSphere Addon

In Odoo:

1. Open Apps.
2. Activate developer mode if the addon list is cached.
3. Click Update Apps List.
4. Search for `EcoSphere ESG Management Platform` or `ecosphere_esg`.
5. Install the module.

## 7. Load Demo Data

If demo data was enabled at database creation, Odoo loads `addons/ecosphere_esg/data/demo_data.xml` automatically when the module installs.

For an existing database without demo data, start Odoo with demo loading enabled or create a fresh local demo database. The demo includes:

- Logins: `esg_manager / esg_manager`, `esg_auditor / esg_auditor`, `esg_employee / esg_employee`
- Three departments and ten employees
- Multiple emission factors and product ESG profiles
- Carbon transactions, environmental goals, CSR activities, challenges, policies, acknowledgements, audits, compliance issues, badges, rewards, redemptions, and score history

## 8. Open The Platform

Go to:

```text
http://localhost:8069
```

Then open the EcoSphere menu. Recommended demo flow:

1. Review carbon transactions and verify pending Scope 3 material emissions.
2. Open Environmental Goals and refresh progress from verified carbon data.
3. Approve CSR or challenge submissions and inspect the points ledger.
4. Acknowledge a policy from the employee account.
5. Review overdue compliance issues from the auditor or manager account.
6. Open Score History and print the ESG Summary Report.
7. Open Action Centre to see rule-based recommendations.

## Optional Docker Compose

Docker is optional. The standard local installation above remains supported.

Start PostgreSQL and Odoo:

```bash
docker compose up
```

The compose file provides:

- `odoo` service on port `8069`
- `postgres` service
- `./addons` mounted as a custom addon volume
- Persistent PostgreSQL and Odoo data volumes

Then open:

```text
http://localhost:8069
```

Create a database and install EcoSphere from Apps.

## Testing

From the Odoo source directory, run:

```bash
python odoo-bin -c /path/to/egs/odoo.conf -d ecosphere_test --test-enable --stop-after-init -i ecosphere_esg
```

The test suite covers:

- Carbon calculation and duplicate source prevention
- Evidence enforcement
- Approval/rejection and XP award only once
- Badge auto-award
- Reward balance and stock handling
- Policy acknowledgement
- Compliance overdue logic
- Score calculation bounds

## Architecture

EcoSphere uses standard Odoo layers:

- Models in `addons/ecosphere_esg/models`
- Security groups, ACLs, and record rules in `addons/ecosphere_esg/security`
- Menus, actions, forms, lists, kanban, calendar, pivot, and graph views in `addons/ecosphere_esg/views`
- Scheduled actions, email templates, sequences, and demo data in `addons/ecosphere_esg/data`
- QWeb PDF report in `addons/ecosphere_esg/reports`
- Odoo transaction tests in `addons/ecosphere_esg/tests`

## Role Matrix

| Role | Access |
| --- | --- |
| ESG Employee | Own activities, proof submissions, policy acknowledgements, points, badges, and redemptions |
| Department ESG Manager | Department operational ESG records and approvals |
| ESG Manager | Organization-wide ESG data, verification, configuration, scoring, and action centre |
| ESG Auditor | Audits, policies, compliance issues, and governance evidence |
| ESG Administrator | Full configuration and administrative access |

## Known Limitations

- Email delivery depends on local outgoing mail configuration.
- External integrations are intentionally local/offline-safe placeholders through Odoo-native source hooks.
- XLSX export is not custom-coded; use Odoo list export or add `xlsxwriter`-based report generation as a later enhancement.
- Odoo 19 should be used where available. If your Docker registry does not yet provide `odoo:19.0`, switch the image and manifest version to the Odoo Community version installed locally.

## Future Improvements

- Add richer OWL dashboards once core workflows are stable.
- Add custom XLSX exports for each ESG report family.
- Expand source hooks for more precise purchase, fleet, manufacturing, and expense emission quantities.
- Add more granular multi-company tests and data-lineage report pages.
