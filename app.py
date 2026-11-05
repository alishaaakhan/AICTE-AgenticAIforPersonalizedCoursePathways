"""
app.py
───────
Flask web server for LearnMate.
Exposes a REST/JSON API consumed by the frontend SPA.

Endpoints:
  POST /api/session/start        – onboard or resume a student
  POST /api/chat                 – send a message, get AI reply
  GET  /api/roadmap              – fetch current roadmap
  POST /api/roadmap/regenerate   – regenerate roadmap
  GET  /api/progress             – fetch progress report
  POST /api/course/start         – mark course as started
  POST /api/course/complete      – mark course as completed
  POST /api/assess               – run skill assessment (single Q&A turn)
  GET  /api/domains              – list available domains
  GET  /api/profiles             – list all saved profiles

Run:
  python app.py
  → http://localhost:5000
"""

from __future__ import annotations

import os
import traceback

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from learnmate.agents.coach_agent import COACH_SYSTEM_PROMPT
from learnmate.course_catalog import get_all_domains
from learnmate.granite_client import GraniteClient
from learnmate.progress_tracker import build_progress_report
from learnmate.roadmap_generator import RoadmapGenerator
from learnmate.student_profile import DOMAINS, SKILL_LEVELS, ProfileManager, StudentProfile

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "learnmate-secret-2024")

# ── Singletons ────────────────────────────────────────────────────────────────
pm = ProfileManager()

try:
    llm = GraniteClient()
    llm_available = True
except EnvironmentError:
    llm = None
    llm_available = False

roadmap_gen = RoadmapGenerator(granite_client=llm)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _profile_to_dict(p: StudentProfile) -> dict:
    return {
        "student_id": p.student_id,
        "name": p.name,
        "email": p.email,
        "primary_domain": p.primary_domain,
        "skill_level": p.skill_level,
        "long_term_goal": p.long_term_goal,
        "weekly_hours": p.weekly_hours,
        "preferred_style": p.preferred_style,
        "session_count": p.session_count,
        "completed_count": len(p.completed_courses),
        "in_progress_count": len(p.in_progress_courses),
        "roadmap_phases": len(p.roadmap),
    }


def _err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", llm_available=llm_available)


# --------------------------------------------------------------------------
# Session
# --------------------------------------------------------------------------

@app.route("/api/session/start", methods=["POST"])
def session_start():
    """
    Body: { name, domain, skill_level, goal, weekly_hours, preferred_style }
    Returns the student profile dict + whether roadmap was built.
    """
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return _err("name is required")

    profile = pm.find_by_name(name)
    is_new = profile is None

    if is_new:
        domain        = data.get("domain", DOMAINS[0])
        skill_level   = data.get("skill_level", "beginner")
        goal          = data.get("goal", "Become a professional")
        weekly_hours  = int(data.get("weekly_hours", 5))
        preferred_style = data.get("preferred_style", "mixed")

        profile = pm.create_profile(name=name)
        profile.primary_domain   = domain
        profile.skill_level      = skill_level
        profile.long_term_goal   = goal
        profile.weekly_hours     = weekly_hours
        profile.preferred_style  = preferred_style
        pm.save_profile(profile)

    profile.session_count += 1
    pm.save_profile(profile)

    # Build roadmap if missing
    roadmap_built = False
    if not profile.roadmap and profile.primary_domain:
        try:
            profile.roadmap = roadmap_gen.generate_roadmap(profile)
            pm.save_profile(profile)
            roadmap_built = True
        except Exception:
            pass

    return jsonify({
        "profile": _profile_to_dict(profile),
        "is_new": is_new,
        "roadmap_built": roadmap_built,
        "llm_available": llm_available,
    })


# --------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Body: { student_id, message }
    Returns: { reply }
    """
    data = request.get_json(force=True)
    sid  = data.get("student_id", "")
    msg  = (data.get("message") or "").strip()

    if not sid or not msg:
        return _err("student_id and message are required")

    profile = pm.load_profile(sid)
    if not profile:
        return _err("Profile not found", 404)

    if not llm_available:
        reply = (
            "IBM Granite is not configured yet. "
            "Please add your IBM_API_KEY and WATSONX_PROJECT_ID to the .env file. "
            "In the meantime, use the Roadmap and Progress tabs!"
        )
    else:
        pm.add_conversation_turn(profile, "user", msg)
        try:
            reply = llm.generate_with_history(
                profile.conversation_history,
                system_prompt=COACH_SYSTEM_PROMPT,
            )
        except Exception as exc:
            reply = f"I had trouble reaching IBM Granite: {exc}. Please try again."
        pm.add_conversation_turn(profile, "assistant", reply)

    return jsonify({"reply": reply})


# --------------------------------------------------------------------------
# Roadmap
# --------------------------------------------------------------------------

@app.route("/api/roadmap", methods=["GET"])
def get_roadmap():
    sid = request.args.get("student_id", "")
    if not sid:
        return _err("student_id is required")
    profile = pm.load_profile(sid)
    if not profile:
        return _err("Profile not found", 404)
    return jsonify({"roadmap": profile.roadmap})


@app.route("/api/roadmap/regenerate", methods=["POST"])
def regenerate_roadmap():
    data = request.get_json(force=True)
    sid  = data.get("student_id", "")
    if not sid:
        return _err("student_id is required")
    profile = pm.load_profile(sid)
    if not profile:
        return _err("Profile not found", 404)
    try:
        profile.roadmap = roadmap_gen.adapt_roadmap(profile)
        pm.save_profile(profile)
    except Exception as exc:
        return _err(str(exc), 500)
    return jsonify({"roadmap": profile.roadmap})


# --------------------------------------------------------------------------
# Progress
# --------------------------------------------------------------------------

@app.route("/api/progress", methods=["GET"])
def get_progress():
    sid = request.args.get("student_id", "")
    if not sid:
        return _err("student_id is required")
    profile = pm.load_profile(sid)
    if not profile:
        return _err("Profile not found", 404)
    report = build_progress_report(profile)
    return jsonify({
        "report": report,
        "completed_courses": [c.model_dump() for c in profile.completed_courses],
        "in_progress_courses": [c.model_dump() for c in profile.in_progress_courses],
    })


# --------------------------------------------------------------------------
# Course actions
# --------------------------------------------------------------------------

@app.route("/api/course/start", methods=["POST"])
def start_course():
    data   = request.get_json(force=True)
    sid    = data.get("student_id", "")
    course = data.get("course")          # full course dict from roadmap
    if not sid or not course:
        return _err("student_id and course are required")
    profile = pm.load_profile(sid)
    if not profile:
        return _err("Profile not found", 404)
    pm.mark_course_started(profile, course)
    return jsonify({"ok": True})


@app.route("/api/course/complete", methods=["POST"])
def complete_course():
    data      = request.get_json(force=True)
    sid       = data.get("student_id", "")
    course_id = data.get("course_id", "")
    rating    = data.get("rating")
    notes     = data.get("notes", "")
    if not sid or not course_id:
        return _err("student_id and course_id are required")
    profile = pm.load_profile(sid)
    if not profile:
        return _err("Profile not found", 404)
    ok = pm.mark_course_completed(profile, course_id, rating=rating, notes=notes)
    return jsonify({"ok": ok})


# --------------------------------------------------------------------------
# Skill assessment (single turn)
# --------------------------------------------------------------------------

@app.route("/api/assess", methods=["POST"])
def assess():
    """
    Body: { student_id, answer?, question? }
    First call (no answer): returns a question.
    Subsequent calls (with answer): returns score + feedback.
    """
    data   = request.get_json(force=True)
    sid    = data.get("student_id", "")
    answer = data.get("answer", "")
    question = data.get("question", "")

    profile = pm.load_profile(sid)
    if not profile:
        return _err("Profile not found", 404)

    if not llm_available:
        return jsonify({"question": None, "feedback": "IBM Granite not configured.", "score": None})

    if not answer:
        # Generate a new question
        prompt = (
            f"Generate ONE short skill-assessment question for a "
            f"{profile.skill_level} student learning {profile.primary_domain}. "
            "Output only the question, nothing else."
        )
        q = llm.generate(prompt, max_new_tokens=100)
        return jsonify({"question": q.strip(), "feedback": None, "score": None})
    else:
        # Evaluate the answer
        eval_prompt = (
            f"Question: {question}\n"
            f"Student answer: {answer}\n\n"
            f"Rate this answer 1-10 for a {profile.skill_level} {profile.primary_domain} student. "
            "Respond with exactly: score: X | feedback: <one sentence>"
        )
        raw = llm.generate(eval_prompt, max_new_tokens=120)
        import re
        score_m = re.search(r"score[:\s]+(\d+)", raw, re.IGNORECASE)
        feed_m  = re.search(r"feedback[:\s]+(.+)", raw, re.IGNORECASE)
        score    = int(score_m.group(1)) if score_m else None
        feedback = feed_m.group(1).strip() if feed_m else raw.strip()
        if score:
            pm.update_skill_assessment(profile, profile.primary_domain, score)
        return jsonify({"question": None, "feedback": feedback, "score": score})


# --------------------------------------------------------------------------
# Meta
# --------------------------------------------------------------------------

@app.route("/api/domains", methods=["GET"])
def list_domains():
    return jsonify({"domains": DOMAINS, "skill_levels": SKILL_LEVELS})


@app.route("/api/profiles", methods=["GET"])
def list_profiles():
    profiles = pm.list_profiles()
    return jsonify({"profiles": [_profile_to_dict(p) for p in profiles]})


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n  LearnMate running → http://localhost:{port}\n")
    app.run(debug=True, port=port)
