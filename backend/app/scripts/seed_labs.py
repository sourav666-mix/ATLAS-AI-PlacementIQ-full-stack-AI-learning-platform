# FILE: app/scripts/seed_labs.py
# BATCH 20 / v11 Phase 13 (new) - OFFLINE seeder: labs + starter datasets +
# graded task specs. Idempotent (upsert by title). Data Science + Data
# Analysis labs FIRST (v11 Phase 18 launch rule). Run from backend/:
#   python -m app.scripts.seed_labs
# Datasets use small, stable public CSVs (seaborn-data) — curated + cached.
# Every hidden test below was verified against a correct reference solution.

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.database import Base, engine
from app.models.lab import Lab, LabDataset

try:
    from app.database import SessionLocal
except ImportError:  # pragma: no cover
    from sqlalchemy.ext.asyncio import async_sessionmaker
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

SEABORN = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master"

DATASETS = [
    {"name": "penguins", "domain_tag": "ds",
     "file_url": f"{SEABORN}/penguins.csv", "rows_est": 344, "size_kb": 14,
     "description": "Palmer penguins — classic classification starter."},
    {"name": "tips", "domain_tag": "analysis",
     "file_url": f"{SEABORN}/tips.csv", "rows_est": 244, "size_kb": 8,
     "description": "Restaurant tips — cleaning + visualization starter."},
    {"name": "titanic", "domain_tag": "ds",
     "file_url": f"{SEABORN}/titanic.csv", "rows_est": 891, "size_kb": 57,
     "description": "Titanic survival — feature engineering practice."},
]

LABS = [
    {
        "title": "Data Science Lab: Train Your First Classifier",
        "lab_type": "ds",
        "dataset_ref": f"{SEABORN}/penguins.csv",
        "needs_gpu": False,
        "starter_code": (
            "import pandas as pd\n"
            "from sklearn.model_selection import train_test_split\n"
            "from sklearn.linear_model import LogisticRegression\n\n"
            f"df = pd.read_csv('{SEABORN}/penguins.csv')\n"
            "# TASK 1: drop rows with missing values into df_clean\n"
            "# TASK 2: X = the 4 numeric bill/flipper/mass columns,"
            " y = df_clean['species']\n"
            "# TASK 3: train LogisticRegression(max_iter=1000) as `model`"
            " with accuracy > 0.9 on a 25% test split\n"
        ),
        "graded_tasks_json": [
            {"id": "clean", "title": "Drop missing rows into df_clean",
             "points": 5,
             "test_code": "assert 'df_clean' in globals() and "
                          "df_clean.isna().sum().sum() == 0 and "
                          "len(df_clean) >= 300"},
            {"id": "split", "title": "Build X (4 numeric cols) and y",
             "points": 5,
             "test_code": "assert X.shape[1] == 4 and len(X) == len(y)"},
            {"id": "train", "title": "Trained model with accuracy > 0.9",
             "points": 10,
             "test_code": "from sklearn.metrics import accuracy_score\n"
                          "assert accuracy_score(y_test, "
                          "model.predict(X_test)) > 0.9"},
        ],
    },
    {
        "title": "Data Analysis Lab: Clean and Visualize Real Data",
        "lab_type": "analysis",
        "dataset_ref": f"{SEABORN}/tips.csv",
        "needs_gpu": False,
        "starter_code": (
            "import pandas as pd\nimport matplotlib\n"
            "matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n\n"
            f"df = pd.read_csv('{SEABORN}/tips.csv')\n"
            "# TASK 1: add column tip_pct = tip / total_bill * 100\n"
            "# TASK 2: summary = mean tip_pct grouped by day"
            " (a pandas Series)\n"
            "# TASK 3: save a bar chart of `summary` as chart.png\n"
        ),
        "graded_tasks_json": [
            {"id": "feature", "title": "tip_pct column added", "points": 5,
             "test_code": "assert 'tip_pct' in df.columns and "
                          "abs(df['tip_pct'].mean() - 16.08) < 1.0"},
            {"id": "groupby", "title": "Mean tip_pct by day", "points": 5,
             "test_code": "assert hasattr(summary, 'index') and "
                          "len(summary) == 4"},
            {"id": "chart", "title": "chart.png saved", "points": 10,
             "test_code": "import os\nassert os.path.exists('chart.png') "
                          "and os.path.getsize('chart.png') > 1000"},
        ],
    },
    {
        "title": "AI/ML Lab: From-Scratch Gradient Descent + GPU Bridge",
        "lab_type": "ml",
        "dataset_ref": f"{SEABORN}/penguins.csv",
        "needs_gpu": True,
        "starter_code": (
            "import numpy as np\n"
            "# TASK 1: implement mse(y_true, y_pred)\n"
            "# TASK 2: implement gradient_step(w, X, y, lr) for linear"
            " regression\n"
            "# Deep-learning extension runs on the free Colab GPU bridge.\n"
        ),
        "graded_tasks_json": [
            {"id": "mse", "title": "mse() correct", "points": 5,
             "test_code": "import numpy as np\n"
                          "assert abs(mse(np.array([1,2]), "
                          "np.array([1,4])) - 2.0) < 1e-6"},
            {"id": "gradstep", "title": "gradient_step() reduces loss",
             "points": 10,
             "test_code": "import numpy as np\n"
                          "X=np.array([[1.],[2.]]); y=np.array([2.,4.])\n"
                          "w0=np.zeros(1); w1=gradient_step(w0,X,y,0.1)\n"
                          "assert mse(y, X@w1) < mse(y, X@w0)"},
        ],
    },
]


async def _domain_id(session, preferred_slugs) -> str:
    from app.services.admin_common import model_for_table  # Batch 16 helper
    Domain = model_for_table("domains")
    rows = (await session.execute(select(Domain))).scalars().all()
    if not rows:
        raise SystemExit("No domains found — run seed_content.py first.")
    by_slug = {getattr(r, "slug", None): r for r in rows}
    for slug in preferred_slugs:
        if by_slug.get(slug) is not None:
            return by_slug[slug].id
    return rows[0].id


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # no-op if migrated
    async with SessionLocal() as session:
        for spec in DATASETS:
            exists = (await session.execute(select(LabDataset).where(
                LabDataset.name == spec["name"]))).scalars().first()
            if exists is None:
                session.add(LabDataset(**spec))
                print(f"  + dataset {spec['name']}")
        slug_pref = {"ds": ("data-science",), "analysis": ("data-analysis",
                                                           "data-science"),
                     "ml": ("ai-ml", "machine-learning", "data-science")}
        for spec in LABS:
            exists = (await session.execute(select(Lab).where(
                Lab.title == spec["title"]))).scalars().first()
            if exists is not None:
                exists.starter_code = spec["starter_code"]
                exists.graded_tasks_json = spec["graded_tasks_json"]
                print(f"  ~ updated lab {spec['title']}")
                continue
            domain_id = await _domain_id(session,
                                         slug_pref[spec["lab_type"]])
            session.add(Lab(domain_id=domain_id, **spec))
            print(f"  + lab {spec['title']}")
        await session.commit()
    print("seed_labs: done.")


if __name__ == "__main__":
    asyncio.run(main())