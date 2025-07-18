import re
from datetime import datetime
from typing import Optional

def parse_reservation_text(text: str) -> dict:
    # Name (einfaches Muster: "Ich bin der ..." oder "Mein Name ist ...")
    name = None
    name_match = re.search(r"(?:ich bin|mein name ist) ([A-Za-zÄÖÜäöüß]+)", text, re.IGNORECASE)
    if name_match:
        name = name_match.group(1)

    # Mapping für gesprochene Monatsnamen und Dialektformen
    MONTHS_SPOKEN = {
        "jänner": 1, "januar": 1, "feber": 2, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5,
        "juni": 6, "juli": 7, "august": 8, "achter": 8, "ochta": 8, "achterl": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
        "neunter": 9, "zehnter": 10, "elfter": 11, "zwölfter": 12
    }
    # Erkenne Datumsangaben wie "siebzehnter achter", "siebzehnta ochta"
    date = None
    # Zuerst Standard-Parsing
    date_match = re.search(r"am (\d{1,2})[\./\- ]?(\d{1,2})?([\.\-/ ]?(\d{2,4}))?", text)
    if date_match:
        day = date_match.group(1)
        month = date_match.group(2)
        year = date_match.group(4) or str(datetime.now().year)
        if month:
            try:
                date = datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y").date().isoformat()
            except Exception:
                date = None
    # Gesprochene Monatsnamen/Dialekt (z.B. "siebzehnter achter", "siebzehnta ochta")
    if not date:
        spoken_date_match = re.search(r"am (\d{1,2})(?:\.|\s|ter|ta|te|ten|ten)?\s*([a-zäöüß]+)", text.lower())
        if spoken_date_match:
            day = spoken_date_match.group(1)
            month_word = spoken_date_match.group(2)
            month = MONTHS_SPOKEN.get(month_word)
            year = str(datetime.now().year)
            if month:
                try:
                    date = datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y").date().isoformat()
                except Exception:
                    date = None
    # Fallback: "morgen", "übermorgen"
    if not date:
        if "morgen" in text.lower():
            date = (datetime.now().date()).isoformat()
        elif "übermorgen" in text.lower():
            date = (datetime.now().date()).isoformat()

    # Uhrzeit ("um 18 Uhr", "18:30", "ab 19 Uhr")
    time = None
    time_match = re.search(r"(?:um |ab )?(\d{1,2})(?:[:\.]?(\d{2}))? ?uhr", text)
    if time_match:
        hour = time_match.group(1)
        minute = time_match.group(2) or "00"
        time = f"{hour.zfill(2)}:{minute.zfill(2)}"

    # Personenanzahl ("für 2 Personen", "17 Personen", "zu sechst", "6 Leute")
    persons = None
    persons_match = re.search(r"für (\d{1,2}) personen|(\d{1,2}) personen|(\d{1,2}) leute|zu (\w+)", text, re.IGNORECASE)
    if persons_match:
        for group in persons_match.groups():
            if group and group.isdigit():
                persons = int(group)
                break

    # Anlass ("Geburtstag", "Taufe", "Feier")
    occasion = None
    for o in ["geburtstag", "taufe", "feier", "hochzeit", "anlass"]:
        if o in text.lower():
            occasion = o
            break

    # Terrasse/Garten
    terrace = "terrasse" in text.lower() or "garten" in text.lower()

    # Kinder/Hund/Rollstuhl
    children = "kinder" in text.lower()
    pets = "hund" in text.lower()
    wheelchair = "rollstuhl" in text.lower()

    # Spezialwunsch
    special = None
    if "spezial" in text.lower() or "wunsch" in text.lower():
        special = text

    return {
        "name": name,
        "date": date,
        "time": time,
        "persons": persons,
        "occasion": occasion,
        "terrace": terrace,
        "children": children,
        "pets": pets,
        "wheelchair": wheelchair,
        "special_request": special,
    }
