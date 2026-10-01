import base64
import os
import smtplib
from datetime import date, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

# API Keys
DUFFEL_API_KEY = os.environ.get("DUFFEL_API_KEY")
GEOAPIFY_API_KEY = os.environ.get("GEOAPIFY_API_KEY")
# -----------------------------------------
# EMAIL CONFIGURATION (from environment variables)
# -----------------------------------------
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")


# -----------------------------------------
# TOOL 1: WEATHER
# -----------------------------------------

def get_weather(city):
    """Get current weather for a city."""
    try:
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        }

        geo_response = requests.get(geocoding_url, params=geo_params, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return {"success": False, "error": f"City '{city}' was not found."}

        location = geo_data["results"][0]
        latitude = location["latitude"]
        longitude = location["longitude"]

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "apparent_temperature,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "timezone": "auto",
        }

        weather_response = requests.get(weather_url, params=weather_params, timeout=10)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        current = weather_data["current"]

        return {
            "success": True,
            "city": location["name"],
            "country": location.get("country"),
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "wind_speed": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
            "timezone": weather_data.get("timezone"),
        }

    except requests.RequestException as error:
        return {"success": False, "error": f"Weather API problem: {error}"}


# -----------------------------------------
# TOOL 2: CURRENCY
# -----------------------------------------

def convert_currency(amount, from_currency, to_currency):
    try:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        url = f"https://open.er-api.com/v6/latest/{from_currency}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("result") != "success":
            return {
                "success": False,
                "error": "Could not retrieve currency rates.",
            }

        rates = data.get("rates", {})
        if to_currency not in rates:
            return {
                "success": False,
                "error": f"Currency {to_currency} is not supported.",
            }

        rate = rates[to_currency]
        converted_amount = amount * rate

        return {
            "success": True,
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "converted_amount": round(converted_amount, 2),
        }

    except requests.RequestException as error:
        return {"success": False, "error": f"Currency API problem: {error}"}


# -----------------------------------------
# TOOL 3: BUDGET CALCULATOR
# -----------------------------------------

def calculate_daily_budget(total_budget, days):
    try:
        total_budget = float(total_budget)
        days = int(days)

        if days <= 0:
            return {
                "success": False,
                "error": "Days must be greater than zero.",
            }

        daily_budget = total_budget / days

        return {
            "success": True,
            "total_budget": total_budget,
            "days": days,
            "daily_budget": round(daily_budget, 2),
        }

    except (ValueError, TypeError):
        return {"success": False, "error": "Invalid budget or number of days."}


def create_trip_plan(
    destination,
    days,
    total_budget,
    work_days,
    interests,
    work_start,
    work_end,
    avoid,
):
    daily_budget = total_budget / days
    trip_days = []

    suggested_interests = [interest for interest in interests if interest not in avoid]

    for day_number in range(1, days + 1):
        if day_number in work_days:
            day = {
                "day": day_number,
                "budget": round(daily_budget, 2),
                "type": "work",
                "work_start": work_start,
                "work_end": work_end,
                "available_time": "after work",
                "suggested_activity_types": suggested_interests[:2],
            }
        else:
            day = {
                "day": day_number,
                "budget": round(daily_budget, 2),
                "type": "free",
                "work_start": None,
                "work_end": None,
                "available_time": "full day",
                "suggested_activity_types": suggested_interests,
            }
        trip_days.append(day)

    return {
        "success": True,
        "destination": destination,
        "days": days,
        "total_budget": total_budget,
        "daily_budget": round(daily_budget, 2),
        "work_days": work_days,
        "interests": interests,
        "work_start": work_start,
        "work_end": work_end,
        "avoid": avoid,
        "plan": trip_days,
    }


def search_flights(origin, destination, departure_date, cabin_class="economy", adults=1):
    DUFFEL_BASE_URL = "https://api.duffel.com"

    if not DUFFEL_API_KEY:
        return {
            "success": False,
            "error": "DUFFEL_API_KEY is not set in the environment.",
        }

    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Duffel-Version": "v2",
            "Authorization": f"Bearer {DUFFEL_API_KEY}",
        }

        payload = {
            "data": {
                "cabin_class": cabin_class,
                "slices": [
                    {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date,
                    }
                ],
                "passengers": [{"type": "adult"} for _ in range(adults)],
            }
        }

        response = requests.post(
            f"{DUFFEL_BASE_URL}/air/offer_requests",
            headers=headers,
            json=payload,
            timeout=20,
        )

        response.raise_for_status()
        data = response.json().get("data", {})
        offers = data.get("offers", [])
        if not offers:
            simplified_offers = _generate_mock_offers(
                origin, destination, departure_date, cabin_class, adults
            )
            return {
                "success": True,
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "offers": simplified_offers,
                "is_estimated": True,
            }

        simplified_offers = []
        for offer in offers[:8]:
            first_slice = offer["slices"][0]
            first_segment = first_slice["segments"][0]

            simplified_offers.append(
                {
                    "offer_id": offer["id"],
                    "airline": offer.get("owner", {}).get("name"),
                    "price": offer.get("total_amount"),
                    "currency": offer.get("total_currency"),
                    "cabin_class": cabin_class,
                    "departure_time": first_segment.get("departing_at"),
                    "arrival_time": first_segment.get("arriving_at"),
                    "duration": first_slice.get("duration"),
                    "stops": len(first_slice.get("segments", [])) - 1,
                }
            )

        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "offers": simplified_offers,
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "error": f"Flight search API problem: {error}",
        }

import random

def _generate_mock_offers(origin, destination, departure_date, cabin_class, adults):
    """Fallback fake offers when the real API has no data for this route/date."""
    airlines = ["Royal Jordanian", "Turkish Airlines", "Emirates", "Qatar Airways"]
    offers = []
    for i in range(3):
        price = round(random.uniform(120, 480), 2)
        dep_hour = random.choice([6, 9, 13, 17, 21])
        duration_hours = random.choice([2, 3, 4, 5])
        offers.append({
            "offer_id": f"mock-{origin}-{destination}-{departure_date}-{i}",
            "airline": random.choice(airlines),
            "price": str(price),
            "currency": "USD",
            "cabin_class": cabin_class,
            "departure_time": f"{departure_date}T{dep_hour:02d}:00:00",
            "arrival_time": f"{departure_date}T{(dep_hour + duration_hours) % 24:02d}:00:00",
            "duration": f"PT{duration_hours}H",
            "stops": random.choice([0, 0, 1]),
            "is_estimated": True,
        })
    return offers


def search_flights_range(origin, destination, start_date=None, days_ahead=7, cabin_class="economy", adults=1):
    if start_date is None:
        start_date = date.today().isoformat()

    try:
        start = date.fromisoformat(start_date)
    except ValueError:
        return {
            "success": False,
            "error": "Invalid start_date format. Use YYYY-MM-DD.",
        }

    available_dates = {}

    for offset in range(days_ahead):
        current_date = (start + timedelta(days=offset)).isoformat()
        day_result = search_flights(
            origin=origin,
            destination=destination,
            departure_date=current_date,
            cabin_class=cabin_class,
            adults=adults,
        )

        if day_result.get("success") and day_result.get("offers"):
            available_dates[current_date] = day_result["offers"]

    if not available_dates:
        return {
            "success": False,
            "error": f"No available flights found for {origin} -> {destination} in the next {days_ahead} days.",
        }

    return {
        "success": True,
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "days_checked": days_ahead,
        "available_dates": available_dates,
    }


# -----------------------------------------
# TOOL: ROUTING
# -----------------------------------------

def get_route(from_lat, from_lon, to_lat, to_lon, mode="walk"):
    if not GEOAPIFY_API_KEY:
        return {
            "success": False,
            "error": "GEOAPIFY_API_KEY is not set in environment variables.",
        }

    try:
        url = "https://api.geoapify.com/v1/routing"
        params = {
            "waypoints": f"{from_lat},{from_lon}|{to_lat},{to_lon}",
            "mode": mode,
            "apiKey": GEOAPIFY_API_KEY,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        if not features:
            return {
                "success": False,
                "error": "Could not find a route between the given coordinates.",
            }

        properties = features[0].get("properties", {})
        distance_meters = properties.get("distance", 0)
        distance_km = round(distance_meters / 1000.0, 2)

        time_seconds = properties.get("time", 0)
        travel_minutes = round(time_seconds / 60.0)

        warning = None
        if travel_minutes > 60:
            warning = "Warning: The walking time between these places is more than 60 minutes, which may be inconvenient."

        return {
            "success": True,
            "distance_km": distance_km,
            "travel_minutes": travel_minutes,
            "mode": mode,
            "warning": warning,
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "error": f"Geoapify Routing API error: {error}",
        }


# -----------------------------------------
# TOOL: SEND EMAIL
# -----------------------------------------

def send_plan_email(recipient, image_data_url):
    if not recipient:
        return {
            "success": False,
            "error": "Please enter a valid email address.",
        }

    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD or EMAIL_ADDRESS == "exampil@gmail.com":
        return {
            "success": False,
            "error": "Email sending is not configured on the server. Please update EMAIL_ADDRESS and EMAIL_APP_PASSWORD in tools.py.",
        }

    if not image_data_url or "," not in image_data_url:
        return {"success": False, "error": "No plan image was received."}

    try:
        header, encoded = image_data_url.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        msg = MIMEMultipart("related")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient
        msg["Subject"] = "Your Travel Plan"

        html = """
        <html>
          <body style="margin:0; padding:24px; background:#f1f5f9;">
            <img src="cid:plan_image" style="max-width:100%; border-radius:12px;">
          </body>
        </html>
        """

        msg.attach(MIMEText(html, "html", "utf-8"))

        image_part = MIMEImage(image_bytes, _subtype="png")
        image_part.add_header("Content-ID", "<plan_image>")
        image_part.add_header(
            "Content-Disposition", "inline", filename="travel-plan.png"
        )
        msg.attach(image_part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)

        return {
            "success": True,
            "message": "Your travel plan was sent successfully!",
        }

    except Exception as error:
        print("Email error:", error)
        return {
            "success": False,
            "error": f"Could not send the email: {error}",
        }


def revise_itinerary_day(itinerary, day_number, note):
    if not itinerary or "plan" not in itinerary:
        return {
            "success": False,
            "error": "No existing itinerary found to revise. Create a trip first.",
        }

    plan = itinerary["plan"]
    target_day = None

    for day in plan:
        if day.get("day") == day_number:
            day["note"] = note
            target_day = day
            break

    if target_day is None:
        return {
            "success": False,
            "error": f"Day {day_number} was not found in the current itinerary.",
        }

    itinerary["plan"] = plan

    return {
        "success": True,
        "updated_day": day_number,
        "note": note,
        "itinerary": itinerary,
    }


# -----------------------------------------
# TOOL: PREPARE EMAIL ACTION
# -----------------------------------------

def prepare_itinerary_email(recipient_email=None):
    return {
        "success": True,
        "action": "email_prepared",
        "recipient_email": recipient_email,
        "message": (
            "The itinerary is ready to email. Nothing has been sent yet. "
            "Please confirm the recipient and approve sending in the app."
        ),
    }


# -----------------------------------------
# TOOL: SEARCH PLACES
# -----------------------------------------

def search_places(city, category):
    if not GEOAPIFY_API_KEY:
        return {
            "success": False,
            "error": "GEOAPIFY_API_KEY is not set in environment variables.",
        }

    try:
        geocode_url = "https://api.geoapify.com/v1/geocode/search"
        geo_params = {"text": city, "apiKey": GEOAPIFY_API_KEY}

        geo_res = requests.get(geocode_url, params=geo_params, timeout=10)
        geo_data = geo_res.json()

        geo_features = geo_data.get("features", [])
        if not geo_features:
            return {
                "success": False,
                "error": f"Could not find coordinates for city: {city}.",
            }

        lon = geo_features[0]["geometry"]["coordinates"][0]
        lat = geo_features[0]["geometry"]["coordinates"][1]

        places_url = "https://api.geoapify.com/v2/places"
        places_params = {
            "categories": category,
            "filter": f"circle:{lon},{lat},5000",
            "limit": 5,
            "apiKey": GEOAPIFY_API_KEY,
        }

        places_res = requests.get(places_url, params=places_params, timeout=10)
        places_data = places_res.json()

        places_features = places_data.get("features")
        if places_features is None:
            return {
                "success": False,
                "error": "Places API failed or returned unexpected payload.",
            }

        clean_places = []
        for feature in places_features:
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [0, 0])
            clean_places.append(
                {
                    "name": props.get("name", "Unknown"),
                    "address": props.get("formatted", ""),
                    "latitude": coords[1],
                    "longitude": coords[0],
                }
            )

        return {
            "success": True,
            "city": city,
            "category": category,
            "places": clean_places,
        }

    except requests.RequestException as error:
        return {"success": False, "error": f"Geoapify Places API error: {error}"}