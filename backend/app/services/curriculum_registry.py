# backend/app/services/curriculum_registry.py
"""
ATLAS AI 4.0 - v12 SkillPath Reforged: THE LOCKED CURRICULUM.

This file is pure data - zero AI calls, zero DB access. It is the single
source of truth for:
  * the 9 domain cards (Section 2 step 1),
  * the shared topic library (Section 5 - seeded ONCE, referenced everywhere),
  * each domain's roadmap order + phase mapping (Section 4, verbatim),
  * the 10/10/5 difficulty mix per 25-question subtopic set (Section 6),
  * the interactive-visualization kind per topic family (Learn mode).

Rule for every AI assistant touching this file: the topic and subtopic
lists below come directly from the founder's specification. They are the
product. Do NOT rename, reorder, merge or 'improve' them.
"""

from typing import Dict, List, TypedDict

# Locked per-subtopic question mix: 10 basic / 10 medium / 5 advanced = 25
QUESTIONS_PER_SUBTOPIC = 25
DIFFICULTY_MIX = {"basic": 10, "medium": 10, "advanced": 5}
MASTERY_CORRECT_THRESHOLD = 20      # >= 20/25 correct (80%) ticks the tab green
CORRECT_SCORE_THRESHOLD = 60        # an attempt counts correct at score >= 60

# Plan gate: which plan (months) unlocks which phase. Deterministic.
PHASE_MIN_PLAN_MONTHS = {"Foundation": 3, "Core": 3, "Advanced": 6}


class TopicSpec(TypedDict):
    title: str
    subtopics: List[str]
    default_kind: str          # 'code' | 'text' | 'sql' | 'math'
    viz_kind: str              # which interactive viz Learn mode mounts
    est_hours: int


# ----------------------------------------------------------------------
# The shared topic library - seeded once, referenced by every roadmap.
# ~196 unique subtopic sets across all keys (~4,900 questions).
# ----------------------------------------------------------------------
TOPIC_LIBRARY: Dict[str, TopicSpec] = {
    # ---- shared across DS / DA / AI / Backend --------------------------
    "python": {
        "title": "Python",
        "subtopics": ["list", "string", "loops", "function",
                      "dictionary", "OOP", "tuple", "set"],
        "default_kind": "code", "viz_kind": "loop_viz", "est_hours": 16,
    },
    "mysql": {
        "title": "MySQL",
        "subtopics": ["DDL", "DML", "DCL", "TCL", "data aggregation",
                      "grouping", "joins", "window functions"],
        "default_kind": "sql", "viz_kind": "join_viz", "est_hours": 14,
    },
    "numpy": {
        "title": "NumPy",
        "subtopics": ["array", "indexing", "slicing", "maths", "aggregation"],
        "default_kind": "code", "viz_kind": "array_viz", "est_hours": 8,
    },
    "pandas": {
        "title": "Pandas",
        "subtopics": ["data structure", "data inspection",
                      "selection & filtering", "data cleaning",
                      "data transformation", "grouping", "aggregation",
                      "combining datasets", "time series"],
        "default_kind": "code", "viz_kind": "dataframe_viz", "est_hours": 18,
    },
    "data_visualization": {
        "title": "Data Visualization",
        "subtopics": ["matplotlib", "seaborn", "plotly"],
        "default_kind": "code", "viz_kind": "chart_viz", "est_hours": 6,
    },
    "stats_prob_linalg": {
        "title": "Statistics, Probability & Linear Algebra",
        "subtopics": ["distributions", "Bayes theorem", "A/B testing",
                      "hypothesis testing", "linear algebra"],
        "default_kind": "math", "viz_kind": "distribution_viz", "est_hours": 12,
    },
    "machine_learning": {
        "title": "Machine Learning",
        "subtopics": [
            # Supervised (11)
            "linear regression", "logistic regression", "SVR & SVC", "KNN",
            "naive Bayes", "decision tree", "random forest", "AdaBoost",
            "gradient boosting", "XGBoost", "LightGBM",
            # Unsupervised (2)
            "k-means", "DBSCAN",
        ],
        "default_kind": "code", "viz_kind": "gradient_descent_viz",
        "est_hours": 30,
    },
    "feature_engineering": {
        "title": "Feature Engineering",
        "subtopics": ["feature engineering"],   # one set; admin can split later
        "default_kind": "code", "viz_kind": "feature_viz", "est_hours": 6,
    },
    "deep_learning": {
        "title": "Deep Learning",
        "subtopics": ["CNN", "RNN", "LSTM", "GNN"],
        "default_kind": "code", "viz_kind": "network_viz", "est_hours": 16,
    },
    "reinforcement_learning": {
        "title": "Reinforcement Learning",
        "subtopics": ["Q-learning", "SARSA"],
        "default_kind": "code", "viz_kind": "rl_grid_viz", "est_hours": 8,
    },

    # ---- Artificial Intelligence only ----------------------------------
    "advanced_architectures": {
        "title": "Advanced Architectures",
        "subtopics": ["Transformer architecture", "GNN Pro"],
        "default_kind": "text", "viz_kind": "attention_viz", "est_hours": 10,
    },

    # ---- Generative AI --------------------------------------------------
    "llm_basics": {
        "title": "LLM Basics",
        "subtopics": ["tokens", "embeddings", "context window"],
        "default_kind": "text", "viz_kind": "token_viz", "est_hours": 6,
    },
    "prompt_engineering": {
        "title": "Prompt Engineering",
        "subtopics": ["prompt engineering"],
        "default_kind": "text", "viz_kind": "prompt_viz", "est_hours": 4,
    },
    "rag": {
        "title": "RAG",
        "subtopics": ["vector DBs", "FAISS", "ChromaDB", "Pinecone"],
        "default_kind": "code", "viz_kind": "rag_viz", "est_hours": 10,
    },
    "langchain": {
        "title": "LangChain",
        "subtopics": ["LangChain"],
        "default_kind": "code", "viz_kind": "chain_viz", "est_hours": 6,
    },
    "fine_tuning": {
        "title": "Fine-Tuning",
        "subtopics": ["fine-tuning"],
        "default_kind": "text", "viz_kind": "loss_curve_viz", "est_hours": 6,
    },
    "agentic_ai": {
        "title": "Agentic AI",
        "subtopics": ["tool calling", "multi-agent systems", "CrewAI"],
        "default_kind": "code", "viz_kind": "agent_graph_viz", "est_hours": 8,
    },

    # ---- Frontend Developer ---------------------------------------------
    "html_css": {
        "title": "HTML & CSS",
        "subtopics": ["HTML", "CSS"],
        "default_kind": "code", "viz_kind": "box_model_viz", "est_hours": 10,
    },
    "javascript": {
        "title": "JavaScript",
        "subtopics": ["JavaScript"],
        "default_kind": "code", "viz_kind": "event_loop_viz", "est_hours": 12,
    },
    "react": {
        "title": "React",
        "subtopics": ["hooks", "state management"],
        "default_kind": "code", "viz_kind": "render_tree_viz", "est_hours": 12,
    },
    "tailwind_css": {
        "title": "Tailwind CSS",
        "subtopics": ["Tailwind CSS"],
        "default_kind": "code", "viz_kind": "utility_viz", "est_hours": 4,
    },

    # ---- Backend Developer only -----------------------------------------
    "fastapi": {
        "title": "FastAPI",
        "subtopics": ["FastAPI"],
        "default_kind": "code", "viz_kind": "request_flow_viz", "est_hours": 8,
    },
    "caching": {
        "title": "Caching",
        "subtopics": ["caching"],
        "default_kind": "text", "viz_kind": "cache_viz", "est_hours": 4,
    },
    "microservices": {
        "title": "Microservices Architecture",
        "subtopics": ["microservices architecture"],
        "default_kind": "text", "viz_kind": "service_mesh_viz", "est_hours": 6,
    },
    "realtime_api_infra": {
        "title": "Realtime & API Infrastructure",
        "subtopics": ["WebSockets", "rate limiting", "API gateway"],
        "default_kind": "code", "viz_kind": "socket_viz", "est_hours": 8,
    },
    "system_design": {
        "title": "System Design Fundamentals",
        "subtopics": ["system design fundamentals"],
        "default_kind": "text", "viz_kind": "architecture_viz", "est_hours": 8,
    },

    # ---- Cloud Computing only ---------------------------------------------
    "cloud_core_concepts": {
        "title": "Core Concepts",
        "subtopics": ["IaaS", "PaaS", "SaaS"],
        "default_kind": "text", "viz_kind": "cloud_layers_viz", "est_hours": 5,
    },
    "aws": {
        "title": "AWS",
        "subtopics": ["AWS"],
        "default_kind": "text", "viz_kind": "aws_map_viz", "est_hours": 8,
    },
    "cloud_networking": {
        "title": "Networking",
        "subtopics": ["VPC", "load balancers"],
        "default_kind": "text", "viz_kind": "vpc_viz", "est_hours": 6,
    },
    "cloud_security_basics": {
        "title": "Security Basics",
        "subtopics": ["security basics"],
        "default_kind": "text", "viz_kind": "iam_viz", "est_hours": 4,
    },
    "docker": {
        "title": "Docker",
        "subtopics": ["Docker"],
        "default_kind": "code", "viz_kind": "container_viz", "est_hours": 6,
    },

    # ---- MLOps (3 phases as topics) -----------------------------------------
    "mlops_foundation": {
        "title": "MLOps Foundation",
        "subtopics": ["Git/GitHub", "Docker basics",
                      "ML lifecycle concepts (train, deploy, monitor)"],
        "default_kind": "text", "viz_kind": "pipeline_viz", "est_hours": 8,
    },
    "mlops_core": {
        "title": "MLOps Core",
        "subtopics": ["Experiment tracking (MLflow, Weights & Biases)",
                      "Model serving (FastAPI + Docker, TorchServe)",
                      "CI/CD for ML (GitHub Actions)"],
        "default_kind": "code", "viz_kind": "pipeline_viz", "est_hours": 10,
    },
    "mlops_advanced": {
        "title": "MLOps Advanced",
        "subtopics": ["Orchestration (Kubeflow, Airflow)",
                      "Model monitoring & drift detection",
                      "Feature stores (Feast)",
                      "A/B testing models & canary deployments"],
        "default_kind": "text", "viz_kind": "drift_viz", "est_hours": 12,
    },

    # ---- Cybersecurity (3 phases as topics; concept-first, browser-safe) ----
    "cyber_foundation": {
        "title": "Cybersecurity Foundation",
        "subtopics": ["Networking basics (TCP/IP, DNS, firewalls)",
                      "Linux fundamentals & command line",
                      "OWASP Top 10"],
        "default_kind": "text", "viz_kind": "network_layers_viz", "est_hours": 8,
    },
    "cyber_core": {
        "title": "Cybersecurity Core",
        "subtopics": ["Web app security (SQLi, XSS, CSRF)",
                      "Cryptography basics (hashing, encryption, TLS)",
                      "Security tools (Wireshark, Nmap, Burp Suite)"],
        "default_kind": "text", "viz_kind": "crypto_viz", "est_hours": 10,
    },
    "cyber_advanced": {
        "title": "Cybersecurity Advanced",
        "subtopics": ["Intrusion Detection Systems",
                      "Threat hunting & SIEM tools",
                      "Penetration testing / ethical hacking (OSCP path)",
                      "Compliance: DPDP Act, RBI cybersecurity frameworks"],
        "default_kind": "text", "viz_kind": "siem_viz", "est_hours": 12,
    },
}


class RoadmapEntry(TypedDict):
    topic_key: str
    phase: str


class DomainSpec(TypedDict):
    name: str
    tagline: str
    roles: List[str]
    example_companies: List[str]
    roadmap: List[RoadmapEntry]


def _r(topic_key: str, phase: str) -> RoadmapEntry:
    return {"topic_key": topic_key, "phase": phase}


# ----------------------------------------------------------------------
# The nine locked domains, roadmap order verbatim from Section 4.
# ----------------------------------------------------------------------
DOMAIN_REGISTRY: Dict[str, DomainSpec] = {
    "data_science": {
        "name": "Data Science",
        "tagline": "From Python to production models",
        "roles": ["Data Scientist", "ML Engineer", "Applied Scientist"],
        "example_companies": ["Flipkart", "Swiggy", "Fractal", "Mu Sigma"],
        "roadmap": [
            _r("python", "Foundation"), _r("numpy", "Foundation"),
            _r("pandas", "Core"), _r("data_visualization", "Core"),
            _r("stats_prob_linalg", "Core"), _r("machine_learning", "Core"),
            _r("feature_engineering", "Core"),
            _r("deep_learning", "Advanced"),
            _r("reinforcement_learning", "Advanced"),
        ],
    },
    "data_analysis": {
        "name": "Data Analysis",
        "tagline": "SQL-first analytics and storytelling",
        "roles": ["Data Analyst", "Business Analyst", "BI Developer"],
        "example_companies": ["Deloitte", "ZS", "Paytm", "Nielsen"],
        "roadmap": [
            _r("mysql", "Foundation"), _r("python", "Foundation"),
            _r("numpy", "Core"), _r("pandas", "Core"),
            _r("data_visualization", "Core"),
            _r("stats_prob_linalg", "Advanced"),
        ],
    },
    "artificial_intelligence": {
        "name": "Artificial Intelligence",
        "tagline": "Data Science plus the modern AI stack",
        "roles": ["AI Engineer", "Research Engineer", "ML Scientist"],
        "example_companies": ["Google", "Microsoft", "Sarvam", "Krutrim"],
        "roadmap": [
            _r("python", "Foundation"), _r("numpy", "Foundation"),
            _r("pandas", "Core"), _r("data_visualization", "Core"),
            _r("stats_prob_linalg", "Core"), _r("machine_learning", "Core"),
            _r("feature_engineering", "Core"),
            _r("deep_learning", "Advanced"),
            _r("reinforcement_learning", "Advanced"),
            _r("advanced_architectures", "Advanced"),
        ],
    },
    "generative_ai": {
        "name": "Generative AI",
        "tagline": "LLMs, RAG and agents in production",
        "roles": ["GenAI Engineer", "LLM Application Developer"],
        "example_companies": ["OpenAI partners", "Sarvam", "Haptik", "Yellow.ai"],
        "roadmap": [
            _r("llm_basics", "Foundation"),
            _r("prompt_engineering", "Foundation"),
            _r("rag", "Core"), _r("langchain", "Core"),
            _r("fine_tuning", "Advanced"), _r("agentic_ai", "Advanced"),
        ],
    },
    "frontend_developer": {
        "name": "Frontend Developer",
        "tagline": "Modern UI engineering with React",
        "roles": ["Frontend Engineer", "UI Engineer"],
        "example_companies": ["Razorpay", "CRED", "Zerodha", "Atlassian"],
        "roadmap": [
            _r("html_css", "Foundation"), _r("javascript", "Foundation"),
            _r("react", "Core"), _r("tailwind_css", "Core"),
        ],
    },
    "backend_developer": {
        "name": "Backend Developer",
        "tagline": "APIs, data and systems at scale",
        "roles": ["Backend Engineer", "API Engineer", "SDE-1"],
        "example_companies": ["Amazon", "PhonePe", "Freshworks", "Zoho"],
        "roadmap": [
            _r("python", "Foundation"), _r("mysql", "Foundation"),
            _r("fastapi", "Core"), _r("caching", "Core"),
            _r("microservices", "Core"),
            _r("realtime_api_infra", "Advanced"),
            _r("system_design", "Advanced"),
        ],
    },
    "cloud_computing": {
        "name": "Cloud Computing",
        "tagline": "Cloud-native infrastructure fundamentals",
        "roles": ["Cloud Engineer", "DevOps Engineer (entry)"],
        "example_companies": ["AWS partners", "TCS Cloud", "Infosys Cobalt"],
        "roadmap": [
            _r("mysql", "Foundation"),
            _r("cloud_core_concepts", "Foundation"),
            _r("aws", "Core"), _r("cloud_networking", "Core"),
            _r("cloud_security_basics", "Core"), _r("docker", "Advanced"),
        ],
    },
    "mlops": {
        "name": "MLOps",
        "tagline": "Ship, serve and monitor ML in production",
        "roles": ["MLOps Engineer", "ML Platform Engineer"],
        "example_companies": ["Databricks partners", "Walmart Labs", "Dream11"],
        "roadmap": [
            _r("mlops_foundation", "Foundation"),
            _r("mlops_core", "Core"),
            _r("mlops_advanced", "Advanced"),
        ],
    },
    "cybersecurity": {
        "name": "Cybersecurity",
        "tagline": "Defensive security, concept-first and safe",
        "roles": ["Security Analyst", "SOC Analyst", "GRC Associate"],
        "example_companies": ["Palo Alto", "Quick Heal", "big-4 cyber teams"],
        "roadmap": [
            _r("cyber_foundation", "Foundation"),
            _r("cyber_core", "Core"),
            _r("cyber_advanced", "Advanced"),
        ],
    },
}

DOMAIN_ORDER = list(DOMAIN_REGISTRY.keys())   # card order on the selection screen


# ----------------------------------------------------------------------
# Pure helpers (no DB, no AI)
# ----------------------------------------------------------------------

def domain_stats(domain_key: str) -> dict:
    """Deterministic card numbers: topics / subtopic sets / question bank."""
    spec = DOMAIN_REGISTRY[domain_key]
    subtopic_sets = sum(
        len(TOPIC_LIBRARY[e["topic_key"]]["subtopics"]) for e in spec["roadmap"]
    )
    return {
        "topic_count": len(spec["roadmap"]),
        "subtopic_sets": subtopic_sets,
        "question_bank": subtopic_sets * QUESTIONS_PER_SUBTOPIC,
    }


def difficulty_sequence() -> List[str]:
    """The locked serving order for a 25-question bank: basic -> advanced."""
    return (["basic"] * DIFFICULTY_MIX["basic"]
            + ["medium"] * DIFFICULTY_MIX["medium"]
            + ["advanced"] * DIFFICULTY_MIX["advanced"])


def phase_unlocked(phase: str, plan_months: int) -> bool:
    return plan_months >= PHASE_MIN_PLAN_MONTHS.get(phase, 3)
