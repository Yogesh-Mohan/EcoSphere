# EcoSphere ESG Management Platform

EcoSphere is a native Odoo addon for production-grade ESG management. It is designed to combine environmental accounting, social participation, governance controls, employee engagement, ESG scoring, dashboards, reports, and auditable workflows inside Odoo.

## Current Target

- Target Odoo version: 17.0 Community conventions.
- Current repository mode: standalone addon source tree.
- Current addon name: `ecosphere_esg`.
- Current workspace does not include an Odoo server, database, addons path, or configuration file.

## Installation

Add this repository directory, or its parent directory, to the Odoo addons path and update the app list.

Example command when Odoo is available:

```bash
odoo-bin -d <database> -u ecosphere_esg --addons-path=<odoo_addons>,<custom_addons> --stop-after-init
```

If the module is not installed yet:

```bash
odoo-bin -d <database> -i ecosphere_esg --addons-path=<odoo_addons>,<custom_addons> --stop-after-init
```

## Dependencies

The module depends on standard Odoo Community applications where available:

- `base`
- `mail`
- `web`
- `hr`
- `product`
- `purchase`
- `mrp`
- `hr_expense`
- `fleet`

No Enterprise-only dependency is planned unless the deployment repository proves that such modules are available and approved.

## User Roles

EcoSphere defines these role groups:

- ESG Employee
- Department ESG Manager
- ESG Officer
- Governance Auditor
- ESG Administrator

Access rules will be expanded by phase as business models are added. Sensitive employee evidence, XP history, and reward records are designed to be protected by record rules rather than UI hiding alone.

## UI Direction

The interface follows an Enterprise Sustainability Control Centre design direction:

- Native Odoo operational views for record management.
- Owl components only for dashboards and interaction-heavy experiences.
- No placeholder KPIs or static dashboard values.
- Every KPI must explain its unit, period, source, and drill-down action.
- Accessibility, responsive behavior, loading states, empty states, and permission states are required for custom UI.

## Emission Calculation

The planned carbon calculation formula is:

```text
emission_kgco2e = activity_value * emission_factor.factor_value * conversion_multiplier
```

Automatic source integrations will be idempotent. Recalculation updates an existing source-linked transaction instead of creating duplicates.

Current environmental implementation includes:

- Emission factors with activity type, scope, source, validity, region, and company support.
- Product ESG profile fields on products.
- Environmental goals with reduction/increase progress calculation.
- Carbon transactions with calculation explanation and validation workflow.
- Purchase confirmation integration for product-based emissions.
- Manufacturing integration service method for finished product emissions.

## Scoring Formula

All ESG scores are normalized to 0-100.

Department total score uses configured company weights:

```text
total = environmental_score * environmental_weight / 100
      + social_score * social_weight / 100
      + governance_score * governance_weight / 100
```

Default weights are Environmental 40, Social 30, Governance 30. The total must equal 100.

## Business Workflows

Planned production workflows include:

- Carbon transaction calculation, validation, and source reconciliation.
- CSR registration, evidence submission, review, approval, and XP award.
- Policy publication and employee acknowledgement tracking.
- Audit and compliance issue management with due-date reminders.
- Challenge participation, evidence review, and XP/points award.
- Badge auto-award based on structured metrics.
- Reward redemption with point and stock validation.
- Periodic ESG score snapshots.

Current social implementation includes:

- CSR activity lifecycle and participation tracking.
- Evidence submission and review workflow.
- Evidence-required approval validation.
- Immutable XP/points ledger foundation.
- Reversal ledger entries for approval reversal.
- Employee balances computed from ledger entries.

## Cron Jobs

Planned scheduled actions include:

- Policy acknowledgement reminders.
- Compliance due-date reminders.
- Overdue issue detection.
- Badge reconciliation.
- ESG score calculation.
- Source integration synchronization where automatic emission calculation is enabled.

## Reports

Planned reports include:

- Environmental Report
- Social Report
- Governance Report
- ESG Summary Report
- Custom Report Builder

PDF, Excel, and CSV exports are planned. The report builder will use controlled filters, not arbitrary SQL.

## Testing

When an Odoo runtime is available, run module tests with a command similar to:

```bash
odoo-bin -d <test_database> -i ecosphere_esg --test-enable --stop-after-init --addons-path=<odoo_addons>,<custom_addons>
```

## Known Limitations

- The current workspace does not include Odoo, so install/upgrade validation cannot yet run here.
- Phase 1 contains the application shell, security roles, core configuration, department ESG extensions, employee ESG recognition setting, ESG categories, and native configuration views.
- Environmental, social, governance, gamification, scoring, reports, and dashboards will be implemented phase by phase.

## Implementation Status

- Phase 0: complete with local validation.
- Phase 1: complete with local validation.
- Phase 2: environmental backend, views, security, source integration services, and tests complete with local validation.
- Phase 3: social CSR workflows, immutable XP ledger foundation, views, security, and tests complete with local validation.
- Full Odoo install/upgrade validation remains blocked until an Odoo runtime and database are available.
