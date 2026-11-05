"""
learnmate/roadmap_generator.py
───────────────────────────────
Uses IBM Granite (via GraniteClient) to generate and adapt a personalized
learning roadmap for a student, and provides a fallback rule-based roadmap
when the LLM is unavailable.
"""

from __future__ import annotations

import json
import re
from typing import Any

from learnmate.course_catalog import (
    COURSE_CATALOG,
    get_courses_by_domain,
    get_courses_by_level,
)
from learnmate.student_profile import SKILL_LEVELS, StudentProfile


# ──────────────────────────────────────────────────────────────────────────────
# Prompt templates
# ──────────────────────────────────────────────────────────────────────────────

_ROADMAP_SYSTEM = """\
You are LearnMate, an expert AI learning coach. Your job is to create a
personalized, step-by-step course roadmap for students based on their
profile. Always respond with a valid JSON array of roadmap phase objects.
Do NOT add any text before or after the JSON.
"""

_ROADMAP_USER_TEMPLATE = """\
Create a personalized learning roadmap for the following student profile.

Student Profile:
- Name: {name}
- Primary Domain: {primary_domain}
- Current Skill Level: {skill_level}
- Long-Term Goal: {goal}
- Hours per week available: {weekly_hours}
- Preferred Learning Style: {preferred_style}
- Current skills: {skill_map}

Available courses in the catalog for this domain:
{catalog_summary}

Rules:
1. Return ONLY a JSON array (no markdown, no prose).
2. Each element is a phase object with these keys:
   - "phase": integer (1, 2, 3 …)
   - "phase_title": short descriptive title string
   - "duration_weeks": estimated weeks for this phase
   - "courses": array of course objects, each with:
       * "id"            – course id from the catalog
       * "title"         – course title
       * "domain"        – domain string
       * "level"         – beginner | intermediate | advanced
       * "duration_weeks"
       * "skills_taught" – array of strings
       * "url"           – resource URL
       * "provider"      – provider name
       * "why"           – one-sentence reason this course suits the student
3. Sequence from the student's current level to their goal.
4. Respect prerequisites – never recommend a course before its prerequisites.
5. Fit pacing to {weekly_hours} hours/week (a 5-hr/wk student should not have
   more than 2 simultaneous courses).
"""

_ADAPT_USER_TEMPLATE = """\
A student's roadmap needs to be adapted based on recent progress.

Student: {name}
Completed courses: {completed}
In-progress courses: {in_progress}
Current skill level: {skill_level}
Updated goal: {goal}

Current roadmap (phases not yet completed):
{remaining_roadmap}

Available additional courses:
{catalog_summary}

Rules:
1. Return ONLY a JSON array of updated remaining phases.
2. Same schema as before.
3. Remove already-completed courses.
4. If the student is ahead, suggest more advanced material.
5. If the student is struggling (repeated same level), add bridging resources.
"""


# ──────────────────────────────────────────────────────────────────────────────
# RoadmapGenerator
# ──────────────────────────────────────────────────────────────────────────────

class RoadmapGenerator:
    """
    Generates and adapts personalized learning roadmaps.

    Falls back to a rule-based roadmap if IBM Granite is unavailable.
    """

    def __init__(self, granite_client=None) -> None:
        """
        Args:
            granite_client: An instance of GraniteClient (optional).
                            Pass None to use rule-based fallback only.
        """
        self._llm = granite_client

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------

    def generate_roadmap(self, profile: StudentProfile) -> list[dict[str, Any]]:
        """
        Generate a personalized roadmap for a student.

        Returns:
            List of phase dicts, each containing course recommendations.
        """
        if self._llm:
            try:
                return self._generate_with_llm(profile)
            except Exception as exc:
                print(f"[LLM roadmap generation failed: {exc}. Using rule-based fallback.]")
        return self._generate_rule_based(profile)

    def adapt_roadmap(self, profile: StudentProfile) -> list[dict[str, Any]]:
        """
        Adapt an existing roadmap based on the student's current progress.

        Returns:
            Updated list of remaining phase dicts.
        """
        if self._llm:
            try:
                return self._adapt_with_llm(profile)
            except Exception as exc:
                print(f"[LLM roadmap adaptation failed: {exc}. Using rule-based fallback.]")
        return self._generate_rule_based(profile)

    # --------------------------------------------------------------------------
    # LLM-based roadmap generation
    # --------------------------------------------------------------------------

    def _generate_with_llm(self, profile: StudentProfile) -> list[dict]:
        catalog = get_courses_by_domain(profile.primary_domain)
        catalog_summary = self._catalog_to_text(catalog)

        user_msg = _ROADMAP_USER_TEMPLATE.format(
            name=profile.name,
            primary_domain=profile.primary_domain,
            skill_level=profile.skill_level,
            goal=profile.long_term_goal or "Become a professional in this field",
            weekly_hours=profile.weekly_hours,
            preferred_style=profile.preferred_style,
            skill_map=json.dumps(profile.skill_map),
            catalog_summary=catalog_summary,
        )

        messages = [{"role": "user", "content": user_msg}]
        raw = self._llm.generate_with_history(messages, system_prompt=_ROADMAP_SYSTEM)
        return self._parse_json_response(raw)

    def _adapt_with_llm(self, profile: StudentProfile) -> list[dict]:
        completed_titles = [c.course_title for c in profile.completed_courses]
        in_progress_titles = [c.course_title for c in profile.in_progress_courses]
        remaining = [
            phase for phase in profile.roadmap
            if not all(
                any(c.get("title") == ct for ct in completed_titles)
                for c in phase.get("courses", [])
            )
        ]
        catalog = get_courses_by_domain(profile.primary_domain)
        catalog_summary = self._catalog_to_text(catalog)

        user_msg = _ADAPT_USER_TEMPLATE.format(
            name=profile.name,
            completed=", ".join(completed_titles) or "None yet",
            in_progress=", ".join(in_progress_titles) or "None",
            skill_level=profile.skill_level,
            goal=profile.long_term_goal or "Become a professional",
            remaining_roadmap=json.dumps(remaining, indent=2),
            catalog_summary=catalog_summary,
        )

        messages = [{"role": "user", "content": user_msg}]
        raw = self._llm.generate_with_history(messages, system_prompt=_ROADMAP_SYSTEM)
        return self._parse_json_response(raw)

    # --------------------------------------------------------------------------
    # Rule-based fallback roadmap
    # --------------------------------------------------------------------------

    def _generate_rule_based(self, profile: StudentProfile) -> list[dict]:
        """
        Simple level-progression roadmap:
        Phase 1 = beginner courses → Phase 2 = intermediate → Phase 3 = advanced
        Only includes courses for the primary domain.
        """
        domain = profile.primary_domain
        current_level_idx = SKILL_LEVELS.index(profile.skill_level)
        phases: list[dict] = []
        phase_num = 1

        for level in SKILL_LEVELS[current_level_idx:]:
            courses = get_courses_by_level(domain, level)
            if not courses:
                continue
            # Limit to 3 courses per phase
            courses = courses[:3]
            for c in courses:
                c["why"] = f"This course builds {level}-level skills in {domain}."
            phases.append(
                {
                    "phase": phase_num,
                    "phase_title": f"{level.capitalize()} – {domain}",
                    "duration_weeks": sum(c["duration_weeks"] for c in courses),
                    "courses": courses,
                }
            )
            phase_num += 1

        return phases

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------

    @staticmethod
    def _catalog_to_text(catalog: list[dict]) -> str:
        lines = []
        for c in catalog:
            prereqs = ", ".join(c.get("prerequisites", [])) or "None"
            skills = ", ".join(c.get("skills_taught", []))
            lines.append(
                f"[{c['id']}] {c['title']} | Level: {c['level']} | "
                f"Weeks: {c['duration_weeks']} | Skills: {skills} | "
                f"Prerequisites: {prereqs} | URL: {c['url']}"
            )
        return "\n".join(lines)

    @staticmethod
    def _parse_json_response(raw: str) -> list[dict]:
        """
        Extract a JSON array from raw LLM output.
        Handles markdown code fences and stray prose.
        """
        # Strip markdown fences
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        # Find the outermost JSON array
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found in LLM response.")
        return json.loads(raw[start:end])
