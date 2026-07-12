# -*- coding: utf-8 -*-

{
    "name": "EcoSphere ESG Management Platform",
    "summary": "Enterprise ESG management, carbon accounting, governance, and sustainability engagement",
    "description": """
EcoSphere is a native Odoo ESG management platform for environmental,
social, governance, scoring, reporting, and employee engagement workflows.
    """,
    "version": "17.0.1.0.0",
    "category": "Sustainability/ESG",
    "author": "EcoSphere",
    "website": "https://example.com/ecosphere",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "web",
        "hr",
        "product",
        "purchase",
        "mrp",
        "hr_expense",
        "fleet",
    ],
    "data": [
        "security/esg_security.xml",
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/sequences.xml",
        "views/menu_views.xml",
        "views/configuration_views.xml",
        "views/department_views.xml",
        "views/environmental_views.xml",
        "views/social_views.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "ecosphere_esg/static/src/scss/esg_tokens.scss",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
