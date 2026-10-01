import os
import traceback
from flask import Flask, jsonify, render_template, request, session
from agent import run_agent
from tools import convert_currency, search_flights, send_plan_email
import mimetypes
mimetypes.add_type('model/gltf-binary', '.glb')
app = Flask(__name__)
# 1. إضافة secret_key لتفعيل الـ session في Flask
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)


def extract_places_for_map(steps):
    """يفحص خطوات التنفيذ (execution trace) ويلقط كل الأماكن الحقيقية التي

    رجعتها search_places، باش نعرضهم على خريطة تفاعلية.
    """
    places = []
    seen = set()

    for step in steps or []:
        if step.get("tool") != "search_places":
            continue

        result = step.get("result") or {}
        if not result.get("success"):
            continue

        for place in result.get("places", []):
            name = place.get("name")
            lat = place.get("latitude")
            lon = place.get("longitude")

            if not name or lat is None or lon is None:
                continue

            key = (name, round(lat, 5), round(lon, 5))
            if key in seen:
                continue
            seen.add(key)

            places.append(
                {
                    "name": name,
                    "address": place.get("address", ""),
                    "category": result.get("category", ""),
                    "lat": lat,
                    "lon": lon,
                }
            )

    return places


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/planner", methods=["GET", "POST"])
def planner():
    goal = ""
    answer = None
    steps = []
    state = None
    error = None
    places = []

    if request.method == "POST":
        goal = request.form.get("goal", "").strip()

        if not goal:
            error = "Please enter a travel goal."
        else:
            try:
                # 2. إعداد الـ context وقراءة الخطة المحفوظة من الـ session
                context = {
                    "existing_itinerary": session.get("itinerary"),
                    "trip_profile": session.get("trip_profile"),
                }

                # 3. تمرير الـ context لدالة الـ agent
                result = run_agent(goal, context=context)

                answer = result.get("answer")
                steps = result.get("steps", [])
                state = result.get("state")

                if not result.get("success"):
                    error = answer
                else:
                    # 4. حفظ الخطة الحالية وملف الرحلة في الـ session فور نجاح التوليد أو التعديل
                    if state and isinstance(state, dict):
                        if state.get("itinerary") is not None:
                            session["itinerary"] = state["itinerary"]
                        if state.get("trip_profile") is not None:
                            session["trip_profile"] = state["trip_profile"]

                        # الـ agent ما يصيفطش الإيميل بروحه. إذا نادى
                        # prepare_itinerary_email، نخزنو الطلب كـ "pending"
                        # وما يصير الإرسال إلا بعد موافقة صريحة (/approve-email).
                        pending_action = state.get("pending_action")
                        if pending_action:
                            session["pending_action"] = pending_action

                    places = extract_places_for_map(steps)

            except Exception as e:
                print("Agent error:", e)
                traceback.print_exc()
                error = (
                    "The travel agent could not complete "
                    "the request. Please try again."
                )

    return render_template(
        "index.html",
        goal=goal,
        answer=answer,
        steps=steps,
        state=state,
        error=error,
        pending_action=session.get("pending_action"),
        places=places,
    )


@app.route("/approve-email", methods=["POST"])
def approve_email():
    """الإرسال الحقيقي يصير هنا فقط، بعد ما المستخدم يضغط "Approve" فـ الواجهة.

    نتأكد أن هناك طلب pending حقيقي فـ الـ session (يعني الـ agent هو لي
    طلبها، مش أي زر عشوائي).
    """
    pending_action = session.get("pending_action")

    if not pending_action:
        return (
            jsonify(
                success=False,
                message="There is no pending email action to approve.",
            ),
            400,
        )

    data = request.get_json(silent=True) or {}

    recipient = (
        data.get("recipient_email", "").strip()
        or (pending_action.get("recipient_email") or "").strip()
    )
    image_data = data.get("image_data", "")

    result = send_plan_email(recipient, image_data)

    if result.get("success"):
        session.pop("pending_action", None)
        return jsonify(success=True, message=result.get("message"))

    return jsonify(success=False, message=result.get("error")), 400


@app.route("/cancel-email", methods=["POST"])
def cancel_email():
    session.pop("pending_action", None)
    return jsonify(success=True, message="Email action cancelled.")


# ============================================
# NEW ENDPOINT: DIRECT SAVE & SHARE
# Lets the user email the currently displayed plan at any
# time, without needing the agent to first call
# prepare_itinerary_email. No session pending_action required.
# ============================================
@app.route("/send-plan-direct", methods=["POST"])
def send_plan_direct():
    data = request.get_json(silent=True) or {}

    recipient = (data.get("recipient_email") or "").strip()
    image_data = data.get("image_data", "")

    result = send_plan_email(recipient, image_data)

    if result.get("success"):
        return jsonify(success=True, message=result.get("message"))

    return jsonify(success=False, message=result.get("error")), 400


# ============================================
# NEW ENDPOINT: STANDALONE FLIGHT AVAILABILITY (7-day check)
# Direct, deterministic — does NOT go through the LLM agent.
# Just origin + destination -> real available dates.
# ============================================
@app.route("/api/flight-availability", methods=["POST"])
def api_flight_availability():
    from tools import search_flights_range

    data = request.get_json(silent=True) or {}

    origin = (data.get("origin") or "").strip().upper()
    destination = (data.get("destination") or "").strip().upper()
    days_ahead = data.get("days_ahead", 7)

    if not origin or not destination:
        return (
            jsonify(success=False, error="Please enter both origin and destination airport codes."),
            400,
        )

    try:
        days_ahead = int(days_ahead)
    except (TypeError, ValueError):
        days_ahead = 7

    days_ahead = max(1, min(days_ahead, 14))

    result = search_flights_range(
        origin=origin,
        destination=destination,
        days_ahead=days_ahead,
    )

    if result.get("success"):
        return jsonify(result)

    return jsonify(success=False, error=result.get("error", "No flights found.")), 400


@app.route("/api/convert", methods=["POST"])
def api_convert():
    """Endpoint خفيف يستعمله ودجت 'تحويل العملة' فـ الواجهة مباشرة، بلا ما يمر عبر

    الـ LLM agent — أسرع وأرخص لتحويل بسيط.
    """
    data = request.get_json(silent=True) or {}

    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify(success=False, error="Invalid amount."), 400

    from_currency = (data.get("from_currency") or "").strip()
    to_currency = (data.get("to_currency") or "").strip()

    if not from_currency or not to_currency:
        return jsonify(success=False, error="Missing currency codes."), 400

    result = convert_currency(amount, from_currency, to_currency)

    if result.get("success"):
        return jsonify(result)

    return (
        jsonify(
            success=False, error=result.get("error", "Conversion failed.")
        ),
        400,
    )


# ================= ==========================
# NEW ENDPOINT: FLIGHT SEARCH API
# ============================================
@app.route("/api/search-flights", methods=["POST"])
def api_search_flights():
    """Endpoint مخصص للبحث المباشر عن الرحلات الجوية من واجهة المستخدم."""
    data = request.get_json(silent=True) or {}

    origin = data.get("origin", "AMM").strip().upper()
    destination = data.get("destination", "IST").strip().upper()
    departure_date = data.get("departure_date")
    cabin_class = data.get("cabin_class", "economy")
    adults = data.get("adults", 1)

    if not departure_date:
        return (
            jsonify({"success": False, "error": "يرجى تحديد تاريخ المغادرة"}),
            400,
        )

    try:
        adults = int(adults)
    except (TypeError, ValueError):
        adults = 1

    result = search_flights(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        cabin_class=cabin_class,
        adults=adults,
    )

    if result.get("success"):
        return jsonify(result)

    return (
        jsonify(
            success=False,
            error=result.get("error", "Failed to retrieve flights."),
        ),
        400,
    )


if __name__ == "__main__":
    app.run(debug=True)