from pydantic import BaseModel, Field
from textual.design import ColorSystem


class Theme(BaseModel):
    primary: str
    secondary: str | None = None
    warning: str | None = None
    error: str | None = None
    success: str | None = None
    accent: str | None = None
    foreground: str | None = None
    background: str | None = None
    surface: str | None = None
    panel: str | None = None
    boost: str | None = None
    dark: bool = True
    luminosity_spread: float = 0.15
    text_alpha: float = 0.95
    variables: dict[str, str] = Field(default_factory=dict)

    def to_color_system(self) -> ColorSystem:
        """Convert this theme to a ColorSystem."""
        return ColorSystem(**self.model_dump())


BUILTIN_THEMES: dict[str, Theme] = {
    "dark": Theme(
        name="textual-dark",
        primary="#0178D4",
        secondary="#004578",
        accent="#ffa62b",
        warning="#ffa62b",
        error="#ba3c5b",
        success="#4EBF71",
        foreground="#e0e0e0",
    ),
    "galaxy": Theme(
        name="galaxy",
        primary="#8A2BE2",  # Improved Deep Magenta (Blueviolet)
        secondary="#a684e8",
        warning="#FFD700",  # Gold, more visible than orange
        error="#FF4500",  # OrangeRed, vibrant but less harsh than pure red
        success="#00FA9A",  # Medium Spring Green, kept for vibrancy
        accent="#FF69B4",  # Hot Pink, for a pop of color
        dark=True,
        background="#0F0F1F",  # Very Dark Blue, almost black
        surface="#1E1E3F",  # Dark Blue-Purple
        panel="#2D2B55",  # Slightly Lighter Blue-Purple
    ),
    "alpine": Theme(
        name="alpine",
        primary="#4A90E2",  # Clear Sky Blue
        secondary="#81A1C1",  # Misty Blue
        warning="#EBCB8B",  # Soft Sunlight
        error="#BF616A",  # Muted Red
        success="#A3BE8C",  # Alpine Meadow Green
        accent="#5E81AC",  # Mountain Lake Blue
        dark=True,
        background="#262b35",  # Dark Slate Grey
        surface="#3B4252",  # Darker Blue-Grey
        panel="#434C5E",  # Lighter Blue-Grey
    ),
    "cobalt": Theme(
        name="cobalt",
        primary="#334D5C",  # Deep Cobalt Blue
        secondary="#4878A6",  # Slate Blue
        warning="#FFAA22",  # Amber, suitable for warnings related to primary
        error="#E63946",  # Red, universally recognized for errors
        success="#4CAF50",  # Green, commonly used for success indication
        accent="#D94E64",  # Candy Apple Red
        dark=True,
        surface="#27343B",  # Dark Lead
        panel="#2D3E46",  # Storm Gray
        background="#1F262A",  # Charcoal
    ),
    "hacker": Theme(
        name="hacker",
        primary="#00FF00",  # Bright Green (Lime)
        secondary="#32CD32",  # Lime Green
        warning="#ADFF2F",  # Green Yellow
        error="#FF4500",  # Orange Red (for contrast)
        success="#00FA9A",  # Medium Spring Green
        accent="#39FF14",  # Neon Green
        dark=True,
        background="#0D0D0D",  # Almost Black
        surface="#1A1A1A",  # Very Dark Gray
        panel="#2A2A2A",  # Dark Gray
    ),
    "nord": Theme(
        name="nord",
        primary="#88C0D0",
        secondary="#81A1C1",
        accent="#B48EAD",
        foreground="#D8DEE9",
        background="#2E3440",
        success="#A3BE8C",
        warning="#EBCB8B",
        error="#BF616A",
        surface="#3B4252",
        panel="#434C5E",
        variables={
            "block-cursor-background": "#88C0D0",
            "block-cursor-foreground": "#2E3440",
            "block-cursor-text-style": "none",
            "footer-key-foreground": "#88C0D0",
            "input-selection-background": "#81a1c1 35%",
            "button-color-foreground": "#2E3440",
            "button-focus-text-style": "reverse",
        },
    ),
    "gruvbox": Theme(
        name="gruvbox",
        primary="#85A598",
        secondary="#A89A85",
        warning="#fe8019",
        error="#fb4934",
        success="#b8bb26",
        accent="#fabd2f",
        foreground="#fbf1c7",
        background="#282828",
        surface="#3c3836",
        panel="#504945",
        variables={
            "block-cursor-foreground": "#fbf1c7",
            "input-selection-background": "#689d6a40",
            "button-color-foreground": "#282828",
        },
    ),
    "catppuccin-mocha": Theme(
        name="catppuccin-mocha",
        primary="#F5C2E7",
        secondary="#cba6f7",
        warning="#FAE3B0",
        error="#F28FAD",
        success="#ABE9B3",
        accent="#fab387",
        foreground="#cdd6f4",
        background="#181825",
        surface="#313244",
        panel="#45475a",
        variables={
            "input-cursor-foreground": "#11111b",
            "input-cursor-background": "#f5e0dc",
            "input-selection-background": "#9399b2 30%",
            "border": "#b4befe",
            "border-blurred": "#585b70",
            "footer-background": "#45475a",
            "block-cursor-foreground": "#1e1e2e",
            "block-cursor-text-style": "none",
            "button-color-foreground": "#181825",
        },
    ),
    "dracula": Theme(
        name="dracula",
        primary="#BD93F9",
        secondary="#6272A4",
        warning="#FFB86C",
        error="#FF5555",
        success="#50FA7B",
        accent="#FF79C6",
        background="#282A36",
        surface="#2B2E3B",
        panel="#313442",
        foreground="#F8F8F2",
        variables={
            "button-color-foreground": "#282A36",
        },
    ),
    "tokyo-night": Theme(
        name="tokyo-night",
        primary="#BB9AF7",
        secondary="#7AA2F7",
        warning="#E0AF68",  # Yellow
        error="#F7768E",  # Red
        success="#9ECE6A",  # Green
        accent="#FF9E64",  # Orange
        foreground="#a9b1d6",
        background="#1A1B26",  # Background
        surface="#24283B",  # Surface
        panel="#414868",  # Panel
        variables={
            "button-color-foreground": "#24283B",
        },
    ),
    "flexoki": Theme(
        name="flexoki",
        primary="#205EA6",  # blue
        secondary="#24837B",  # cyan
        warning="#AD8301",  # yellow
        error="#AF3029",  # red
        success="#66800B",  # green
        accent="#9B76C8",  # purple light
        background="#100F0F",  # base.black
        surface="#1C1B1A",  # base.950
        panel="#282726",  # base.900
        foreground="#FFFCF0",  # base.paper
        variables={
            "input-cursor-foreground": "#5E409D",
            "input-cursor-background": "#FFFCF0",
            "input-selection-background": "#6F6E69 35%",  # base.600 with opacity
            "button-color-foreground": "#FFFCF0",
        },
    ),
    "caracol": Theme(
        name="caracol",
        primary="#d94a6d",  # cerise
        secondary="#9b7fd4",  # violetl (lavanda)
        accent="#9b7fd4",  # violetl
        warning="#de7f26",  # ocre
        error="#ff4466",  # error pi
        success="#4a7a4a",  # green
        foreground="#e8cfd4",  # platinum
        background="#232031",  # dark
        surface="#312559",  # violet
        panel="#3a3255",  # borderMuted pi
        dark=True,
        variables={
            "block-cursor-background": "#d94a6d",  # cerise
            "block-cursor-foreground": "#111111",  # cursor-text ghostty
            "block-cursor-text-style": "none",
            "input-cursor-foreground": "#111111",
            "input-cursor-background": "#d94a6d",
            "input-selection-background": "#9b7fd4 35%",
            "border": "#d94a6d",  # cerise
            "border-blurred": "#3a3255",
            "footer-key-foreground": "#9b7fd4",
            "footer-description-foreground": "#c0a8a2",  # timberwolf
            "button-color-foreground": "#232031",
        },
    ),
    "papel": Theme(
        name="papel",
        primary="#A34A63",
        secondary="#6F5A82",
        accent="#925020",
        warning="#8B5A14",
        error="#A3444E",
        success="#526B4E",
        foreground="#352F2A",
        background="#FFF5C8",
        surface="#ECE5D9",
        panel="#E2D8CA",
        dark=False,
        variables={
            "border": "#B2A48A",
            "border-blurred": "#C2B69E",
            "footer-background": "#E2D8CA",
            "footer-key-foreground": "#A34A63",
            "footer-description-foreground": "#6F655B",
            "block-cursor-background": "#A34A63",
            "block-cursor-foreground": "#FFF5C8",
            "block-cursor-text-style": "none",
            "input-cursor-foreground": "#FFF5C8",
            "input-cursor-background": "#A34A63",
            "input-selection-background": "#DED3C4",
            "button-color-foreground": "#352F2A",
        },
    ),
    # "textual-light": Theme(
    #     name="textual-light",
    #     primary="#004578",
    #     secondary="#0178D4",
    #     accent="#ffa62b",
    #     warning="#ffa62b",
    #     error="#ba3c5b",
    #     success="#4EBF71",
    #     surface="#D8D8D8",
    #     panel="#D0D0D0",
    #     background="#E0E0E0",
    #     dark=False,
    #     variables={
    #         "footer-key-foreground": "#0178D4",
    #     },
    # ),
    # "catppuccin-latte": Theme(
    #     name="catppuccin-latte",
    #     secondary="#DC8A78",
    #     primary="#8839EF",
    #     warning="#DF8E1D",
    #     error="#D20F39",
    #     success="#40A02B",
    #     accent="#FE640B",
    #     foreground="#4C4F69",
    #     background="#EFF1F5",
    #     surface="#E6E9EF",
    #     panel="#CCD0DA",
    #     dark=False,
    #     variables={
    #         "button-color-foreground": "#EFF1F5",
    #     },
    # ),
    # "solarized-light": Theme(
    #     name="solarized-light",
    #     primary="#268bd2",
    #     secondary="#2aa198",
    #     warning="#cb4b16",
    #     error="#dc322f",
    #     success="#859900",
    #     accent="#6c71c4",
    #     foreground="#586e75",
    #     background="#fdf6e3",
    #     surface="#eee8d5",
    #     panel="#eee8d5",
    #     dark=False,
    #     variables={
    #         "button-color-foreground": "#fdf6e3",
    #         "footer-background": "#268bd2",
    #         "footer-key-foreground": "#fdf6e3",
    #         "footer-description-foreground": "#fdf6e3",
    #     },
    # ),
}
