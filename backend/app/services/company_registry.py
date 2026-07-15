# backend/app/services/company_registry.py
"""Curated directory of recruiters students can pull an Intel report for.

This is a static allow-list (not a DB table) so slugs are validated before we
ever spend an AI call, and the frontend has a browsable list. Add/adjust rows
freely — the report itself is generated + cached in company_intel_cache.
"""
from __future__ import annotations

# slug -> {name, sector, aliases}
_COMPANIES: dict[str, dict] = {
    "tcs":         {"name": "Tata Consultancy Services", "sector": "IT Services",
                    "aliases": ["tata consultancy", "tcs nqt"]},
    "infosys":     {"name": "Infosys", "sector": "IT Services", "aliases": ["infy"]},
    "wipro":       {"name": "Wipro", "sector": "IT Services", "aliases": []},
    "accenture":   {"name": "Accenture", "sector": "Consulting / IT", "aliases": []},
    "cognizant":   {"name": "Cognizant", "sector": "IT Services", "aliases": ["cts"]},
    "capgemini":   {"name": "Capgemini", "sector": "IT Services", "aliases": []},
    "hcltech":     {"name": "HCLTech", "sector": "IT Services", "aliases": ["hcl"]},
    "techmahindra":{"name": "Tech Mahindra", "sector": "IT Services", "aliases": ["tech m"]},
    "amazon":      {"name": "Amazon", "sector": "Product / Cloud", "aliases": ["aws"]},
    "microsoft":   {"name": "Microsoft", "sector": "Product / Cloud", "aliases": ["msft"]},
    "google":      {"name": "Google", "sector": "Product", "aliases": ["alphabet"]},
    "flipkart":    {"name": "Flipkart", "sector": "E-commerce", "aliases": []},
    "deloitte":    {"name": "Deloitte", "sector": "Consulting", "aliases": []},
    "zoho":        {"name": "Zoho", "sector": "Product / SaaS", "aliases": []},
    "paytm":       {"name": "Paytm", "sector": "Fintech", "aliases": ["one97"]},
    "phonepe":     {"name": "PhonePe", "sector": "Fintech", "aliases": []},
    "ibm":         {"name": "IBM", "sector": "IT Services / Product", "aliases": []},
    "oracle":      {"name": "Oracle", "sector": "Product / Cloud", "aliases": []},
}

# alias -> canonical slug (built once)
_ALIAS_INDEX: dict[str, str] = {}
for _slug, _meta in _COMPANIES.items():
    _ALIAS_INDEX[_slug] = _slug
    _ALIAS_INDEX[_meta["name"].lower()] = _slug
    for _a in _meta.get("aliases", []):
        _ALIAS_INDEX[_a.lower()] = _slug


def resolve_slug(raw: str) -> str | None:
    """Accept a slug, name, or alias; return the canonical slug or None."""
    if not raw:
        return None
    key = raw.strip().lower().replace(" ", "")
    if key in _COMPANIES:
        return key
    return _ALIAS_INDEX.get(raw.strip().lower())


def get_company(slug: str) -> dict | None:
    meta = _COMPANIES.get(slug)
    if not meta:
        return None
    return {"slug": slug, "name": meta["name"], "sector": meta["sector"]}


def list_companies() -> list[dict]:
    return [{"slug": s, "name": m["name"], "sector": m["sector"]}
            for s, m in _COMPANIES.items()]


def all_slugs() -> list[str]:
    return list(_COMPANIES.keys())