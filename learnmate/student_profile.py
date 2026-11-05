"""
learnmate/student_profile.py
─────────────────────────────
Manages student profiles: creation, persistence (JSON files in ./data/),
skill assessment, and goal tracking.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Data models
# ──────────────────────────────────────────────────────────────────────────────

SKILL_LEVELS = ["beginner", "intermediate", "advanced"]

DOMAINS = [
    "Frontend Development",
    "Backend Development",
    "Full Stack Development",
    "Data Science & Machine Learning",
    "Cybersecurity",
    "UI/UX Design",
    "Mobile Development",
    "Cloud Computing",
    "DevOps & MLOps",
    "Blockchain",
    "Game Development",
    "Embedded Systems & IoT",
]


class CourseProgress(BaseModel):
    course_id: str
    course_title: str
    domain: str
    status: str = "not_started"   # not_started | in_progress | completed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    rating: Optional[int] = None  # 1–5 stars given by student
    notes: str = ""


class StudentProfile(BaseModel):
    student_id: str
    name: str
    email: str = ""
    age: Optional[int] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Learning preferences
    primary_domain: str = ""
    secondary_domains: list[str] = Field(default_factory=list)
    skill_level: str = "beginner"          # beginner | intermediate | advanced
    long_term_goal: str = ""
    weekly_hours: int = 5                  # hours per week the student can dedicate
    preferred_style: str = "video"         # video | text | project-based | mixed

    # Skill map: domain → self-assessed score 1-10
    skill_map: dict[str, int] = Field(default_factory=dict)

    # Roadmap & progress
    roadmap: list[dict[str, Any]] = Field(default_factory=list)
    completed_courses: list[CourseProgress] = Field(default_factory=list)
    in_progress_courses: list[CourseProgress] = Field(default_factory=list)

    # Conversation memory (last N turns stored for context)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    session_count: int = 0


# ──────────────────────────────────────────────────────────────────────────────
# ProfileManager
# ──────────────────────────────────────────────────────────────────────────────

class ProfileManager:
    """Handles create / load / save operations for StudentProfile objects."""

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------------------

    def create_profile(
        self,
        name: str,
        email: str = "",
        age: Optional[int] = None,
    ) -> StudentProfile:
        """Create a brand-new student profile and persist it."""
        student_id = self._generate_id(name)
        profile = StudentProfile(
            student_id=student_id,
            name=name,
            email=email,
            age=age,
        )
        self.save_profile(profile)
        return profile

    def load_profile(self, student_id: str) -> Optional[StudentProfile]:
        """Load a profile by student_id; returns None if not found."""
        path = self._profile_path(student_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return StudentProfile(**data)
        except Exception:
            return None

    def save_profile(self, profile: StudentProfile) -> None:
        """Persist a profile to disk as JSON."""
        profile.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._profile_path(profile.student_id)
        path.write_text(
            json.dumps(profile.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list_profiles(self) -> list[StudentProfile]:
        """Return all saved profiles."""
        profiles = []
        for p in self.data_dir.glob("profile_*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                profiles.append(StudentProfile(**data))
            except Exception:
                pass
        return profiles

    def find_by_name(self, name: str) -> Optional[StudentProfile]:
        """Find a profile by student name (case-insensitive)."""
        for p in self.list_profiles():
            if p.name.lower() == name.lower():
                return p
        return None

    # --------------------------------------------------------------------------
    # Profile updates
    # --------------------------------------------------------------------------

    def update_skill_assessment(
        self,
        profile: StudentProfile,
        domain: str,
        score: int,
    ) -> None:
        """Record/update a skill score (1–10) for a domain."""
        score = max(1, min(10, score))
        profile.skill_map[domain] = score
        self.save_profile(profile)

    def add_conversation_turn(
        self,
        profile: StudentProfile,
        role: str,
        content: str,
        max_history: int = 20,
    ) -> None:
        """Append a conversation turn and trim history to max_history turns."""
        profile.conversation_history.append({"role": role, "content": content})
        if len(profile.conversation_history) > max_history:
            profile.conversation_history = profile.conversation_history[-max_history:]
        self.save_profile(profile)

    def mark_course_started(
        self, profile: StudentProfile, course: dict[str, Any]
    ) -> None:
        cp = CourseProgress(
            course_id=course.get("id", ""),
            course_title=course.get("title", ""),
            domain=course.get("domain", ""),
            status="in_progress",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        # Avoid duplicates
        existing_ids = {c.course_id for c in profile.in_progress_courses}
        if cp.course_id not in existing_ids:
            profile.in_progress_courses.append(cp)
        self.save_profile(profile)

    def mark_course_completed(
        self,
        profile: StudentProfile,
        course_id: str,
        rating: Optional[int] = None,
        notes: str = "",
    ) -> bool:
        """Move a course from in_progress → completed. Returns True on success."""
        for i, cp in enumerate(profile.in_progress_courses):
            if cp.course_id == course_id:
                cp.status = "completed"
                cp.completed_at = datetime.now(timezone.utc).isoformat()
                cp.rating = rating
                cp.notes = notes
                profile.completed_courses.append(cp)
                profile.in_progress_courses.pop(i)
                self.save_profile(profile)
                return True
        return False

    # --------------------------------------------------------------------------
    # Private helpers
    # --------------------------------------------------------------------------

    @staticmethod
    def _generate_id(name: str) -> str:
        """Generate a deterministic-ish student ID from name + timestamp."""
        slug = re.sub(r"[^a-z0-9]", "_", name.lower())[:20]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"{slug}_{ts}"

    def _profile_path(self, student_id: str) -> Path:
        return self.data_dir / f"profile_{student_id}.json"
