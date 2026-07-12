# EcoSphere ESG Management Platform

EcoSphere is a production-oriented native Odoo addon for ESG management. It is built as an Odoo module named `ecosphere_esg`, using Python models, Odoo ORM, XML views, security rules, scheduled actions, reports, and Owl components where custom interaction is justified.

The current repository contains the addon source code under:

```text
ecosphere_esg/
```

## Target Platform

- Target Odoo version: Odoo 17 Community conventions.
- Addon name: `ecosphere_esg`.
- Architecture: native Odoo addon, not React/FastAPI/Node.js.
- UI direction: Enterprise Sustainability Control Centre.
- Current runtime note: this workspace did not include an Odoo server/database, so install and upgrade validation must be run in an Odoo environment.

## Implemented Phases

### Phase 0 - Repository Analysis and Addon Skeleton

Status: complete with local validation.

- Created addon skeleton.
- Added manifest and init files.
- Added base security group structure.
- Added menu shell.
- Added README, implementation status, and demo script files.

### Phase 1 - Core, Configuration and Security

Status: complete with local validation.

- Added ESG settings on `res.company` and `res.config.settings`.
- Added ESG score weight validation where Environmental + Social + Governance must equal 100.
- Extended `hr.department` with ESG code, ESG manager, status, employee count, and latest score fields.
- Extended `hr.employee` with ESG recognition opt-in and computed ESG balances.
- Added `esg.category` master data.
- Added security groups, access controls, record rules, and native configuration views.

### Phase 2 - Environmental

Status: complete with local validation.

- Added emission factors with scope, activity type, source, validity, region, and company support.
- Added product ESG profile fields on `product.template`.
- Added environmental goals with reduction/increase progress calculation.
- Added carbon transactions with calculation explanation, validation workflow, duplicate prevention, and idempotent source upsert.
- Added purchase/manufacturing source integration service methods.
- Added environmental menus, list/form/search/graph/pivot views, and tests.

### Phase 3 - Social

Status: complete with local validation.

- Added CSR activities with lifecycle, capacity, department eligibility, organizer, and participation metrics.
- Added CSR participation with evidence attachments, proof description, hours, review workflow, rejection reason, and ledger links.
- Added evidence-required approval validation.
- Added immutable XP/points ledger foundation.
- Added approval reversal through negative ledger entries.
- Added social views, metrics views, security rules, and tests.

## Pending Phases

- Phase 4 - Governance: policies, acknowledgements, audits, compliance issues, overdue detection, scheduled reminders.
- Phase 5 - Gamification: challenges, badges, rewards, redemptions, leaderboards.
- Phase 6 - Scoring: department score snapshots, organization score, scoring explanations.
- Phase 7 - Notifications and reports: mail templates, reminders, PDF, XLSX, CSV, custom report builder.
- Phase 8 - Dashboards: Owl dashboards, reusable components, real ORM data services.
- Phase 9 - Demo and quality: full demo dataset, performance review, security hardening, final walkthrough.

## Installation

Place this repository, or the `ecosphere_esg` folder, in an Odoo addons path and update the app list.

Install:

```bash
odoo-bin -d <database> -i ecosphere_esg --addons-path=<odoo_addons>,<custom_addons> --stop-after-init
```

Upgrade:

```bash
odoo-bin -d <database> -u ecosphere_esg --addons-path=<odoo_addons>,<custom_addons> --stop-after-init
```

Run tests:

```bash
odoo-bin -d <test_database> -i ecosphere_esg --test-enable --stop-after-init --addons-path=<odoo_addons>,<custom_addons>
```

## Dependencies

The addon currently declares these Odoo dependencies:

- `base`
- `mail`
- `web`
- `hr`
- `product`
- `purchase`
- `mrp`
- `hr_expense`
- `fleet`

## Validation Completed Locally

- Python compile passed.
- XML parsing passed.
- Manifest data-file validation passed.
- Access CSV shape validation passed.

## Runtime Validation Still Required

The current development workspace did not include Odoo, so these checks must be completed inside an Odoo environment:

- Module install.
- Module upgrade.
- Server log inspection.
- Odoo test execution.
- Menu opening checks.
- Security role testing.
