import secrets

ADJECTIVES = [
    "Nutmeg",
    "Rabona",
    "Panenka",
    "Offside",
    "Stoppage",
    "Worldie",
    "Volley",
    "Header",
    "Counter",
    "Pressing",
    "Bicycle",
    "Trivela",
    "Backheel",
]

NOUNS = [
    "Maestro",
    "Libero",
    "Sweeper",
    "Playmaker",
    "Keeper",
    "Galactico",
    "Winger",
    "Striker",
    "Anchor",
    "Talisman",
    "Regista",
    "Pivot",
    "Skipper",
]


def generate_display_name() -> str:
    return f"{secrets.choice(ADJECTIVES)}{secrets.choice(NOUNS)}{secrets.randbelow(99) + 1}"
