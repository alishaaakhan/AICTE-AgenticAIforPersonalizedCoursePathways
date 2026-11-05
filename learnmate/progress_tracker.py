"""
learnmate/progress_tracker.py
──────────────────────────────
Generates progress reports and analytics for a student.
Used by the coach agent and can be called standalone.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from learnmate.student_profile import StudentProfile


def compute_completion_percentage(profile: StudentProfile) -> float:
    """
    Returns the percentage of roadmap courses the student has completed.
    """
    total_courses = sum(
        len(phase.get("courses", [])) for phase in profile.roadmap
    )
    if total_courses == 0:
        return 0.0
    completed = len(profile.completed_courses)
    return round((completed / total_courses) * 100, 1)


def compute_total_weeks_remaining(profile: StudentProfile) -> int:
    """
    Estimates remaining weeks based on not-yet-completed courses
    and the student's weekly availability.
    """
    completed_ids = {c.course_id for c in profile.completed_courses}
    in_progress_ids = {c.course_id for c in profile.in_progress_courses}

    remaining_weeks = 0
    for phase in profile.roadmap:
        for course in phase.get("courses", []):
            cid = course.get("id", "")
            if cid not in completed_ids:
                remaining_weeks += course.get("duration_weeks", 0)

    # Adjust for weekly hours (baseline = 10 hrs/week)
    if profile.weekly_hours and profile.weekly_hours < 10:
        factor = 10 / profile.weekly_hours
        remaining_weeks = int(remaining_weeks * factor)

    return remaining_weeks


def get_next_recommended_course(profile: StudentProfile) -> dict[str, Any] | None:
    """
    Returns the next course the student should focus on,
    taking into account completed and in-progress courses.
    """
    completed_ids = {c.course_id for c in profile.completed_courses}
    in_progress_ids = {c.course_id for c in profile.in_progress_courses}

    for phase in profile.roadmap:
        for course in phase.get("courses", []):
            cid = course.get("id", "")
            if cid not in completed_ids and cid not in in_progress_ids:
                return course
    return None


def get_skill_growth_summary(profile: StudentProfile) -> str:
    """
    Returns a human-readable string summarising the student's skill map.
    """
    if not profile.skill_map:
        return "No skill assessments recorded yet."
    lines = [f"  • {domain}: {score}/10" for domain, score in profile.skill_map.items()]
    return "\n".join(lines)


def build_progress_report(profile: StudentProfile) -> dict[str, Any]:
    """
    Returns a structured progress report dict suitable for display or storage.
    """
    pct = compute_completion_percentage(profile)
    weeks_left = compute_total_weeks_remaining(profile)
    next_course = get_next_recommended_course(profile)
    skills = get_skill_growth_summary(profile)

    # Estimate completion date
    if weeks_left > 0:
        from datetime import timedelta
        eta = (datetime.now(timezone.utc) + timedelta(weeks=weeks_left)).strftime("%B %Y")
    else:
        eta = "Goal reached! 🎉"

    return {
        "student_name": profile.name,
        "primary_domain": profile.primary_domain,
        "skill_level": profile.skill_level,
        "long_term_goal": profile.long_term_goal,
        "sessions_attended": profile.session_count,
        "completion_percentage": pct,
        "completed_courses": len(profile.completed_courses),
        "in_progress_courses": len(profile.in_progress_courses),
        "total_roadmap_courses": sum(len(p.get("courses", [])) for p in profile.roadmap),
        "weeks_remaining": weeks_left,
        "estimated_completion": eta,
        "next_recommended_course": next_course.get("title") if next_course else "—",
        "next_course_url": next_course.get("url") if next_course else "—",
        "skill_map_summary": skills,
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
    }
