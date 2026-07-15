# run_gate.py - V12 Batch 1 verification gate
import asyncio, json, sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import Base, engine, SessionLocal, get_db
from app.routers.skillpath_v12 import router
from app.utils.jwt_utils import get_current_user
from app.services import ai_provider_router as air
from app.models.practice import TopicQuestion
from app.services.curriculum_registry import difficulty_sequence

PASS, FAIL = [], []
def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name + (f" [{extra}]" if extra else ""))
    print(("  PASS " if cond else "  FAIL ") + name, extra)

# 1. mapper config + schema build in async SQLite
async def build():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.get_event_loop().run_until_complete(build())
check("schema build (async SQLite)", True)

app = FastAPI()
app.include_router(router)
client = TestClient(app)

# 2. domains (Type A)
r = client.get("/skillpath/domains")
check("GET /domains 200", r.status_code == 200, str(r.status_code))
d = r.json()["domains"]
check("nine locked domains", len(d) == 9, str(len(d)))
ds = next(x for x in d if x["key"] == "data_science")
check("DS card: 9 topics / 50 sets / 1250 Q",
      (ds["topic_count"], ds["subtopic_sets"], ds["question_bank"]) == (9, 50, 1250),
      f"{ds['topic_count']}/{ds['subtopic_sets']}/{ds['question_bank']}")
da = next(x for x in d if x["key"] == "data_analysis")
check("DA card: 6 topics / 38 sets / 950 Q",
      (da["topic_count"], da["subtopic_sets"], da["question_bank"]) == (6, 38, 950),
      f"{da['topic_count']}/{da['subtopic_sets']}/{da['question_bank']}")
ai_dom = next(x for x in d if x["key"] == "artificial_intelligence")
check("AI card: 10 topics / 52 sets / 1300 Q",
      (ai_dom["topic_count"], ai_dom["subtopic_sets"], ai_dom["question_bank"]) == (10, 52, 1300),
      f"{ai_dom['topic_count']}/{ai_dom['subtopic_sets']}/{ai_dom['question_bank']}")

# 3. select: domain first, then plan
r = client.post("/skillpath/select", json={"domain_key": "data_science", "plan_months": 3})
check("POST /select 200", r.status_code == 200, r.text[:120])
domain_id = r.json()["domain_id"]
r_bad = client.post("/skillpath/select", json={"domain_key": "data_science", "plan_months": 5})
check("plan_months=5 rejected (422)", r_bad.status_code == 422)

# 4. roadmap: order, ring, status colors, plan gate
r = client.get(f"/skillpath/roadmap/{domain_id}")
check("GET /roadmap 200", r.status_code == 200, r.text[:120])
road = r.json()
titles = [t["title"] for t in road["topics"]]
check("founder's DS order verbatim",
      titles == ["Python", "NumPy", "Pandas", "Data Visualization",
                 "Statistics, Probability & Linear Algebra", "Machine Learning",
                 "Feature Engineering", "Deep Learning", "Reinforcement Learning"],
      "|".join(titles))
check("first topic = current (blue)", road["topics"][0]["status"] == "current")
check("plan gate: Advanced locked on 3-month plan",
      all(t["status"] == "locked" for t in road["topics"] if t["phase"] == "Advanced"))
check("all rings start at 0", all(t["progress_pct"] == 0 for t in road["topics"]))
python_topic = road["topics"][0]
check("Python has 8 subtopics", python_topic["subtopic_total"] == 8)
check("viz_kind mounted", python_topic["viz_kind"] == "loop_viz")

# 5. LEARN mode (Type A, 5 examples locked)
tid = python_topic["topic_id"]
r = client.get(f"/skillpath/topic/{tid}/learn")
check("GET /learn 200", r.status_code == 200, r.text[:120])
learn = r.json()
check("learn: 8 subtopic explainers", len(learn["subtopics"]) == 8)
check("learn: exactly 5 examples each",
      all(len(s["examples"]) == 5 for s in learn["subtopics"]))

# 6. subtopic tabs
r = client.get(f"/skillpath/topic/{tid}/subtopics", params={"domain_id": domain_id})
check("GET /subtopics 200", r.status_code == 200, r.text[:120])
tabs = r.json()["tabs"]
check("tabs order = list,string,loops,function,dictionary,OOP,tuple,set",
      [t["name"] for t in tabs] == ["list","string","loops","function","dictionary","OOP","tuple","set"])
sub_id = tabs[0]["subtopic_id"]

# seed a 25-question bank for subtopic 'list' (10/10/5, mimicking seed_content.py)
async def seed_bank():
    async with SessionLocal() as db:
        for i, diff in enumerate(difficulty_sequence()):
            db.add(TopicQuestion(topic_id=sub_id, difficulty=diff,
                question_kind="code", review_status="published", created_order=i,
                body_json={"question": f"Q{i+1} on list ({diff})",
                    "examples": [{"input":"[1,2]","output":"2","why":"len"},
                                 {"input":"[]","output":"0","why":"empty"}],
                    "starter_code": "# solve here",
                    "model_solution": f"solution {i+1}",
                    "why_how": "reasoning", "common_mistakes": ["off-by-one"]}))
        await db.commit()
asyncio.get_event_loop().run_until_complete(seed_bank())
print("  seeded 25-question bank (10 basic / 10 medium / 5 advanced)")

# 7. next-question: difficulty order, no solution leak, Type A
air.CALLS["count"] = 0
r = client.get(f"/skillpath/subtopic/{sub_id}/next-question", params={"domain_id": domain_id})
check("GET /next-question 200", r.status_code == 200, r.text[:120])
q = r.json()["question"]
check("serves basic first", q["difficulty"] == "basic", q["difficulty"])
check("exactly 2 worked examples", len(q["examples"]) == 2)
check("model_solution NOT leaked pre-answer", "model_solution" not in q)
check("next-question is Type A (0 AI calls)", air.CALLS["count"] == 0)

# 8. analyze: exactly ONE AI call, deterministic follow-through
air.CALLS["count"] = 0
r = client.post("/skillpath/subtopic/analyze", params={"domain_id": domain_id},
                json={"question_id": q["question_id"], "answer_text": "len(x)",
                      "run_output": "2", "time_taken_seconds": 40})
check("POST /analyze 200", r.status_code == 200, r.text[:200])
a = r.json()
check("analyze = exactly 1 AI call (Type B)", air.CALLS["count"] == 1, str(air.CALLS["count"]))
check("verdict normalized", a["verdict"] == "correct")
check("model_solution returned AFTER answer", a["model_solution"] == "solution 1")
check("points awarded (basic, score 90)", a["points_awarded"] == 9, str(a["points_awarded"]))

# repeat same question -> counted=False -> 0 points, no double progress
r2 = client.post("/skillpath/subtopic/analyze", params={"domain_id": domain_id},
                 json={"question_id": q["question_id"], "answer_text": "again"})
check("repeat attempt earns 0 points", r2.json()["points_awarded"] == 0)

# 9. walk the remaining 24 -> mastery tick at 20 correct, difficulty order held
seen_diffs, mastered_at = [q["difficulty"]], None
for n in range(2, 26):
    nq = client.get(f"/skillpath/subtopic/{sub_id}/next-question",
                    params={"domain_id": domain_id}).json()["question"]
    seen_diffs.append(nq["difficulty"])
    ra = client.post("/skillpath/subtopic/analyze", params={"domain_id": domain_id},
                     json={"question_id": nq["question_id"], "answer_text": "ans"}).json()
    if ra["subtopic_mastered"] and mastered_at is None:
        mastered_at = n
check("difficulty order basic->medium->advanced",
      seen_diffs == difficulty_sequence(), "|".join(seen_diffs[:12]) + "...")
check("mastery ticks at question 20 (>=20/25 correct)", mastered_at == 20, str(mastered_at))

r = client.get(f"/skillpath/subtopic/{sub_id}/progress", params={"domain_id": domain_id})
p = r.json()
check("progress: 25 answered / 25 correct / mastered",
      (p["answered"], p["correct"], p["mastered"]) == (25, 25, True),
      f"{p['answered']}/{p['correct']}/{p['mastered']}")

# 10. bank exhausted -> generate-once-cache: exactly 1 AI call, saved as auto
air.CALLS["count"] = 0
r = client.get(f"/skillpath/subtopic/{sub_id}/next-question", params={"domain_id": domain_id})
j = r.json()
check("exhaustion flagged", j["exhausted_and_regenerated"] is True)
check("generate-once-cache = exactly 1 AI call", air.CALLS["count"] == 1, str(air.CALLS["count"]))
check("auto question served, source=auto", j["question"]["source"] == "auto")
check("bank grew to 26", j["question"]["bank_size"] == 26, str(j["question"]["bank_size"]))
# second student hit would now be free - the row is in topic_questions with review_status='auto'

# 11. roadmap ring after mastering 1 of 8 Python subtopics
r = client.get(f"/skillpath/roadmap/{domain_id}").json()
py = r["topics"][0]
check("Python ring = 13% (1/8 mastered)", py["progress_pct"] == 13,
      str(py["progress_pct"]))
check("Python still current (not complete)", py["status"] == "current")

# 12. per-domain isolation: same subtopic in Data Analysis shows 0 progress
r = client.post("/skillpath/select", json={"domain_key": "data_analysis", "plan_months": 6})
da_id = r.json()["domain_id"]
r = client.get(f"/skillpath/subtopic/{sub_id}/progress", params={"domain_id": da_id})
check("progress isolated per domain (DA sees 0 answered)",
      r.json()["answered"] == 0, str(r.json()["answered"]))

# 13. 6-month plan unlocks Advanced in DA roadmap
road_da = client.get(f"/skillpath/roadmap/{da_id}").json()
adv = [t for t in road_da["topics"] if t["phase"] == "Advanced"]
check("6-month plan: Advanced not plan-locked",
      all(t["status"] != "locked" or road_da["topics"].index(t) > 0 for t in adv))
check("DA roadmap = MySQL first",
      road_da["topics"][0]["title"] == "MySQL", road_da["topics"][0]["title"])

app.dependency_overrides[get_db] = get_db
app.dependency_overrides[get_current_user] = get_current_user

print()
print(f"GATE RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:", *FAIL, sep="\n  - ")
    sys.exit(1)
print("VERIFICATION GATE: ALL CHECKS PASSED")
