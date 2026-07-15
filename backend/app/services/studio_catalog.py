# backend/app/services/studio_catalog.py
"""Interview Studio catalog — 16+ interview domains × 3 levels × 4 lengths.

Pure data + lookups, no DB, no AI. The frontend SetupWizard reads this list;
the service validates against it. Extend freely.
"""
from __future__ import annotations

# slug -> display name + focus hint fed to the question-set prompt
DOMAINS: dict[str, dict] = {
    "data_science":       {"name": "Data Science",
                           "focus": "statistics, ML fundamentals, pandas, model evaluation, case questions"},
    "data_analysis":      {"name": "Data Analysis",
                           "focus": "SQL, Excel, dashboards, metrics, business reasoning"},
    "software_engineer":  {"name": "Software Engineering",
                           "focus": "DSA, OOP, system basics, debugging, code quality"},
    "ai_engineer":        {"name": "AI Engineering",
                           "focus": "deep learning, model serving, prompt engineering, evaluation"},
    "genai":              {"name": "Generative AI",
                           "focus": "LLMs, RAG, fine-tuning, embeddings, safety"},
    "mlops":              {"name": "MLOps",
                           "focus": "pipelines, CI/CD for models, monitoring, drift, deployment"},
    "cloud_computing":    {"name": "Cloud Computing",
                           "focus": "AWS/Azure/GCP basics, networking, IAM, cost, architecture"},
    "backend":            {"name": "Backend Development",
                           "focus": "APIs, databases, caching, auth, scaling"},
    "frontend":           {"name": "Frontend Development",
                           "focus": "JavaScript, React, CSS, performance, accessibility"},
    "fullstack":          {"name": "Full-Stack Development",
                           "focus": "end-to-end features, API design, DB modeling, deployment"},
    "devops":             {"name": "DevOps",
                           "focus": "Docker, Kubernetes, CI/CD, observability, incident response"},
    "cybersecurity":      {"name": "Cybersecurity",
                           "focus": "OWASP, network security, threat modeling, incident handling"},
    "database":           {"name": "Database Engineering",
                           "focus": "SQL depth, indexing, transactions, normalization, tuning"},
    "system_design":      {"name": "System Design",
                           "focus": "scalability, load balancing, caching, trade-offs, estimation"},
    "product_analyst":    {"name": "Product Analytics",
                           "focus": "A/B testing, funnels, metrics trees, SQL, storytelling"},
    "hr_behavioral":      {"name": "HR & Behavioral",
                           "focus": "STAR answers, strengths/weaknesses, teamwork, conflict, motivation"},
    "aptitude_verbal":    {"name": "Aptitude & Communication",
                           "focus": "quantitative reasoning explained aloud, logic, clear articulation"},
}

LEVELS = ["beginner", "intermediate", "advanced"]
QUESTION_COUNTS = [3, 10, 15, 20]


def resolve_domain(raw: str) -> dict | None:
    """Accept a slug or display name; return {slug, name, focus} or None."""
    if not raw:
        return None
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    if key in DOMAINS:
        d = DOMAINS[key]
        return {"slug": key, "name": d["name"], "focus": d["focus"]}
    # try display-name match
    low = raw.strip().lower()
    for slug, d in DOMAINS.items():
        if d["name"].lower() == low:
            return {"slug": slug, "name": d["name"], "focus": d["focus"]}
    return None


def list_domains() -> list[dict]:
    return [{"slug": s, "name": d["name"]} for s, d in DOMAINS.items()]