import streamlit as st
import requests
import pandas as pd

# Titel und Layout
st.set_page_config(page_title="Google Places Scraper+", layout="centered")
st.title("📞 Google Places Scraper mit Telefonnummer & Website")

API_KEY = st.secrets["api_key"] ["openai"] 

# 🔁 Geocoding: Adresse → Koordinaten
def get_coordinates_from_address(address, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    res = requests.get(url, params=params).json()
    if res["status"] == "OK":
        location = res["results"][0]["geometry"]["location"]
        return f"{location['lat']},{location['lng']}"
    return None

# 🔁 Place Details API: Telefonnummer & Website abrufen
def get_place_details(place_id, api_key):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,website",
        "key": api_key
    }
    res = requests.get(url, params=params).json()
    if res["status"] == "OK":
        result = res["result"]
        return {
            "Telefon": result.get("formatted_phone_number", ""),
            "Website": result.get("website", "")
        }
    return {"Telefon": "", "Website": ""}

# 🎛️ Eingabemaske
with st.form("input_form"):
    address = st.text_input("📍 Stadt oder Adresse", "München")
    radius = st.slider("📏 Radius (Meter)", 100, 50000, 1000)
    place_type = st.text_input("🏷️ Kategorie", "restaurant")
    
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
        
    submitted = st.form_submit_button("🔎 Suche starten")

# 🧠 Wenn abgeschickt
if submitted:
    coords = get_coordinates_from_address(address, API_KEY)
    if not coords:
        st.error("❌ Adresse konnte nicht gefunden werden.")
    else:
        with st.spinner("📡 Suche läuft..."):
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": coords,
                "radius": radius,
                "type": place_type,
                "key": API_KEY
            }
            res = requests.get(url, params=params).json()
            results = res.get("results", [])
            data = []

            for place in results:
                entry = {}
                place_id = place.get("place_id", "")

                # Details holen
                details = get_place_details(place_id, API_KEY) if (show_phone or show_website or filter_phone or filter_website) else {}

                if filter_website and not details.get("Website"):
                    continue
                if filter_phone and not details.get("Telefon"):
                    continue

                if show_name:
                    entry["Name"] = place.get("name", "")
                if show_address:
                    entry["Adresse"] = place.get("vicinity", "")
                if show_rating:
                    entry["Bewertung"] = place.get("rating", "")
                if show_phone:
                    entry["Telefon"] = details.get("Telefon", "")
                if show_website:
                    entry["Website"] = details.get("Website", "")
                if show_maps_link:
                    entry["Google Maps"] = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

                data.append(entry)

            # Anzeige
            if not data:
                st.warning("❗ Keine passenden Ergebnisse.")
            else:
                df = pd.DataFrame(data)
                st.success(f"{len(data)} Ergebnisse gefunden.")
                st.dataframe(df)

                # Export
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 CSV herunterladen", csv, "places_export.csv", "text/csv")

# Footer
st.markdown("---")
st.caption("💡 Powered by Google Places & Geocoding API – 2025")
