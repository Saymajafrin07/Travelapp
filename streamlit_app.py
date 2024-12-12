import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
import streamlit as st
import pandas as pd
import datetime
import requests
from openai import AzureOpenAI  # Ensure this import is correct based on your OpenAI package version
from fpdf import FPDF  # Install via pip: pip install fpdf
import json

# ============================
# 🔒 API Key Configuration
# ============================

# Initialize Azure OpenAI client with your credentials
openai_client = AzureOpenAI(
    api_key="3a59a09bd3c740d68d863863d94214ba",  # 🔑 Insert your Azure OpenAI API key here
    api_version="2023-05-15",                     # 📅 Set your OpenAI API version
    azure_endpoint="https://hkust.azure-api.net"   # 🌐 Set your Azure OpenAI endpoint
)

# RapidAPI Key Configuration
RAPIDAPI_KEY = "bade58722emsh90eeb0734c24c82p13e375jsnb8ab70489ec9"  # 🔑 Insert your RapidAPI key here

# ============================
# 📄 Page Configuration
# ============================

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================
# 🎨 Custom CSS Styling
# ============================

st.markdown("""
    <style>
    body {
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }
    .main {
        background-color: #f0f2f6;
        padding: 20px;
    }
    h1, h2, h3, h4 {
        font-family: "Segoe UI Semibold", sans-serif;
    }
    .stButton > button {
        background-color: #1e90ff;
        border: none;
        padding: 0.6em 1em;
        border-radius: 5px;
        color: #fff;
        font-size: 1em;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #0077e6;
    }
    .stTextInput > div > input, .stDateInput > div > input, .stNumberInput input {
        background-color: #fff;
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 0.5em;
    }
    .stSelectbox > div > div {
        border-radius: 5px !important;
    }
    .st-mc, .st-ml {
        font-size: 0.9em;
    }
    .info-text {
        font-size: 0.9em;
        color: #555;
    }
    </style>
""", unsafe_allow_html=True)

# ============================
# 🛠️ Sidebar Configuration
# ============================

st.sidebar.title("🔑 Configuration & Help")
st.sidebar.image("https://i.imgur.com/6Iej2c6.png", use_column_width=True)
st.sidebar.write("**Welcome to the AI Travel Planner!**")
st.sidebar.write("Provide destination, travel details, and flight parameters. The AI will generate a personalized itinerary.")

# ============================
# 🗄️ Session State Initialization
# ============================

if 'cities' not in st.session_state:
    st.session_state.cities = []
if 'currencies' not in st.session_state:
    st.session_state.currencies = []

# ============================
# 🌐 API Headers Setup
# ============================

headers = {
    "x-rapidapi-key": RAPIDAPI_KEY,  # 🔑 Your RapidAPI key
    "x-rapidapi-host": "tripadvisor16.p.rapidapi.com"
}

# ============================
# 🔌 API Utility Functions
# ============================

def test_connection():
    """
    Test the connection to the TripAdvisor API.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/test"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_supported_currencies():
    """
    Retrieve supported currencies from the TripAdvisor API.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/getCurrency"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "currencies" in data["data"]:
                return data["data"]["currencies"]
    except requests.RequestException as e:
        st.error(f"Error fetching supported currencies: {str(e)}")
    return []

def search_location(city):
    """
    Search for a location ID based on the city name.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchLocation"
    params = {"query": city}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]:
                return data["data"][0].get("locationId")
    except requests.RequestException as e:
        st.error(f"Error searching location for {city}: {str(e)}")
    return None

def search_airport(city_name):
    """
    Search for an airport code by city name.
    Returns the first matching IATA code or None.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchAirport"
    params = {"query": city_name}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                airport_code = data["data"][0].get("code") or data["data"][0].get("airportCode")
                return airport_code
    except requests.RequestException as e:
        st.error(f"Error searching airport for {city_name}: {str(e)}")
    return None

def get_hotels(location_id, currency="USD"):
    """
    Retrieve a list of hotels based on the location ID and currency.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchHotels"
    params = {"pageNumber": "1", "currencyCode": currency, "locationId": location_id}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        hotels_data = []
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "data" in data["data"]:
                for hotel in data["data"]["data"]:
                    geo = hotel.get("geoPoint", {})
                    hotel_info = {
                        "name": hotel.get("name"),
                        "price": hotel.get("priceForDisplay"),
                        "rating": hotel.get("rating"),
                        "address": geo.get("addressString", ""),
                        "latitude": geo.get("latitude"),
                        "longitude": geo.get("longitude")
                    }
                    hotels_data.append(hotel_info)
        return hotels_data
    except requests.RequestException as e:
        st.error(f"Error fetching hotels: {str(e)}")
    return []

def get_restaurants(location_id, currency="USD"):
    """
    Retrieve a list of restaurants based on the location ID and currency.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"
    params = {"locationId": location_id, "currencyCode": currency}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        restaurants_data = []
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "data" in data["data"]:
                for restaurant in data["data"]["data"]:
                    geo = restaurant.get("geoPoint", {})
                    restaurant_info = {
                        "name": restaurant.get("name"),
                        "cuisine": [c.get("localizedName") for c in restaurant.get("cuisine", []) if "localizedName" in c],
                        "rating": restaurant.get("rating"),
                        "latitude": geo.get("latitude"),
                        "longitude": geo.get("longitude")
                    }
                    restaurants_data.append(restaurant_info)
        return restaurants_data
    except requests.RequestException as e:
        st.error(f"Error fetching restaurants: {str(e)}")
    return []

def get_rentals(location_id, currency="USD"):
    """
    Retrieve a list of vacation rentals based on the location ID and currency.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/rentals/rentalSearch"
    params = {"sortOrder":"POPULARITY","page":"1","currencyCode": currency, "locationId": location_id}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        rentals_data = []
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "data" in data["data"]:
                for rental in data["data"]["data"]:
                    rental_info = {
                        "name": rental.get("name"),
                        "price": rental.get("priceForDisplay"),
                        "rating": rental.get("rating")
                    }
                    rentals_data.append(rental_info)
        return rentals_data
    except requests.RequestException as e:
        st.error(f"Error fetching rentals: {str(e)}")
    return []

def get_flights(source_airport, destination_airport, currency="USD"):
    """
    Retrieve a list of flights based on source and destination airport codes and currency.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchFlights"
    params = {
        "sourceAirportCode": source_airport,
        "destinationAirportCode": destination_airport,
        "itineraryType": "ONE_WAY",
        "sortOrder": "ML_BEST_VALUE",
        "numAdults": "1",
        "numSeniors": "0",
        "classOfService": "ECONOMY",
        "pageNumber": "1",
        "nearby": "yes",
        "nonstop": "yes",
        "currencyCode": currency,
        "region": "USA"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        flights_data = []
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "flights" in data["data"]:
                for flight in data["data"]["flights"][:3]:
                    price = flight.get("displayPrice", "N/A")
                    airline_codes = flight.get("details", {}).get("airlineCodes", ["Unknown"])
                    flights_data.append({"airline": airline_codes[0], "price": price})
        return flights_data
    except requests.RequestException as e:
        st.error(f"Error fetching flights: {str(e)}")
    return []

def get_flight_filters(source_airport, destination_airport, itinerary_type, class_of_service, departure_date, currency="USD"):
    """
    Retrieve flight filters based on flight parameters.
    """
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/getFilters"
    params = {
        "sourceAirportCode": source_airport,
        "destinationAirportCode": destination_airport,
        "itineraryType": itinerary_type,
        "classOfService": class_of_service,
        "departureDate": departure_date.strftime("%Y-%m-%d")
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        filters_data = {}
        if response.status_code == 200:
            filters_data = response.json()
        return filters_data
    except requests.RequestException as e:
        st.error(f"Error fetching flight filters: {str(e)}")
    return {}

def get_data_from_api(city, currency, source_city, arrival_date):
    """
    Aggregate data from various APIs based on user inputs.
    """
    api_data = {}
    location_id = search_location(city)

    if location_id is None:
        st.warning(f"No location found for {city}. Some data may be unavailable. Please try a more specific city or check spelling.")

    hotels = get_hotels(location_id, currency) if location_id else []
    restaurants = get_restaurants(location_id, currency) if location_id else []
    rentals = get_rentals(location_id, currency) if location_id else []

    # Get airport codes for source and destination cities
    source_airport_code = search_airport(source_city) if source_city else None
    destination_airport_code = search_airport(city) if city else None  # Flight Arrival City is same as Destination City

    if source_city and not source_airport_code:
        st.warning(f"No airports found for your current place: {source_city}. Flights data may be unavailable.")
    if city and not destination_airport_code:
        st.warning(f"No airports found for destination city: {city}. Flights data may be unavailable.")

    flights = []
    flight_filters = {}
    if source_airport_code and destination_airport_code:
        flights = get_flights(source_airport_code, destination_airport_code, currency=currency)
        flight_filters = get_flight_filters(
            source_airport=source_airport_code,
            destination_airport=destination_airport_code,
            itinerary_type="ONE_WAY",
            class_of_service="ECONOMY",
            departure_date=arrival_date,
            currency=currency
        )

    api_data["hotels"] = hotels
    api_data["restaurants"] = restaurants
    api_data["rentals"] = rentals
    api_data["flights"] = flights
    api_data["flight_filters"] = flight_filters

    return api_data

# ============================
# 🤖 Generate Trip Suggestion
# ============================

def generate_trip_suggestion(client, city, arrival_date, departure_date, preferences, budget, accommodation, transport, api_data):
    """
    Generate a detailed trip itinerary using the Azure OpenAI client.
    """
    preferences_text = ""
    if preferences:
        preferences_text = " They prefer " + ", ".join(preferences) + "."

    api_data_text = ""

    if api_data.get("flights"):
        api_data_text += "\n\n**Flight Options:**\n"
        for flight in api_data["flights"]:
            api_data_text += f"- Airline: {flight['airline']}, Price: {flight['price']}\n"

    if api_data.get("flight_filters"):
        api_data_text += "\n**Flight Filters (example data):**\n"
        api_data_text += f"{json.dumps(api_data['flight_filters'], indent=2)}\n"

    if api_data.get("hotels"):
        api_data_text += "\n**Recommended Hotels:**\n"
        for h in api_data["hotels"][:3]:
            api_data_text += f"- {h['name']} (Price: {h['price']}, Rating: {h['rating']})\n"

    if api_data.get("restaurants"):
        api_data_text += "\n**Recommended Restaurants:**\n"
        for r in api_data["restaurants"][:3]:
            cuisines = ", ".join(r["cuisine"]) if r["cuisine"] else "Various cuisines"
            api_data_text += f"- {r['name']} (Cuisine: {cuisines}, Rating: {r['rating']})\n"

    if api_data.get("rentals"):
        api_data_text += "\n**Recommended Vacation Rentals:**\n"
        for rr in api_data["rentals"][:3]:
            api_data_text += f"- {rr['name']} (Price: {rr['price']}, Rating: {rr['rating']})\n"

    # === Added Instruction for Proximity to Attractions ===
    proximity_instruction = (
        "\n\n**Note:** All recommended hotels, restaurants, and rentals are located near major attractions in the city."
    )

    prompt = (
        f"Please generate a detailed itinerary for {city} from {arrival_date} to {departure_date}."
        f" The user's budget is ${budget} per day and they prefer {accommodation} accommodation and {transport} for transportation."
        f"{preferences_text}"
        f"{api_data_text}"
        f"{proximity_instruction}"
        f"\n\nProvide a day-by-day itinerary based on the above information."
    )

    try:
        response = client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful travel planner assistant who provides detailed, friendly, and easy-to-read travel itineraries."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating trip suggestion: {str(e)}"

# ============================
# 🚀 Check API Connection
# ============================

if not test_connection():
    st.error("Failed to connect to the TripAdvisor API. Please check your network and API credentials.")
    st.stop()

# ============================
# 💱 Fetch Supported Currencies
# ============================

if not st.session_state.currencies:
    currencies = get_supported_currencies()
    st.session_state.currencies = currencies if currencies else ["USD"]

# ============================
# 🖥️ User Interface
# ============================

# Page Title and Instructions
st.title("🌍 AI-Powered Travel Planner")
st.write("""
**Welcome!** Provide your travel details, including your current location.
We will find the matching airports automatically and generate a personalized itinerary.
""")

st.subheader("📝 Plan Your Trip")

with st.form("add_city"):
    st.write("**Basic Travel Details**")
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("Destination City", help="e.g., 'New York', 'Paris', 'Tokyo'")
        arrival_date = st.date_input("Arrival Date", datetime.date.today(), help="Your starting travel date (also used as flight departure date).")
    with col2:
        departure_date = st.date_input("Departure Date", datetime.date.today() + datetime.timedelta(days=5), help="Your return travel date.")
    budget = st.number_input("Daily Budget (USD)", min_value=50, max_value=10000, value=200, step=50, help="Your daily spending limit.")
    accommodation = st.selectbox("Accommodation Type", ["hostel", "hotel", "apartment", "resort"], help="Preferred lodging type.")
    transport = st.selectbox("Preferred Transportation", ["public transportation", "rental car", "taxi", "ride-sharing"], help="Main mode of travel.")
    preferences = st.multiselect("Interests/Preferences", ["adventure", "relaxation", "cultural sites", "nightlife", "foodie"], help="Select your travel interests.")

    st.write("**Flight Parameters**")
    # Changed label from "Flight Departure City" to "My Current Place"
    source_city = st.text_input("My Current Place", help="City from where you will start your flight. The app finds the nearest airport.")
    # Removed "Flight Arrival City" as it will be same as Destination City
    # destination_city = st.text_input("Flight Arrival City", help="City where your flight lands. The app finds the nearest airport.")

    currency_choices = ["USD"] + st.session_state.currencies
    currency = st.selectbox("Preferred Currency", currency_choices, help="Prices displayed in this currency.")

    submit = st.form_submit_button("Add Destination")

if submit and city:
    # Input Validation
    missing_fields = []
    if not city:
        missing_fields.append("Destination City")
    if not arrival_date:
        missing_fields.append("Arrival Date")
    if not departure_date:
        missing_fields.append("Departure Date")
    if not budget:
        missing_fields.append("Daily Budget")
    if not accommodation:
        missing_fields.append("Accommodation Type")
    if not transport:
        missing_fields.append("Preferred Transportation")
    if not currency:
        missing_fields.append("Preferred Currency")
    if not source_city:
        missing_fields.append("My Current Place")

    if departure_date <= arrival_date:
        st.error("Departure date must be after the arrival date.")
    elif missing_fields:
        st.error(f"Please fill in the following fields: {', '.join(missing_fields)}")
    else:
        with st.spinner("Fetching travel suggestions..."):
            # Since Flight Arrival City is same as Destination City, pass 'city' as destination_city
            api_data = get_data_from_api(city, currency, source_city, arrival_date)
            suggestion = generate_trip_suggestion(
                client=openai_client,
                city=city,
                arrival_date=arrival_date,
                departure_date=departure_date,
                preferences=preferences,
                budget=budget,
                accommodation=accommodation,
                transport=transport,
                api_data=api_data
            )

        st.subheader(f"Suggested Itinerary for {city}")

        # Editable Itinerary
        edited_itinerary = st.text_area("Edit Your Itinerary:", value=suggestion, height=300)

        # Generate Interactive Map
        st.markdown("### 📍 Recommended Locations on Map")
        # Collect latitude and longitude from hotels and restaurants
        map_data = []
        for hotel in api_data.get("hotels", []):
            if hotel.get("latitude") and hotel.get("longitude"):
                map_data.append({
                    "lat": hotel["latitude"],
                    "lon": hotel["longitude"],
                    "name": hotel["name"],
                    "type": "Hotel"
                })
        for restaurant in api_data.get("restaurants", []):
            if restaurant.get("latitude") and restaurant.get("longitude"):
                map_data.append({
                    "lat": restaurant["latitude"],
                    "lon": restaurant["longitude"],
                    "name": restaurant["name"],
                    "type": "Restaurant"
                })
        # Convert to DataFrame
        if map_data:
            map_df = pd.DataFrame(map_data)
            st.map(map_df[['lat', 'lon']])
        else:
            st.write("No location data available to display on the map.")

        # Downloadable Itinerary as PDF
        def generate_pdf(itinerary_text, city_name):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"Itinerary for {city_name}", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            for line in itinerary_text.split('\n'):
                pdf.multi_cell(0, 10, line)
            return pdf.output(dest='S').encode('latin1')

        if st.button("Download Itinerary as PDF"):
            pdf_bytes = generate_pdf(edited_itinerary, city)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"{city}_itinerary.pdf",
                mime="application/pdf"
            )

        # Feedback Form
        st.markdown("### 📝 Provide Your Feedback")
        with st.form("feedback_form"):
            feedback = st.text_area("Your Feedback:", height=100, help="Share your thoughts or suggestions about the itinerary.")
            submit_feedback = st.form_submit_button("Submit Feedback")
            if submit_feedback:
                if feedback.strip() == "":
                    st.warning("Please enter your feedback before submitting.")
                else:
                    # For demonstration, we'll just display a success message.
                    # In production, you might want to save this feedback to a database or send it via email.
                    st.success("Thank you for your feedback!")

        # Store city in session state
        st.session_state.cities.append({
            "city": city,
            "arrival_date": arrival_date,
            "departure_date": departure_date,
            "suggestion": edited_itinerary
        })

# ============================
# 📜 Display Planned Trips
# ============================

if st.session_state.cities:
    st.subheader("Your Planned Trips")
    st.write("Below are the itineraries you've generated so far.")
    for idx, c in enumerate(st.session_state.cities, 1):
        st.write(f"### {idx}. **{c['city']}** from {c['arrival_date']} to {c['departure_date']}")
        st.write(c["suggestion"])
