import requests

API_URL = "https://api.resmio.com/v1/facility/hofler-am-fluss/bookings"
API_KEY = "bbbe37d3e35649578644b9d5353083e61db6ca59"

def finde_id_per_ref(ref_num_eingabe):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    # Entfernt alle Raute-Zeichen und Leerzeichen aus der Eingabe
    ref_num_suche = ref_num_eingabe.replace("#", "").replace(" ", "").strip()

    response = requests.get(API_URL, headers=headers, params={"limit": 100})
    if response.status_code != 200:
        print(f"Fehler bei API-Anfrage: {response.status_code} {response.text}")
        return None

    daten = response.json()
    buchungen = daten.get("objects", [])
    for buchung in buchungen:
        ref_num_api = buchung.get("ref_num", "")
        # Case-insensitive Vergleich ohne Raute oder Leerzeichen
        if ref_num_api and ref_num_api.lower() == ref_num_suche.lower():
            return buchung.get("id")
    return None

def storniere_reservierung_per_id(booking_id):
    url = f"{API_URL}/{booking_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"✅ Reservierung {booking_id} erfolgreich storniert.")
    else:
        print(f"❌ Fehler beim Stornieren: {response.status_code} {response.text}")

if __name__ == "__main__":
    ref_num_input = input("Bitte Reservierungsnummer eingeben (z.B. CO0tFv oder #CO0tFv): ").strip()
    booking_id = finde_id_per_ref(ref_num_input)
    if booking_id:
        print(f"Reservierung mit ID {booking_id} gefunden.")
        bestaetigung = input("Möchtest du diese Reservierung wirklich stornieren? (j/n): ").strip().lower()
        if bestaetigung == "j":
            storniere_reservierung_per_id(booking_id)
        else:
            print("Stornierung abgebrochen.")
    else:
        print("❌ Keine Reservierung mit dieser Nummer gefunden.")
