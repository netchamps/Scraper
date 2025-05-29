import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Google Places Scraper+", layout="centered")
st.title("📍 Google Places Scraper – Typ & Freitext kombiniert")

API_KEY = st.secrets["api_key"]

# 🔁 Geocoding
def get_coordinates_from_address(address, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    res = requests.get(url, params=params).json()
    if res["status"] == "OK":
        loc = res["results"][0]["geometry"]["location"]
        return f"{loc['lat']},{loc['lng']}"
    return None

# 🔁 Details API
def get_place_details(place_id, api_key):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,website",
        "key": api_key
    }
    res = requests.get(url, params=params).json()
    if res["status"] == "OK":
        r = res["result"]
        return {"Telefon": r.get("formatted_phone_number", ""), "Website": r.get("website", "")}
    return {"Telefon": "", "Website": ""}

# ✅ Offizielle Google Place Types (auszugsweise)
google_place_types = [
    "restaurant", "cafe", "bar", "gym", "hospital", "pharmacy", "school", "bank",
    "supermarket", "library", "police", "fire_station", "atm", "lodging", "spa",
    "clothing_store", "bakery", "car_repair", "dentist", "doctor", "veterinary_care"
]

# 🎛️ UI
with st.form("input_form"):
    st.markdown("### 🔍 Suchparameter")
    address = st.text_input("📍 Adresse / Stadt", "München")
    radius = st.slider("📏 Suchradius (Meter)", 100, 50000, 1000)
    max_results = st.number_input("🔢 Max. Einträge", min_value=1, max_value=60, value=20, step=1)

    place_type = st.selectbox("🏷️ Kategorie auswählen (optional)", [""] + google_place_types)
    text_query = st.text_input("📝 Oder Freitext-Suche (optional)", "")

    st.markdown("### 📌 Welche Infos brauchst du?")
    col1, col2 = st.columns(2)
    with col1:
        show_name = st.checkbox("✅ Name", value=True)
        show_address = st.checkbox("✅ Adresse", value=True)
        show_rating = st.checkbox("✅ Bewertung", value=True)
        show_maps_link = st.checkbox("✅ Google Maps Link", value=True)
    with col2:
        show_phone = st.checkbox("📞 Telefonnummer", value=True)
        show_website = st.checkbox("🌐 Website", value=True)
        filter_website = st.checkbox("🔍 Nur mit Website anzeigen")
        filter_phone = st.checkbox("🔍 Nur mit Telefonnummer anzeigen")

    submitted = st.form_submit_button("🚀 Suche starten")

if submitted:
    coords = get_coordinates_from_address(address, API_KEY)
    if not coords:
        st.error("❌ Adresse konnte nicht gefunden werden.")
    else:
        with st.spinner("📡 Suche läuft..."):
            data = []
            if text_query:
                # Textsuche verwenden
                url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
                params = {
                    "query": f"{text_query} in {address}",
                    "key": API_KEY
                }
           elif place_type:
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": coords,
        "radius": radius,
        "type": place_type,
        "keyword": text_query,  # z. B. keyword="friseur"
        "key": API_KEY
    }
            else:
                st.error("❗ Bitte entweder einen Typ auswählen oder Freitext eingeben.")
                st.stop()

            while True:
                res = requests.get(url, params=params).json()
                results = res.get("results", [])
                for place in results:
                    if len(data) >= max_results:
                        break
                    entry = {}
                    place_id = place.get("place_id", "")
                    details = get_place_details(place_id, API_KEY) if (show_phone or show_website or filter_phone or filter_website) else {}

                    if filter_website and not details.get("Website"):
                        continue
                    if filter_phone and not details.get("Telefon"):
                        continue

                    if show_name:
                        entry["Name"] = place.get("name", "")
                    if show_address:
                        entry["Adresse"] = place.get("formatted_address", "") or place.get("vicinity", "")
                    if show_rating:
                        entry["Bewertung"] = place.get("rating", "")
                    if show_phone:
                        entry["Telefon"] = details.get("Telefon", "")
                    if show_website:
                        entry["Website"] = details.get("Website", "")
                    if show_maps_link:
                        entry["Google Maps"] = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

                    data.append(entry)

                # Abbruchbedingung
                if len(data) >= max_results or "next_page_token" not in res:
                    break

                time.sleep(2)
                params["pagetoken"] = res["next_page_token"]

            # Ergebnisse anzeigen
            if not data:
                st.warning("⚠️ Keine passenden Ergebnisse gefunden.")
            else:
                df = pd.DataFrame(data)
                st.success(f"{len(df)} Ergebnisse gefunden.")
                st.dataframe(df)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 CSV herunterladen", csv, "places_export.csv", "text/csv")

st.markdown("---")
st.caption("🚀 Powered by Google Places API – 2025")
