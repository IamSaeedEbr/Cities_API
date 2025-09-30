import csv
import requests
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
CITIES_FILE = os.getenv("CITIES_FILE", "Cities/CountryCode-City.csv")

def post_city(city, country_code):
    payload = {"city": city.strip(), "country_code": country_code.strip()}
    r = requests.post(f"{API_URL}/city", json=payload)
    if r.status_code in (200, 201):
        print(f"Upserted: {city} -> {country_code}")
    else:
        print(f"Failed {city}: {r.status_code} {r.text}")

def main():
    if not os.path.exists(CITIES_FILE):
        print(f"File not found: {CITIES_FILE}")
        return

    with open(CITIES_FILE, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Handle header 'countyCode' typo
            country_code = row.get("countryCode") or row.get("countyCode")
            city = row.get("city")
            if city and country_code:
                post_city(city, country_code)
            else:
                print("Skipping row:", row)

if __name__ == "__main__":
    main()
