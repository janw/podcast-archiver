from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

_theme = Theme(
    {
        "error": "bold dark_red",
        "warning": "orange1 bold",
        "warning_hint": "orange1 dim",
        "completed": "dark_cyan bold",
        "success": "dark_cyan",
        "present": "dark_cyan",
        "missing": "orange1",
        "title": "bright_magenta bold",
    }
)
console = Console(theme=_theme)
