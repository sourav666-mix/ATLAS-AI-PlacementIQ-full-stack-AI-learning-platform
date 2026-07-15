# __init__.py - admin subpackage router aggregation
# backend/app/routers/admin/__init__.py
"""Role-gated admin router subpackage.

Batch 12 introduces this package with the Jobs Board admin router. Later admin
sessions (auth, content, colleges, analytics, providers, championship) add their
own modules here. main.py includes each admin router explicitly, so this file
stays a simple package marker — no aggregation logic to conflict with later work.
"""