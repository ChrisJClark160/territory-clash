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
    "fortnite_vs_minecraft": {
        "names": ("FORTNITE", "MINECRAFT"),
        "colors": {LEFT: (150, 80, 255), RIGHT: (95, 200, 70)},
        "emoji": ("\U0001FA82", "⛏"),              # parachute, pickaxe
    },
    "zombies_vs_humans": {
        "names": ("ZOMBIES", "HUMANS"),
        "colors": {LEFT: (110, 200, 60), RIGHT: (255, 150, 60)},
        "emoji": ("\U0001F9DF", "\U0001F9D1"),          # zombie, person
    },
    "pirates_vs_ninjas": {
        "names": ("PIRATES", "NINJAS"),
        "colors": {LEFT: (200, 60, 50), RIGHT: (130, 90, 220)},
        "emoji": ("☠", "\U0001F977"),              # skull+bones, ninja
    },
    "dragons_vs_unicorns": {
        "names": ("DRAGONS", "UNICORNS"),
        "colors": {LEFT: (255, 90, 30), RIGHT: (255, 120, 200)},
        "emoji": ("\U0001F409", "\U0001F984"),          # dragon, unicorn
    },
    "aliens_vs_robots": {
        "names": ("ALIENS", "ROBOTS"),
        "colors": {LEFT: (90, 230, 120), RIGHT: (130, 160, 220)},
        "emoji": ("\U0001F47D", "\U0001F916"),          # alien, robot
    },
    "sharks_vs_lions": {
        "names": ("SHARKS", "LIONS"),
        "colors": {LEFT: (60, 140, 255), RIGHT: (240, 180, 50)},
        "emoji": ("\U0001F988", "\U0001F981"),          # shark, lion
    },
    "tiktok_vs_youtube": {
        "names": ("TIKTOK", "YOUTUBE"),
        "colors": {LEFT: (60, 220, 230), RIGHT: (255, 50, 50)},
        "emoji": ("\U0001F3B5", "\U0001F4FA"),          # music note, TV
    },
    "summer_vs_winter": {
        "names": ("SUMMER", "WINTER"),
        "colors": {LEFT: (255, 170, 40), RIGHT: (120, 200, 255)},
        "emoji": ("☀", "⛄"),                  # sun, snowman
    },
    "day_vs_night": {
        "names": ("DAY", "NIGHT"),
        "colors": {LEFT: (255, 210, 70), RIGHT: (110, 80, 220)},
        "emoji": ("\U0001F31E", "\U0001F319"),          # sun face, moon
    },
    "tea_vs_coffee": {
        "names": ("TEA", "COFFEE"),
        "colors": {LEFT: (120, 200, 90), RIGHT: (200, 140, 80)},
        "emoji": ("\U0001F375", "☕"),              # teacup, coffee
    },
    "messi_vs_ronaldo": {
        "names": ("MESSI", "RONALDO"),
        "colors": {LEFT: (120, 190, 255), RIGHT: (230, 40, 60)},
        "emoji": ("\U0001F410", "\U0001F451"),          # goat, crown
    },
    "trex_vs_megalodon": {
        "names": ("T-REX", "MEGALODON"),
        "colors": {LEFT: (140, 200, 60), RIGHT: (70, 130, 230)},
        "emoji": ("\U0001F996", "\U0001F988"),          # t-rex, shark
    },
    "chocolate_vs_vanilla": {
        "names": ("CHOCOLATE", "VANILLA"),
        "colors": {LEFT: (180, 120, 70), RIGHT: (250, 235, 180)},
        "emoji": ("\U0001F36B", "\U0001F366"),          # chocolate, ice cream
    },
    "football_vs_basketball": {
        "names": ("FOOTBALL", "BASKETBALL"),
        "colors": {LEFT: (80, 200, 90), RIGHT: (255, 140, 40)},
        "emoji": ("⚽", "\U0001F3C0"),              # football, basketball
    },
    "coke_vs_pepsi": {
        "names": ("COKE", "PEPSI"),
        "colors": {LEFT: (228, 26, 28), RIGHT: (0, 90, 200)},
        "emoji": ("\U0001F964", "\U0001F9CA"),          # cup with straw, ice
    },
}
