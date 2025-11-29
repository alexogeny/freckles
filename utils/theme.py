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
    name="Sweet Terminal",
    font="Cascadia Code 12",
    background="#222235",
    foreground="#FFFFFF",
    bold="#FFFFFF",
    cursor_background="#FFFFFF",
    cursor_foreground="#222235",
    highlight_background="#3F3F54",
    highlight_foreground="#FFFFFF",
    palette=(
        "#3F3F54",
        "#F60055",
        "#06C993",
        "#9700BE",
        "#F69154",
        "#EC89CB",
        "#60ADEC",
        "#ABB2BF",
        "#959DCB",
        "#F60055",
        "#06C993",
        "#9700BE",
        "#F69154",
        "#EC89CB",
        "#00DDED",
        "#FFFFFF",
    ),
)


__all__ = [
    "FRECKLES_INTERFACE_THEME",
    "FRECKLES_TERMINAL_THEME",
    "InterfaceTheme",
    "TerminalTheme",
]
