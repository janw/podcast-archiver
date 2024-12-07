from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

_theme = Theme(
    {
        "error": "bold dark_red",
        "warning": "magenta",
        "missing": "orange1",
        "completed": "bold dark_cyan",
        "success": "dark_cyan",
    }
)
console = Console(theme=_theme)
