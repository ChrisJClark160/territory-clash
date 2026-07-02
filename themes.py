"""Theme catalogue - team names + tile colours per video.

Colour rules (see WORKING.md design rules): the two sides must stay high
contrast and readable when small/muted on a phone. Ball colours are derived
automatically in main.py. Names are short so "X WINS" fits the banner.

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
    },
    "fire_vs_ice": {
        "names": ("FIRE", "ICE"),
        "colors": {LEFT: (255, 110, 20), RIGHT: (110, 215, 255)},
    },
    "cats_vs_dogs": {
        "names": ("CATS", "DOGS"),
        "colors": {LEFT: (255, 150, 40), RIGHT: (95, 130, 255)},
    },
    "pizza_vs_burger": {
        "names": ("PIZZA", "BURGER"),
        "colors": {LEFT: (230, 60, 50), RIGHT: (255, 190, 60)},
    },
    "xbox_vs_playstation": {
        "names": ("XBOX", "PLAYSTATION"),
        "colors": {LEFT: (70, 220, 70), RIGHT: (40, 90, 255)},
    },
    "iphone_vs_samsung": {
        "names": ("IPHONE", "SAMSUNG"),
        "colors": {LEFT: (200, 200, 210), RIGHT: (40, 120, 255)},
    },
    "minecraft_vs_roblox": {
        "names": ("MINECRAFT", "ROBLOX"),
        "colors": {LEFT: (95, 200, 70), RIGHT: (255, 60, 60)},
    },
    "marvel_vs_dc": {
        "names": ("MARVEL", "DC"),
        "colors": {LEFT: (235, 45, 55), RIGHT: (0, 90, 190)},
    },
    "arsenal_vs_liverpool": {
        "names": ("ARSENAL", "LIVERPOOL"),
        "colors": {LEFT: (255, 55, 65), RIGHT: (0, 185, 165)},
    },
    "kfc_vs_mcdonalds": {
        "names": ("KFC", "MCDONALDS"),
        "colors": {LEFT: (225, 30, 35), RIGHT: (255, 199, 44)},
    },
}
