# FILE: app/services/colab_service.py
# BATCH 20 / v11 Phase 13 (new) - The Colab GPU bridge: generate a
# ready-to-run .ipynb (student code + dataset loader + results callback) and
# hand it to the frontend for one-click upload to Colab. Zero server GPU,
# zero storage — the notebook is generated on the fly, never persisted.

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.lab import Lab
from app.services.lab_service import get_or_create_session


def _md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {},
            "source": source.splitlines(keepends=True)}


def _code(source: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": source.splitlines(keepends=True)}


def build_notebook(lab: Lab, student_code: Optional[str],
                   api_base: str) -> dict:
    dataset = lab.dataset_ref or ""
    loader = (f"import pandas as pd\n"
              f"df = pd.read_csv('{dataset}')\n"
              f"print(df.shape); df.head()"
              if dataset.startswith("http") else
              "# Upload your dataset with the Files panel on the left,\n"
              "# then: import pandas as pd; df = pd.read_csv('your.csv')")
    task_lines = "\n".join(
        f"# {i + 1}. {task.get('title', task.get('id'))}"
        for i, task in enumerate(lab.graded_tasks_json or []))
    cells = [
        _md(f"# ATLAS Live Lab — {lab.title} (GPU via Colab)\n\n"
            f"Runtime → Change runtime type → **T4 GPU**, then Run all.\n\n"
            f"Graded tasks:\n{task_lines}\n"),
        _code("!pip -q install scikit-learn pandas matplotlib torch"),
        _code(loader),
        _code(student_code or lab.starter_code or "# your code here"),
        _md("## Report results back to ATLAS\n"
            "Run the cell below AFTER your tasks pass locally. Paste your "
            "ATLAS token when asked — it marks the GPU tasks passed on your "
            "dashboard."),
        _code(
            "import requests, getpass, json\n"
            f"API = '{api_base.rstrip('/')}'\n"
            "token = getpass.getpass('Paste your ATLAS access token: ')\n"
            "payload = {'lab_id': '" + lab.id + "', "
            "'tasks_passed': {t.get('id'): True for t in "
            + repr([{"id": t.get("id")} for t in (lab.graded_tasks_json or [])])
            + "}}\n"
            "r = requests.post(API + '/lab/grade', json=payload,\n"
            "                  headers={'Authorization': f'Bearer {token}'})\n"
            "print(r.status_code, r.text[:200])"),
    ]
    return {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"colab": {"provenance": []},
                         "kernelspec": {"name": "python3",
                                        "display_name": "Python 3"}},
            "cells": cells}


async def launch(db: AsyncSession, user_id: str, lab_id: str,
                 student_code: Optional[str], api_base: str) -> dict:
    lab = await db.get(Lab, lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    if not lab.needs_gpu:
        raise HTTPException(status_code=409,
                            detail="This lab runs fully in the browser — "
                                   "no Colab bridge needed.")
    session = await get_or_create_session(db, user_id, lab_id)
    session.launched_colab = True
    if student_code:
        session.code_snapshot = student_code
    await db.commit()
    open_url = (getattr(settings, "COLAB_TEMPLATE_URL", "") or
                "https://colab.research.google.com/#create=true")
    safe_title = "".join(c if c.isalnum() else "_" for c in lab.title)[:60]
    return {"filename": f"atlas_lab_{safe_title}.ipynb",
            "notebook": build_notebook(lab, student_code, api_base),
            "open_url": open_url,
            "note": "Download the notebook, open Colab (File → Upload "
                    "notebook), switch runtime to T4 GPU, Run all."}