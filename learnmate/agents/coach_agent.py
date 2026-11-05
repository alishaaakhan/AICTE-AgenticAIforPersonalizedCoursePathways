"""
learnmate/agents/coach_agent.py
────────────────────────────────
The LearnMate Coach Agent – the core agentic loop that:
  1. Onboards new students (collects name, domain, skill level, goals)
  2. Builds/displays a personalized roadmap via IBM Granite
  3. Conducts an AI skill-assessment quiz
  4. Tracks progress (mark courses started / completed)
  5. Adapts the roadmap based on progress
  6. Answers free-form learning questions using IBM Granite

The agent maintains full multi-turn conversation history (stored in the
student profile) so context is preserved across sessions.
"""

from __future__ import annotations

import json
import textwrap
from typing import Any, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich import box

from learnmate.course_catalog import get_course_by_id
from learnmate.granite_client import GraniteClient
from learnmate.roadmap_generator import RoadmapGenerator
from learnmate.student_profile import DOMAINS, SKILL_LEVELS, ProfileManager, StudentProfile

console = Console()

# ──────────────────────────────────────────────────────────────────────────────
# System prompt for the coach persona
# ──────────────────────────────────────────────────────────────────────────────

COACH_SYSTEM_PROMPT = """\
You are LearnMate, an expert and encouraging AI learning coach powered by
IBM Granite. Your personality is warm, clear, and motivating.

Your responsibilities:
1. Help students discover the right learning path for their goals.
2. Ask smart, empathetic questions to understand skill levels.
3. Explain course choices and roadmap phases clearly.
4. Answer technical questions concisely, with examples when helpful.
5. Celebrate progress and adapt plans when students struggle.

Guidelines:
- Keep responses concise (under 200 words unless asked for detail).
- Use bullet points for lists.
- Never make up course URLs – only reference the catalog.
- If a student asks something outside learning/tech, gently redirect.
"""


# ──────────────────────────────────────────────────────────────────────────────
# CoachAgent
# ──────────────────────────────────────────────────────────────────────────────

class CoachAgent:
    """
    Orchestrates the full agentic coaching experience.
    """

    INTENTS = {
        "show_roadmap": ["show roadmap", "my roadmap", "view roadmap", "show my plan", "learning plan"],
        "update_progress": ["completed", "finished", "done with", "i finished", "mark as done"],
        "start_course": ["start", "begin", "i'm starting", "starting"],
        "adapt_roadmap": ["adapt", "update roadmap", "change plan", "refresh roadmap", "regenerate"],
        "show_progress": ["my progress", "how am i doing", "progress", "stats", "dashboard"],
        "assess_skills": ["assess", "quiz me", "test my skills", "skill check"],
        "help": ["help", "what can you do", "commands", "options"],
        "quit": ["quit", "exit", "bye", "goodbye"],
    }

    def __init__(self) -> None:
        self.profile_manager = ProfileManager()
        self.profile: Optional[StudentProfile] = None

        # Try to initialise IBM Granite; fall back gracefully
        try:
            self.llm = GraniteClient()
            self.llm_available = True
        except EnvironmentError as e:
            console.print(
                Panel(
                    f"[yellow]⚠  IBM Granite not configured:[/yellow]\n{e}\n\n"
                    "[dim]LearnMate will run with rule-based roadmaps until credentials are set.[/dim]",
                    title="Configuration Notice",
                    border_style="yellow",
                )
            )
            self.llm = None
            self.llm_available = False

        self.roadmap_gen = RoadmapGenerator(granite_client=self.llm)

    # --------------------------------------------------------------------------
    # Entry point
    # --------------------------------------------------------------------------

    def run(self) -> None:
        """Start the LearnMate coaching session."""
        self._print_banner()
        self.profile = self._get_or_create_profile()
        self.profile.session_count += 1
        self.profile_manager.save_profile(self.profile)

        # Generate roadmap if none exists
        if not self.profile.roadmap and self.profile.primary_domain:
            self._build_roadmap()

        # Main conversation loop
        self._greet_returning_student()
        self._conversation_loop()

    # --------------------------------------------------------------------------
    # Onboarding
    # --------------------------------------------------------------------------

    def _get_or_create_profile(self) -> StudentProfile:
        console.print("\n[bold cyan]What's your name?[/bold cyan] ", end="")
        name = input().strip()
        if not name:
            name = "Student"

        existing = self.profile_manager.find_by_name(name)
        if existing:
            console.print(
                f"\n[green]Welcome back, {existing.name}![/green] "
                f"(Session #{existing.session_count + 1})"
            )
            return existing

        console.print(f"\n[green]Nice to meet you, {name}![/green] Let's set up your learning profile.\n")
        return self._onboard_new_student(name)

    def _onboard_new_student(self, name: str) -> StudentProfile:
        # Domain selection
        console.print("[bold]Choose your primary domain of interest:[/bold]")
        for i, d in enumerate(DOMAINS, 1):
            console.print(f"  [cyan]{i:2}.[/cyan] {d}")
        console.print("\nEnter the number or type the domain name: ", end="")
        domain_input = input().strip()
        primary_domain = self._resolve_domain(domain_input)

        # Skill level
        console.print("\n[bold]What is your current skill level in this domain?[/bold]")
        for i, lvl in enumerate(SKILL_LEVELS, 1):
            console.print(f"  [cyan]{i}.[/cyan] {lvl.capitalize()}")
        console.print("Enter 1, 2, or 3: ", end="")
        level_input = input().strip()
        skill_level = self._resolve_level(level_input)

        # Goal
        console.print("\n[bold]What is your long-term goal? (e.g. 'Get a frontend dev job')[/bold] ", end="")
        goal = input().strip() or "Become a professional in this domain"

        # Weekly hours
        console.print("\n[bold]How many hours per week can you dedicate to learning?[/bold] ", end="")
        try:
            weekly_hours = int(input().strip())
        except ValueError:
            weekly_hours = 5

        # Learning style
        console.print("\n[bold]Preferred learning style?[/bold]")
        styles = ["video", "text", "project-based", "mixed"]
        for i, s in enumerate(styles, 1):
            console.print(f"  [cyan]{i}.[/cyan] {s}")
        console.print("Enter 1-4: ", end="")
        try:
            style_idx = int(input().strip()) - 1
            preferred_style = styles[style_idx] if 0 <= style_idx < len(styles) else "mixed"
        except (ValueError, IndexError):
            preferred_style = "mixed"

        profile = self.profile_manager.create_profile(name=name)
        profile.primary_domain = primary_domain
        profile.skill_level = skill_level
        profile.long_term_goal = goal
        profile.weekly_hours = weekly_hours
        profile.preferred_style = preferred_style
        self.profile_manager.save_profile(profile)
        return profile

    # --------------------------------------------------------------------------
    # Roadmap
    # --------------------------------------------------------------------------

    def _build_roadmap(self) -> None:
        console.print(
            f"\n[dim]🤖 Building your personalized roadmap using IBM Granite…[/dim]"
            if self.llm_available
            else "\n[dim]📋 Building your roadmap (rule-based mode)…[/dim]"
        )
        try:
            roadmap = self.roadmap_gen.generate_roadmap(self.profile)
            self.profile.roadmap = roadmap
            self.profile_manager.save_profile(self.profile)
            console.print("[green]✓ Roadmap ready![/green]\n")
        except Exception as exc:
            console.print(f"[red]Roadmap generation failed: {exc}[/red]")

    def _show_roadmap(self) -> None:
        if not self.profile.roadmap:
            console.print("[yellow]No roadmap yet. Type 'adapt roadmap' to generate one.[/yellow]")
            return

        console.print(
            Panel(
                f"[bold]Personalized Roadmap for {self.profile.name}[/bold]\n"
                f"Domain: {self.profile.primary_domain} | Goal: {self.profile.long_term_goal}",
                border_style="cyan",
            )
        )
        for phase in self.profile.roadmap:
            table = Table(
                title=f"Phase {phase['phase']}: {phase['phase_title']}  "
                      f"(~{phase.get('duration_weeks', '?')} weeks)",
                box=box.ROUNDED,
                show_lines=True,
                title_style="bold magenta",
            )
            table.add_column("Course", style="bold white", no_wrap=False, min_width=28)
            table.add_column("Level", style="cyan", width=14)
            table.add_column("Weeks", justify="center", width=6)
            table.add_column("Why", no_wrap=False, min_width=30)
            table.add_column("URL", style="blue", no_wrap=False)

            for c in phase.get("courses", []):
                table.add_row(
                    c.get("title", ""),
                    c.get("level", ""),
                    str(c.get("duration_weeks", "?")),
                    c.get("why", ""),
                    c.get("url", ""),
                )
            console.print(table)

    # --------------------------------------------------------------------------
    # Progress tracking
    # --------------------------------------------------------------------------

    def _show_progress(self) -> None:
        p = self.profile
        completed = len(p.completed_courses)
        in_prog = len(p.in_progress_courses)
        total = sum(
            len(phase.get("courses", [])) for phase in p.roadmap
        )
        console.print(
            Panel(
                f"[bold]{p.name}'s Progress[/bold]\n\n"
                f"✅ Completed courses : [green]{completed}[/green]\n"
                f"📖 In progress       : [yellow]{in_prog}[/yellow]\n"
                f"📋 Total in roadmap  : {total}\n"
                f"🎯 Goal              : {p.long_term_goal}\n"
                f"🗓  Sessions attended : {p.session_count}",
                border_style="green",
            )
        )
        if p.completed_courses:
            console.print("[bold]Completed courses:[/bold]")
            for c in p.completed_courses:
                stars = "⭐" * (c.rating or 0)
                console.print(f"  ✅ {c.course_title}  {stars}")

        if p.in_progress_courses:
            console.print("[bold]In-progress:[/bold]")
            for c in p.in_progress_courses:
                console.print(f"  📖 {c.course_title}")

    def _handle_update_progress(self, user_input: str) -> None:
        if not self.profile.in_progress_courses:
            console.print("[yellow]You have no in-progress courses. Start a course first![/yellow]")
            return

        console.print("[bold]Which course did you complete?[/bold]")
        for i, c in enumerate(self.profile.in_progress_courses, 1):
            console.print(f"  {i}. {c.course_title}")
        console.print("Enter number: ", end="")
        try:
            idx = int(input().strip()) - 1
            course = self.profile.in_progress_courses[idx]
        except (ValueError, IndexError):
            console.print("[red]Invalid selection.[/red]")
            return

        console.print("Rate the course (1-5 stars): ", end="")
        try:
            rating = int(input().strip())
        except ValueError:
            rating = None

        self.profile_manager.mark_course_completed(
            self.profile, course.course_id, rating=rating
        )
        console.print(f"[green]✅ Marked '{course.course_title}' as completed! Great work![/green]")

        # Ask if roadmap should be adapted
        console.print(
            "\n[dim]Would you like me to adapt your roadmap based on this progress? (y/n)[/dim] ", end=""
        )
        if input().strip().lower().startswith("y"):
            self._adapt_roadmap()

    def _handle_start_course(self, user_input: str) -> None:
        if not self.profile.roadmap:
            console.print("[yellow]No roadmap yet. Ask for 'show roadmap' first.[/yellow]")
            return

        # Collect all courses from roadmap into a flat list
        all_courses: list[dict] = []
        for phase in self.profile.roadmap:
            all_courses.extend(phase.get("courses", []))

        if not all_courses:
            console.print("[yellow]No courses in roadmap.[/yellow]")
            return

        completed_ids = {c.course_id for c in self.profile.completed_courses}
        in_prog_ids = {c.course_id for c in self.profile.in_progress_courses}
        available = [
            c for c in all_courses
            if c.get("id") not in completed_ids and c.get("id") not in in_prog_ids
        ]

        if not available:
            console.print("[green]All roadmap courses are in progress or completed! 🎉[/green]")
            return

        console.print("[bold]Select a course to start:[/bold]")
        for i, c in enumerate(available[:10], 1):
            console.print(f"  {i}. [{c.get('level','?')}] {c.get('title','')}")
        console.print("Enter number: ", end="")
        try:
            idx = int(input().strip()) - 1
            course = available[idx]
        except (ValueError, IndexError):
            console.print("[red]Invalid selection.[/red]")
            return

        self.profile_manager.mark_course_started(self.profile, course)
        console.print(
            f"[green]📖 Started: '{course['title']}'[/green]\n"
            f"Resource: [blue]{course.get('url', 'N/A')}[/blue]"
        )

    def _adapt_roadmap(self) -> None:
        console.print(
            "\n[dim]🤖 Adapting your roadmap based on your progress…[/dim]"
            if self.llm_available
            else "\n[dim]📋 Adapting your roadmap (rule-based mode)…[/dim]"
        )
        try:
            updated = self.roadmap_gen.adapt_roadmap(self.profile)
            self.profile.roadmap = updated
            self.profile_manager.save_profile(self.profile)
            console.print("[green]✓ Roadmap adapted![/green]")
            self._show_roadmap()
        except Exception as exc:
            console.print(f"[red]Adaptation failed: {exc}[/red]")

    # --------------------------------------------------------------------------
    # Skill assessment quiz
    # --------------------------------------------------------------------------

    def _run_skill_assessment(self) -> None:
        if not self.llm_available:
            console.print("[yellow]Skill assessment requires IBM Granite. Please configure your .env file.[/yellow]")
            return

        domain = self.profile.primary_domain
        console.print(
            f"\n[bold cyan]Skill Assessment – {domain}[/bold cyan]\n"
            "[dim]I'll ask you 3 questions. Answer in your own words.[/dim]\n"
        )

        quiz_prompt = (
            f"Generate 3 short skill-assessment questions for a {self.profile.skill_level} "
            f"student learning {domain}. "
            "Format: numbered list, one question per line, no extra text."
        )
        questions_raw = self.llm.generate(quiz_prompt, max_new_tokens=300)
        questions = [
            q.strip()
            for q in questions_raw.split("\n")
            if q.strip() and q.strip()[0].isdigit()
        ][:3]

        total_score = 0
        for q in questions:
            console.print(f"\n[bold]{q}[/bold]")
            console.print("Your answer: ", end="")
            answer = input().strip()
            if not answer:
                continue

            eval_prompt = (
                f"Question: {q}\n"
                f"Student's answer: {answer}\n\n"
                f"Rate this answer on a scale of 1-10 for a {self.profile.skill_level} level "
                f"{domain} student. "
                "Respond with: score: X  (then a brief 1-sentence feedback)"
            )
            feedback_raw = self.llm.generate(eval_prompt, max_new_tokens=150)
            console.print(f"[green]{feedback_raw.strip()}[/green]")

            # Extract numeric score
            match = __import__("re").search(r"score[:\s]+(\d+)", feedback_raw, __import__("re").IGNORECASE)
            if match:
                total_score += int(match.group(1))

        avg = total_score // max(len(questions), 1)
        # Update skill map
        self.profile_manager.update_skill_assessment(self.profile, domain, avg)

        # Suggest level adjustment
        if avg >= 8:
            new_level = "advanced"
        elif avg >= 5:
            new_level = "intermediate"
        else:
            new_level = "beginner"

        if new_level != self.profile.skill_level:
            console.print(
                f"\n[bold]Based on your answers, I'm updating your skill level from "
                f"[yellow]{self.profile.skill_level}[/yellow] → "
                f"[green]{new_level}[/green].[/bold]"
            )
            self.profile.skill_level = new_level
            self.profile_manager.save_profile(self.profile)
            console.print("[dim]Regenerating your roadmap for the updated level…[/dim]")
            self._build_roadmap()

    # --------------------------------------------------------------------------
    # Free-form AI Q&A
    # --------------------------------------------------------------------------

    def _ask_granite(self, user_input: str) -> str:
        """Send a free-form question to IBM Granite with conversation context."""
        if not self.llm_available:
            return (
                "I can answer your questions more thoroughly once IBM Granite is configured. "
                "For now, try 'show roadmap', 'my progress', or 'help'."
            )

        self.profile_manager.add_conversation_turn(self.profile, "user", user_input)
        response = self.llm.generate_with_history(
            self.profile.conversation_history,
            system_prompt=COACH_SYSTEM_PROMPT,
        )
        self.profile_manager.add_conversation_turn(self.profile, "assistant", response)
        return response

    # --------------------------------------------------------------------------
    # Main conversation loop
    # --------------------------------------------------------------------------

    def _conversation_loop(self) -> None:
        self._print_help()
        while True:
            try:
                console.print("\n[bold cyan]You:[/bold cyan] ", end="")
                user_input = input().strip()
            except (EOFError, KeyboardInterrupt):
                self._farewell()
                break

            if not user_input:
                continue

            intent = self._detect_intent(user_input)

            if intent == "quit":
                self._farewell()
                break
            elif intent == "help":
                self._print_help()
            elif intent == "show_roadmap":
                self._show_roadmap()
            elif intent == "show_progress":
                self._show_progress()
            elif intent == "update_progress":
                self._handle_update_progress(user_input)
            elif intent == "start_course":
                self._handle_start_course(user_input)
            elif intent == "adapt_roadmap":
                self._adapt_roadmap()
            elif intent == "assess_skills":
                self._run_skill_assessment()
            else:
                # Free-form AI response via IBM Granite
                response = self._ask_granite(user_input)
                console.print(f"\n[bold green]LearnMate:[/bold green]")
                console.print(Markdown(response))

    # --------------------------------------------------------------------------
    # Intent detection
    # --------------------------------------------------------------------------

    def _detect_intent(self, text: str) -> str:
        text_lower = text.lower()
        for intent, keywords in self.INTENTS.items():
            if any(kw in text_lower for kw in keywords):
                return intent
        return "free_form"

    # --------------------------------------------------------------------------
    # Helpers / display
    # --------------------------------------------------------------------------

    def _greet_returning_student(self) -> None:
        p = self.profile
        if p.session_count > 1:
            completed = len(p.completed_courses)
            msg = (
                f"Welcome back, [bold]{p.name}[/bold]! "
                f"You've completed [green]{completed}[/green] course(s) so far. "
                f"Let's keep the momentum going! 🚀"
            )
        else:
            msg = (
                f"Welcome, [bold]{p.name}[/bold]! "
                f"Your learning journey in [cyan]{p.primary_domain}[/cyan] starts now. "
                f"Type [bold]'show roadmap'[/bold] to see your personalized plan."
            )
        console.print(Panel(msg, border_style="cyan", padding=(1, 2)))

    def _print_banner(self) -> None:
        console.print(
            Panel(
                "[bold cyan]LearnMate[/bold cyan]\n"
                "[dim]Agentic AI for Personalized Course Pathways[/dim]\n"
                "[dim]Powered by IBM Granite on IBM watsonx.ai[/dim]",
                border_style="bright_blue",
                padding=(1, 4),
            )
        )

    def _print_help(self) -> None:
        console.print(
            Panel(
                "[bold]Commands / Phrases:[/bold]\n\n"
                "  [cyan]show roadmap[/cyan]      – View your personalized learning roadmap\n"
                "  [cyan]start course[/cyan]      – Mark a roadmap course as started\n"
                "  [cyan]completed …[/cyan]       – Mark a course as completed\n"
                "  [cyan]my progress[/cyan]       – See your progress dashboard\n"
                "  [cyan]adapt roadmap[/cyan]     – Regenerate roadmap based on progress\n"
                "  [cyan]assess skills[/cyan]     – Take an AI-powered skill quiz\n"
                "  [cyan]help[/cyan]              – Show this menu\n"
                "  [cyan]quit[/cyan]              – Exit LearnMate\n\n"
                "[dim]Or just type any question – LearnMate will answer it![/dim]",
                title="What can I do?",
                border_style="bright_blue",
            )
        )

    def _farewell(self) -> None:
        console.print(
            Panel(
                f"[bold]See you next time, {self.profile.name}![/bold] "
                "Keep learning — every day counts. 🌱",
                border_style="green",
                padding=(1, 2),
            )
        )

    @staticmethod
    def _resolve_domain(raw: str) -> str:
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(DOMAINS):
                return DOMAINS[idx]
        except ValueError:
            pass
        raw_lower = raw.lower()
        for d in DOMAINS:
            if raw_lower in d.lower():
                return d
        return DOMAINS[0]

    @staticmethod
    def _resolve_level(raw: str) -> str:
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(SKILL_LEVELS):
                return SKILL_LEVELS[idx]
        except ValueError:
            pass
        raw_lower = raw.lower()
        for lvl in SKILL_LEVELS:
            if raw_lower in lvl:
                return lvl
        return "beginner"
