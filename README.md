# EcoSphere ESG Management Platform

EcoSphere is a local-first Odoo Community ESG platform. The working local demo addon is under:

```text
addons/ecosphere_esg
```

The platform is designed to run locally with Odoo and PostgreSQL at:

```text
http://localhost:8069
```

## Current Local Validation

- Odoo 19 Docker service runs at `localhost:8069`.
- PostgreSQL runs through Docker Compose.
- Database `ecosphere_demo` was created.
- Module `ecosphere_esg` was installed successfully.
- EcoSphere appears in the Odoo app launcher.
- `EcoSphere > Environmental > Carbon Transactions` loads with 3 demo records.

Demo admin login:

```text
admin@example.local
admin
```

## What Is Included

- Odoo-native Python models, XML views, ORM logic, ACLs, record rules, scheduled actions, chatter, QWeb report, demo data, and Odoo tests.
- Environmental workflows: emission factors, product ESG profiles, carbon transactions, Scope 1/2/3 reporting, verification, goals, and source record drill-down.
- Social workflows: CSR activities, challenge participation, proof review, XP ledger, badges, rewards, and employee dashboard entry points.
- Governance workflows: policies, acknowledgements, audits, compliance issues, overdue checks, reminders, and auditor access.
- Scoring engine: environmental/social/governance scores from 0 to 100, weighted department total, score history, and score explanation.

## Required Odoo Dependencies

```text
base, web, mail, hr, product, purchase, mrp, fleet, hr_expense
```

## Standard Local Setup

1. Install Python and PostgreSQL dependencies required by your Odoo checkout.
2. Create a PostgreSQL user:

```sql
CREATE ROLE odoo WITH LOGIN CREATEDB PASSWORD 'odoo';
```

3. Copy `odoo.conf.example` to `odoo.conf`.
4. Update `addons_path` so it includes this repository's `addons` directory.
5. Start Odoo:

```bash
python odoo-bin -c /path/to/odoo.conf
```

6. Open `http://localhost:8069`.
7. Create a database with demo data enabled.
8. Open Apps, update the app list, and install `EcoSphere ESG Management Platform`.

## Optional Docker Setup

Docker Compose is included for easier local setup:

```bash
docker compose up -d
```

It provides:

- Odoo service on port `8069`
- PostgreSQL service
- Custom addon volume mounted from `./addons`
- Persistent Odoo and PostgreSQL volumes

For one-off Odoo commands in Docker, use `odoo.docker.conf`.

## Testing

From an Odoo environment:

```bash
python odoo-bin -c /path/to/odoo.conf -d ecosphere_test --test-enable --stop-after-init -i ecosphere_esg
```

The test suite covers carbon calculation, duplicate prevention, evidence enforcement, XP awarding, badge awarding, reward balance/stock handling, policy acknowledgement, compliance overdue logic, and score bounds.

## Repository Note

This repository also contains the pre-existing remote addon folder `ecosphere_esg/`. The Docker-validated local hackathon build is in `addons/ecosphere_esg/`.
