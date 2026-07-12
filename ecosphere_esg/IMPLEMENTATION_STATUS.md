# EcoSphere ESG Implementation Status

## Phase 0 - Repository Analysis and Addon Skeleton

Status: Complete with local validation

## Environment Findings

- Workspace path: `/mnt/c/Users/Anuraag S/Downloads/eco`
- Git repository: no
- Odoo executable: not found
- Python `odoo` package: not installed
- Existing addons path: not detected
- Existing Odoo version: not detected
- Working assumption: Odoo 17.0 Community-compatible addon

## Implemented

- Created `ecosphere_esg` addon directory.
- Added Odoo manifest.
- Added package init files.
- Added base ESG security groups.
- Added empty access CSV ready for model access rows.
- Added empty record-rule container ready for model rules.
- Added root EcoSphere menu shell with role-restricted sections.
- Added initial README.

## Verification

- Odoo install/upgrade: blocked because no Odoo server or database is available in this workspace.
- Server log inspection: blocked because no Odoo server is available.
- Odoo tests: blocked because no Odoo server or test database is available.
- Python compile: passed.
- XML parsing: passed.
- Manifest/data-file validation: passed.
- Access CSV shape validation: passed.

## Phase Gate

Phase 1 began after Phase 0 local validation passed. Full Odoo installation verification requires an Odoo runtime.

## Phase 1 - Core, Configuration and Security

Status: Complete with local validation

## Implemented

- Added company ESG configuration fields on `res.company`.
- Added ESG settings exposure through `res.config.settings`.
- Enforced score weights totaling 100.
- Enforced non-negative policy and compliance reminder windows.
- Extended `hr.department` with ESG code, ESG manager, status, latest score fields, and computed active employee count.
- Extended `hr.employee` with ESG public recognition opt-in and managed ESG department relation.
- Added `esg.category` master data model with type, description, active flag, company support, uniqueness, and multi-company rule.
- Added access controls for ESG categories by role.
- Added Odoo-native ESG settings view.
- Added Odoo-native ESG category list, form, and search views.
- Added Odoo-native department ESG list, form, and search views.
- Added reusable SCSS design tokens for the future custom UI layer.

## Verification

- Odoo install/upgrade: blocked because no Odoo runtime is available.
- Python compile: passed.
- XML parsing: passed.
- Manifest/data-file validation: passed.
- Access CSV shape validation: passed.

## Notes

- The Configuration parent menu is visible to department managers, officers, auditors, and administrators, but ESG Settings remains administrator-only.
- Department and category screens use standard Odoo views to preserve native search, grouping, export, and access behavior.

## Phase 2 - Environmental

Status: Complete with local validation; Odoo runtime validation pending

## Implemented

- Added `esg.emission.factor` with scope, activity type, source, region, validity, company support, constraints, chatter, and active factor selection helper.
- Added ESG product profile fields on `product.template` for category, emission factor, carbon value per unit, recycled percentage, renewable material percentage, recyclability, supplier sustainability rating, and notes.
- Added `esg.environmental.goal` with reduction/increase progress calculation, owner, department, target values, workflow actions, constraints, chatter, and activities.
- Added `esg.carbon.transaction` with sequence, source identity, emission factor, activity data, Decimal-safe Odoo float rounding, calculation explanation, state workflow, chatter, activities, duplicate prevention, and idempotent source upsert helper.
- Added purchase and manufacturing source integration service methods.
- Added purchase order confirmation hook to generate/update purchase emissions when automatic calculation is enabled.
- Added environmental menu actions and native Odoo views for emission factors, carbon transactions, environmental goals, product ESG profiles, and environmental analysis.
- Added graph and pivot analysis for carbon transactions.
- Added model access rules and company/department record rules for environmental models.
- Added Odoo tests for carbon calculation, automatic upsert idempotency, duplicate source prevention, environmental goal progress, product ESG validation, and ESG weight validation.

## Verification

- Odoo install/upgrade: blocked because no Odoo runtime is available.
- Server log inspection: blocked because no Odoo server is available.
- Odoo tests: test files added but blocked because no Odoo test database is available.
- Python compile: passed.
- XML parsing: passed.
- Manifest/data-file validation: passed.
- Access CSV shape validation: passed.

## Environmental Integration Rules

- Purchase emissions are generated after purchase confirmation for confirmed or done purchase orders.
- Purchase quantity uses received quantity when available, otherwise ordered quantity.
- Manufacturing emissions are provided through a service method for finished product quantity and product ESG factor.
- Automatic transactions are keyed by company, source model, source record, source line reference, and emission factor.
- Recalculation updates the existing transaction instead of creating duplicates.
- Validated carbon transactions cannot be deleted.

## Phase 3 - Social

Status: Complete with local validation; Odoo runtime validation pending

## Implemented

- Added `esg.csr.activity` with sequence, category, departments, organizer, schedule, capacity, points, lifecycle status, participation metrics, chatter, and activities.
- Added `esg.csr.participation` with employee, department, evidence attachments, proof description, volunteering hours, completion date, review workflow, rejection reason, and ledger links.
- Added duplicate prevention for one employee per activity.
- Enforced evidence and positive hours before CSR approval.
- Added approval workflow that awards XP and points through immutable ledger entries only after approval.
- Added reversal workflow that creates a negative ledger entry instead of editing historical points.
- Added `esg.xp.ledger` foundation with immutable entries, source references, reversal links, and balance helper.
- Added computed employee ESG XP and points balances from ledger entries.
- Added role-aware access controls and record rules for CSR activities, CSR participation, and XP ledger entries.
- Added Odoo-native CSR kanban, list, form, calendar, graph, pivot, social metrics, evidence review, and XP ledger views.
- Added tests for CSR duplicate prevention, evidence requirement, single XP award, reversal ledger entries, and ledger immutability.

## Verification

- Odoo install/upgrade: blocked because no Odoo runtime is available.
- Server log inspection: blocked because no Odoo server is available.
- Odoo tests: test files added but blocked because no Odoo test database is available.
- Python compile: passed.
- XML parsing: passed.
- Manifest/data-file validation: passed.
- Access CSV shape validation: passed.

## Social Workflow Rules

- Employees can join published or ongoing eligible CSR activities.
- Employees can submit evidence and hours for their own participation.
- Approval requires submitted state, proof attachment when company evidence is mandatory, and positive participation hours.
- Approval creates one immutable ledger entry.
- Reversal creates a separate negative ledger entry and preserves history.
- Ordinary employees cannot write review outcome fields directly.
