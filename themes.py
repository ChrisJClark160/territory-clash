"""Theme catalogue - team names, tile colours and ball emoji per video.

Colour rules (see WORKING.md design rules): the two sides must stay high
contrast and readable when small/muted on a phone. Ball colours are derived
automatically in main.py. Names are short so "X WINS" fits the banner.
Emoji render as monochrome pictograms on the balls (Segoe UI Emoji).

Note: Liverpool uses the teal away kit - home red vs Arsenal red would be
unreadable, and readability beats kit accuracy.
"""

from main import LEFT, RIGHT

THEMES = {
    "classic": {
        "names": ("PINK", "CYAN"),
        "colors": {LEFT: (255, 45, 140), RIGHT: (45, 220, 255)},
    },
    "red_vs_blue": {
        "names": ("RED", "BLUE"),
        "colors": {LEFT: (235, 45, 45), RIGHT: (45, 95, 255)},
        "emoji": ("\U0001F534", "\U0001F535"),          # red/blue circles
    },
    "fire_vs_ice": {
        "names": ("FIRE", "ICE"),
        "colors": {LEFT: (255, 110, 20), RIGHT: (110, 215, 255)},
        "emoji": ("\U0001F525", "❄"),              # fire, snowflake
    },
    "cats_vs_dogs": {
        "names": ("CATS", "DOGS"),
        "colors": {LEFT: (255, 150, 40), RIGHT: (95, 130, 255)},
        "emoji": ("\U0001F431", "\U0001F436"),          # cat, dog faces
    },
    "pizza_vs_burger": {
        "names": ("PIZZA", "BURGER"),
        "colors": {LEFT: (230, 60, 50), RIGHT: (255, 190, 60)},
        "emoji": ("\U0001F355", "\U0001F354"),          # pizza, burger
    },
    "xbox_vs_playstation": {
        "names": ("XBOX", "PLAYSTATION"),
        "colors": {LEFT: (70, 220, 70), RIGHT: (40, 90, 255)},
        "emoji": ("❌", "\U0001F53A"),              # X, triangle
    },
    "iphone_vs_samsung": {
        "names": ("IPHONE", "SAMSUNG"),
        "colors": {LEFT: (200, 200, 210), RIGHT: (40, 120, 255)},
        "emoji": ("\U0001F34E", "\U0001F4F1"),          # apple, phone
    },
    "minecraft_vs_roblox": {
        "names": ("MINECRAFT", "ROBLOX"),
        "colors": {LEFT: (95, 200, 70), RIGHT: (255, 60, 60)},
        "emoji": ("⛏", "\U0001F9F1"),              # pickaxe, brick
    },
    "marvel_vs_dc": {
        "names": ("MARVEL", "DC"),
        "colors": {LEFT: (235, 45, 55), RIGHT: (0, 90, 190)},
        "emoji": ("\U0001F9B8", "\U0001F987"),          # superhero, bat
    },
    "arsenal_vs_liverpool": {
        "names": ("ARSENAL", "LIVERPOOL"),
        "colors": {LEFT: (255, 55, 65), RIGHT: (0, 185, 165)},
        "emoji": ("\U0001F4A3", "⚽"),              # cannon(bomb), ball
    },
    "kfc_vs_mcdonalds": {
        "names": ("KFC", "MCDONALDS"),
        "colors": {LEFT: (225, 30, 35), RIGHT: (255, 199, 44)},
        "emoji": ("\U0001F357", "\U0001F35F"),          # drumstick, fries
    },
}
