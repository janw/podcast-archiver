from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

_theme = Theme(
    {
        "error": "dark_red bold",
        "errorhint": "dark_red dim",
        "warning": "orange1 bold",
        "warninghint": "orange1 dim",
        "completed": "dark_cyan bold",
        "success": "dark_cyan",
        "present": "dark_cyan",
        "missing": "orange1",
        "title": "bright_magenta bold",
    }
)
console = Console(theme=_theme)
