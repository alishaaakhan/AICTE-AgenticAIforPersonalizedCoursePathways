"""
main.py
────────
LearnMate – entry point.

Usage:
    python main.py              # start the interactive coaching session
    python main.py --report     # print a progress report for an existing student
    python main.py --list       # list all saved student profiles
"""

from __future__ import annotations

import sys

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def main() -> None:
    args = sys.argv[1:]

    if "--list" in args:
        _list_profiles()
        return

    if "--report" in args:
        _show_report()
        return

    # Default: start the interactive coaching agent
    from learnmate.agents.coach_agent import CoachAgent
    agent = CoachAgent()
    agent.run()


def _list_profiles() -> None:
    from learnmate.student_profile import ProfileManager
    pm = ProfileManager()
    profiles = pm.list_profiles()

    if not profiles:
        console.print("[yellow]No student profiles found.[/yellow]")
        return

    table = Table(title="Saved Student Profiles", box=box.ROUNDED)
    table.add_column("Name", style="bold white")
    table.add_column("Domain", style="cyan")
    table.add_column("Level", style="green")
    table.add_column("Sessions", justify="center")
    table.add_column("Completed", justify="center")
    table.add_column("Created", style="dim")

    for p in profiles:
        table.add_row(
            p.name,
            p.primary_domain or "—",
            p.skill_level,
            str(p.session_count),
            str(len(p.completed_courses)),
            p.created_at[:10],
        )
    console.print(table)


def _show_report() -> None:
    from learnmate.student_profile import ProfileManager
    from learnmate.progress_tracker import build_progress_report

    pm = ProfileManager()
    profiles = pm.list_profiles()

    if not profiles:
        console.print("[yellow]No student profiles found.[/yellow]")
        return

    if len(profiles) == 1:
        profile = profiles[0]
    else:
        console.print("[bold]Select a student:[/bold]")
        for i, p in enumerate(profiles, 1):
            console.print(f"  {i}. {p.name}")
        console.print("Enter number: ", end="")
        try:
            idx = int(input().strip()) - 1
            profile = profiles[idx]
        except (ValueError, IndexError):
            console.print("[red]Invalid selection.[/red]")
            return

    report = build_progress_report(profile)

    from rich.panel import Panel
    console.print(
        Panel(
            "\n".join(
                f"[bold]{k.replace('_', ' ').title()}:[/bold]  {v}"
                for k, v in report.items()
            ),
            title=f"Progress Report – {report['student_name']}",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
