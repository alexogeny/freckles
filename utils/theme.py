"""Shared Freckles theming primitives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterfaceTheme:
    """Fonts and accents applied across the GNOME desktop."""

    accent: str
    interface_font: str
    document_font: str
    monospace_font: str
    titlebar_font: str


@dataclass(frozen=True)
class TerminalTheme:
    """Colour palette and typography for terminal profiles."""

    name: str
    font: str
    background: str
    foreground: str
    bold: str
    cursor_background: str
    cursor_foreground: str
    highlight_background: str
    highlight_foreground: str
    palette: tuple[str, ...]


FRECKLES_INTERFACE_THEME = InterfaceTheme(
    accent="blue",
    interface_font="Cantarell 11",
    document_font="Cantarell 11",
    monospace_font="Cascadia Code 11",
    titlebar_font="Cantarell Bold 11",
)

FRECKLES_TERMINAL_THEME = TerminalTheme(
    name="Freckles Midnight",
    font="Cascadia Code 12",
    background="rgb(13, 16, 24)",
    foreground="rgb(234, 232, 252)",
    bold="rgb(157, 179, 255)",
    cursor_background="rgb(255, 210, 111)",
    cursor_foreground="rgb(13, 16, 24)",
    highlight_background="rgb(62, 70, 90)",
    highlight_foreground="rgb(245, 245, 250)",
    palette=(
        "rgb(23, 23, 27)",
        "rgb(230, 130, 130)",
        "rgb(104, 201, 129)",
        "rgb(246, 202, 113)",
        "rgb(125, 178, 255)",
        "rgb(172, 129, 255)",
        "rgb(97, 212, 214)",
        "rgb(234, 232, 252)",
        "rgb(70, 74, 85)",
        "rgb(255, 151, 151)",
        "rgb(125, 222, 149)",
        "rgb(255, 213, 128)",
        "rgb(146, 189, 255)",
        "rgb(194, 160, 255)",
        "rgb(128, 226, 228)",
        "rgb(247, 247, 252)",
    ),
)


__all__ = [
    "FRECKLES_INTERFACE_THEME",
    "FRECKLES_TERMINAL_THEME",
    "InterfaceTheme",
    "TerminalTheme",
]
