#!/usr/bin/env python3
"""Download circle-flags SVGs for the 48 World Cup teams.

Prompts the user to confirm/correct the HatScripts country code for each
FIFA team code, then downloads the SVG from GitHub.
"""

import os
import urllib.request

DEST_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "flags")
BASE_URL = "https://raw.githubusercontent.com/HatScripts/circle-flags/gh-pages/flags"

TEAMS_WITH_SUGGESTIONS = {
    "ALG": "dz",
    "ARG": "ar",
    "AUS": "au",
    "AUT": "at",
    "BEL": "be",
    "BIH": "ba",
    "BRA": "br",
    "CAN": "ca",
    "CIV": "ci",
    "COD": "cd",
    "COL": "co",
    "CPV": "cv",
    "CRO": "hr",
    "CUW": "cw",
    "CZE": "cz",
    "ECU": "ec",
    "EGY": "eg",
    "ENG": "gb-eng",
    "ESP": "es",
    "FRA": "fr",
    "GER": "de",
    "GHA": "gh",
    "HAI": "ht",
    "IRN": "ir",
    "IRQ": "iq",
    "JOR": "jo",
    "JPN": "jp",
    "KOR": "kr",
    "KSA": "sa",
    "MAR": "ma",
    "MEX": "mx",
    "NED": "nl",
    "NOR": "no",
    "NZL": "nz",
    "PAN": "pa",
    "PAR": "py",
    "POR": "pt",
    "QAT": "qa",
    "RSA": "za",
    "SCO": "gb-sct",
    "SEN": "sn",
    "SUI": "ch",
    "SWE": "se",
    "TUN": "tn",
    "TUR": "tr",
    "URU": "uy",
    "USA": "us",
    "UZB": "uz",
}

COUNTRY_NAMES = {
    "ALG": "Algeria",
    "ARG": "Argentina",
    "AUS": "Australia",
    "AUT": "Austria",
    "BEL": "Belgium",
    "BIH": "Bosnia & Herzegovina",
    "BRA": "Brazil",
    "CAN": "Canada",
    "CIV": "Côte d'Ivoire",
    "COD": "DR Congo",
    "COL": "Colombia",
    "CPV": "Cape Verde",
    "CRO": "Croatia",
    "CUW": "Curaçao",
    "CZE": "Czech Republic",
    "ECU": "Ecuador",
    "EGY": "Egypt",
    "ENG": "England",
    "ESP": "Spain",
    "FRA": "France",
    "GER": "Germany",
    "GHA": "Ghana",
    "HAI": "Haiti",
    "IRN": "Iran",
    "IRQ": "Iraq",
    "JOR": "Jordan",
    "JPN": "Japan",
    "KOR": "South Korea",
    "KSA": "Saudi Arabia",
    "MAR": "Morocco",
    "MEX": "Mexico",
    "NED": "Netherlands",
    "NOR": "Norway",
    "NZL": "New Zealand",
    "PAN": "Panama",
    "PAR": "Paraguay",
    "POR": "Portugal",
    "QAT": "Qatar",
    "RSA": "South Africa",
    "SCO": "Scotland",
    "SEN": "Senegal",
    "SUI": "Switzerland",
    "SWE": "Sweden",
    "TUN": "Tunisia",
    "TUR": "Turkey",
    "URU": "Uruguay",
    "USA": "United States",
    "UZB": "Uzbekistan",
}


def main():
    os.makedirs(DEST_DIR, exist_ok=True)

    confirmed = {}
    teams = list(TEAMS_WITH_SUGGESTIONS.keys())

    print("\nMap each FIFA code to a HatScripts code (ISO 3166-1 alpha-2).")
    print("Press Enter to accept the suggestion, or type a different code.\n")

    for team in teams:
        suggestion = TEAMS_WITH_SUGGESTIONS[team]
        name = COUNTRY_NAMES[team]
        user_input = input(f"  {team} ({name}) -> [{suggestion}]: ").strip().lower()
        confirmed[team] = user_input if user_input else suggestion

    print(f"\n--- Downloading {len(confirmed)} flags ---\n")

    success = 0
    for team, code in confirmed.items():
        url = f"{BASE_URL}/{code}.svg"
        dest = os.path.join(DEST_DIR, f"{team}.svg")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  OK  {team} <- {code}.svg")
            success += 1
        except Exception as e:
            print(f"  FAIL  {team} <- {code}.svg  ({e})")

    print(
        f"\nDone: {success}/{len(confirmed)} flags saved to {os.path.abspath(DEST_DIR)}"
    )


if __name__ == "__main__":
    main()
