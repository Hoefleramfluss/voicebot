import requests

API_URL = "https://api.resmio.com/v1/facility/hofler-am-fluss/bookings"
API_KEY = "bbbe37d3e35649578644b9d5353083e61db6ca59"

def reservierung_an_resmio(num, date, name, phone, comment="Testbuchung über API"):
    headers = {
        "Authorization": f"Bearer bbbe37d3e35649578644b9d5353083e61db6ca59",
        "Content-Type": "application/json"
    }
    payload = {
        "num": num,
        "date": date,
        "name": name,
        "phone": phone,
        "comment": comment,
        "source": "VoiceBot",
        "checksum": "bbbe37d3e35649578644b9d5353083e61db6ca59",
        "fb_access_token": None,
        "newsletter_subscribe": False,
        "resource_group": "",
        "booking_deposit": None,
        "send_email_receipt": True
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    print("Status:", response.status_code)
    print("Antwort:", response.text)
    if response.status_code in (200, 201):
        print("✅ Reservierung erfolgreich!")
        return True
    else:
        print("❌ Fehler bei der Reservierung.")
        return False

if __name__ == "__main__":
    
    num = 2
    date = "2025-07-10T19:00"  # im ISO-Format!
    name = "Susi Test"
    phone = "+4366412345678"
    comment = "Test-API-Reservierung von Susi"

    reservierung_an_resmio(num, date, name, phone, comment)
    
    
