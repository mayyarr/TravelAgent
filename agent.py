import json
import os
from datetime import date

from groq import Groq

from tools import (
    calculate_daily_budget,
    convert_currency,
    create_trip_plan,
    get_route,
    get_weather,
    prepare_itinerary_email,
    revise_itinerary_day,
    search_flights,
    search_flights_range,
    search_places,
)

# -----------------------------------------
# CHECK API KEY
# -----------------------------------------

if "GROQ_API_KEY" not in os.environ:
    raise RuntimeError(
        "GROQ_API_KEY is not set in the operating system environment."
    )

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def extract_trip_profile(user_goal):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
            Extract travel information from the user's message.
            Return JSON only with these fields:
            destination
            origin
            days
            budget
            currency
            interests
            work_days
            work_start_time
            work_end_time
            food_preferences
            avoid
            Use null when information is missing.
            Use [] when interests, work_days, food_preferences, or avoid are missing.
            Budget means the total trip budget.
            origin means the traveler's departure city or airport, if mentioned.
            Do not guess missing information.
            """,
            },
            {"role": "user", "content": user_goal},
        ],
    )
    content = response.choices[0].message.content
    return _parse_json_safely(content, context="trip profile extraction")


def _parse_json_safely(content, context="model response"):
    """
    Groq's JSON mode is normally reliable, but this makes parsing
    resilient to stray markdown fences or leading/trailing text so a
    formatting quirk doesn't crash the whole agent run.
    """
    if content is None:
        raise RuntimeError(f"Empty {context}: the model returned no content.")

    text = content.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise RuntimeError(
            f"Could not parse {context} as JSON. Raw content: {content[:500]!r}"
        )


def validate_trip_profile(trip):
    missing = []
    errors = []

    if not isinstance(trip, dict):
        return {
            "valid": False,
            "missing": [],
            "errors": [
                "The trip information could not be understood. Please rephrase your goal."
            ],
        }

    # The model sometimes returns numbers as strings (e.g. "5" instead of 5).
    for numeric_field in ("days", "budget"):
        value = trip.get(numeric_field)
        if isinstance(value, str):
            try:
                trip[numeric_field] = (
                    float(value) if "." in value else int(value)
                )
            except ValueError:
                trip[numeric_field] = None

    if trip.get("destination") is None:
        missing.append("destination")
    if trip.get("days") is None:
        missing.append("days")
    elif trip["days"] <= 0:
        errors.append("Days must be greater than zero.")
    if trip.get("budget") is None:
        missing.append("budget")
    elif trip["budget"] <= 0:
        errors.append("Budget must be greater than zero.")
    if trip.get("currency") is None:
        missing.append("currency")
    if trip.get("interests") is None:
        missing.append("interests")
    if trip.get("work_days") is None:
        missing.append("work_days")
    if trip.get("work_start_time") is None:
        missing.append("work_start_time")
    if trip.get("work_end_time") is None:
        missing.append("work_end_time")
    if trip.get("food_preferences") is None:
        missing.append("food_preferences")
    if trip.get("avoid") is None:
        missing.append("avoid")

    # NOTE: origin is intentionally NOT added to "missing". If the user
    # didn't mention a departure city, the agent falls back to a sensible
    # default (see system prompt) instead of blocking the whole plan on it.

    return {
        "valid": len(missing) == 0 and len(errors) == 0,
        "missing": missing,
        "errors": errors,
    }


# -----------------------------------------
# TOOL DEFINITIONS FOR THE AI
# -----------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": (
                "Search for available flights between two airports "
                "on a single specific date, returning price, cabin class, "
                "airline, and timing for each offer. Use this only when "
                "the user gave an exact departure date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin airport IATA code, for example AMM",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination airport IATA code, for example IST",
                    },
                    "departure_date": {
                        "type": "string",
                        "description": "Departure date in YYYY-MM-DD format",
                    },
                    "cabin_class": {
                        "type": "string",
                        "description": "Cabin class: economy, premium_economy, business, or first",
                        "enum": [
                            "economy",
                            "premium_economy",
                            "business",
                            "first",
                        ],
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adult passengers",
                    },
                },
                "required": ["origin", "destination", "departure_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_flights_range",
            "description": (
                "Check REAL flight availability across multiple upcoming "
                "days when the user did NOT give an exact departure date. "
                "Calls the flight search API once per day and returns only "
                "the dates where real offers were found, with price, "
                "airline, and timing. Use this instead of asking the user "
                "for a date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin airport IATA code, for example AMM",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination airport IATA code, for example IST",
                    },
                    "start_date": {
                        "type": "string",
                        "description": (
                            "Start date in YYYY-MM-DD format. Defaults to "
                            "today if omitted."
                        ),
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "How many upcoming days to check, default 7",
                    },
                    "cabin_class": {
                        "type": "string",
                        "enum": [
                            "economy",
                            "premium_economy",
                            "business",
                            "first",
                        ],
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adult passengers",
                    },
                },
                "required": ["origin", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, for example Istanbul",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert money from one currency to another.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The amount of money to convert",
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code such as JOD",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code such as TRY",
                    },
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_daily_budget",
            "description": (
                "Calculate how much money the traveler "
                "can spend per day."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "total_budget": {
                        "type": "number",
                        "description": "The traveler's total budget",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of travel days",
                    },
                },
                "required": ["total_budget", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_trip_plan",
            "description": (
                "Create a simple day-by-day trip structure "
                "using destination, number of days, budget, "
                "work days, and traveler interests."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "Travel destination, for example Istanbul",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Total number of trip days",
                    },
                    "total_budget": {
                        "type": "number",
                        "description": "Total trip budget",
                    },
                    "work_days": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": (
                            "Trip day numbers that are work days, "
                            "for example [2, 3]"
                        ),
                    },
                    "interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Traveler interests such as history, "
                            "food, museums, or shopping"
                        ),
                    },
                    "work_start": {
                        "type": "string",
                        "description": "Work start time",
                    },
                    "work_end": {
                        "type": "string",
                        "description": "Work end time",
                    },
                    "avoid": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Things the traveler wants to avoid",
                    },
                },
                "required": [
                    "destination",
                    "days",
                    "total_budget",
                    "work_days",
                    "interests",
                    "work_start",
                    "work_end",
                    "avoid",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_route",
            "description": (
                "Calculate travel distance and travel time in minutes between two geographic coordinates (latitude and longitude)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "from_lat": {
                        "type": "number",
                        "description": "Latitude of the starting location",
                    },
                    "from_lon": {
                        "type": "number",
                        "description": "Longitude of the starting location",
                    },
                    "to_lat": {
                        "type": "number",
                        "description": "Latitude of the destination location",
                    },
                    "to_lon": {
                        "type": "number",
                        "description": "Longitude of the destination location",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Travel mode, default is 'walk'",
                        "enum": ["walk", "drive", "bicycle"],
                    },
                },
                "required": ["from_lat", "from_lon", "to_lat", "to_lon"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_places",
            "description": "Search for real tourist attractions, museums, cafes, and restaurants in a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city to search in, for example Istanbul",
                    },
                    "category": {
                        "type": "string",
                        "description": "The place category",
                        "enum": [
                            "tourism.attraction",
                            "entertainment.museum",
                            "catering.cafe",
                            "catering.restaurant",
                        ],
                    },
                },
                "required": ["city", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "revise_itinerary_day",
            "description": (
                "Update a single day of the traveler's already-saved itinerary "
                "without rebuilding the other days. Use this when the user refers "
                "to an existing trip and asks to change, remove, or replace "
                "something on a specific day (for example: 'remove the museum "
                "from day 1' or 'change day 2 to something with coffee')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "day_number": {
                        "type": "integer",
                        "description": "Which day of the itinerary to change, for example 2",
                    },
                    "note": {
                        "type": "string",
                        "description": (
                            "Plain description of the requested change for that day, "
                            "for example 'Remove the museum, replace with a coffee café'"
                        ),
                    },
                },
                "required": ["day_number", "note"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_itinerary_email",
            "description": (
                "Stage an action to email the current itinerary to the traveler. "
                "This does NOT send anything. It only prepares the action so the "
                "user can review it and click Approve in the interface."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_email": {
                        "type": "string",
                        "description": "The email address the user wants the itinerary sent to, if mentioned",
                    }
                },
                "required": [],
            },
        },
    },
]


def execute_tool(tool_name, arguments, context=None):
    if context is None:
        context = {}

    if tool_name == "get_weather":
        return get_weather(city=arguments["city"])

    elif tool_name == "convert_currency":
        return convert_currency(
            amount=arguments["amount"],
            from_currency=arguments["from_currency"],
            to_currency=arguments["to_currency"],
        )

    elif tool_name == "calculate_daily_budget":
        return calculate_daily_budget(
            total_budget=arguments["total_budget"], days=arguments["days"]
        )

    elif tool_name == "create_trip_plan":
        return create_trip_plan(
            destination=arguments["destination"],
            days=arguments["days"],
            total_budget=arguments["total_budget"],
            work_days=arguments["work_days"],
            interests=arguments["interests"],
            work_start=arguments["work_start"],
            work_end=arguments["work_end"],
            avoid=arguments["avoid"],
        )

    elif tool_name == "search_flights":
        return search_flights(
            origin=arguments["origin"],
            destination=arguments["destination"],
            departure_date=arguments["departure_date"],
            cabin_class=arguments.get("cabin_class", "economy"),
            adults=arguments.get("adults", 1),
        )

    elif tool_name == "search_flights_range":
        return search_flights_range(
            origin=arguments["origin"],
            destination=arguments["destination"],
            start_date=arguments.get("start_date"),
            days_ahead=arguments.get("days_ahead", 7),
            cabin_class=arguments.get("cabin_class", "economy"),
            adults=arguments.get("adults", 1),
        )

    elif tool_name == "get_route":
        return get_route(
            from_lat=arguments["from_lat"],
            from_lon=arguments["from_lon"],
            to_lat=arguments["to_lat"],
            to_lon=arguments["to_lon"],
            mode=arguments.get("mode", "walk"),
        )

    elif tool_name == "search_places":
        return search_places(
            city=arguments["city"], category=arguments["category"]
        )

    elif tool_name == "revise_itinerary_day":
        return revise_itinerary_day(
            itinerary=(context or {}).get("existing_itinerary"),
            day_number=arguments["day_number"],
            note=arguments["note"],
        )

    elif tool_name == "prepare_itinerary_email":
        return prepare_itinerary_email(
            recipient_email=arguments.get("recipient_email")
        )

    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}


# -----------------------------------------
# AGENT LOOP
# -----------------------------------------
def run_agent(user_goal, context=None):
    trip_profile = extract_trip_profile(user_goal)
    validation = validate_trip_profile(trip_profile)

    context = context or {}
    existing_itinerary = context.get("existing_itinerary")

    tool_context = {"existing_itinerary": existing_itinerary}

    state = {
        "goal": user_goal,
        "trip_profile": trip_profile,
        "validation": validation,
        "status": "running",
        "iteration": 0,
        "tools_used": [],
        "steps": [],
        "final_answer": None,
        "itinerary": existing_itinerary,
        "pending_action": None,
    }

    today_str = date.today().isoformat()

    messages = [
        {
            "role": "system",
            "content": f"""
You are an intelligent travel assistant.

Today's date is {today_str}.

Your job is to help the user accomplish a travel goal.

You have access to tools.

Use tools whenever they are necessary.

Rules:

1. Never invent flight availability or prices. Use search_flights or search_flights_range.
2. Never invent current weather. Use get_weather.
3. Never invent exchange rates. Use convert_currency.
4. Use calculate_daily_budget when the user wants to understand a budget across several days.
5. Use create_trip_plan when the user wants a day-by-day trip structure.
6. You may use more than one tool.
7. After receiving tool results, decide whether another tool is required.
8. When enough information is available, provide a clear final answer.
9. When presenting flight results from search_flights, ALWAYS format them as a markdown table with column headers matching the answer's language (see rule 17): Arabic → | شركة الطيران | السعر | المغادرة | الوصول | التوقفات |، English → | Airline | Price | Departure | Arrival | Stops |
10. Use get_route to calculate travel distance and time between coordinates of places.
11. Show travel time in the itinerary (e.g., 'Travel: 18 minutes walking').
12. If walking travel time exceeds 60 minutes between two locations, warn the user that the places may be too far apart for a convenient walking plan.

13. If the user refers to an existing trip (e.g. "change day 2", "remove the museum"),
    and an existing itinerary is provided below, use revise_itinerary_day instead of
    rebuilding the whole trip with create_trip_plan.
14. If the user asks to email or send the itinerary, use prepare_itinerary_email.
    NEVER claim an email was sent — prepare_itinerary_email only stages the action for
    human approval in the UI. Actual sending happens outside your control.

15. If the user wants flight information but did NOT give an exact departure
    date, do NOT ask them to provide one. Instead, call search_flights_range
    starting from today ({today_str}) for the next 7 days. If the user did
    not mention a departure city/airport either, assume "AMM" (Amman) as a
    reasonable default and clearly tell the user this was assumed so they
    can correct it if needed.
16. When presenting search_flights_range results, format them as a markdown
    table with column headers matching the answer's language (see rule 17):
    Arabic → | التاريخ | شركة الطيران | السعر | المغادرة | الوصول | التوقفات |
    English → | Date | Airline | Price | Departure | Arrival | Stops |
    Only include rows for dates where real offers were actually returned.
    Never invent a date, airline, price, or time that wasn't in the tool result.
17. Detect the language the user's goal (the message below) is written in,
    and ALWAYS write your final natural-language answer in that SAME
    language — if the goal is in Arabic, answer in Arabic; if it's in
    English, answer in English; if it's in another language, use that
    language. This applies only to the prose you write for the user — keep
    tool arguments (city names, currency codes like TRY/JOD, airport codes,
    dates) in their normal format. Match markdown table headers to the same
    language: use "| شركة الطيران | السعر | المغادرة | الوصول | التوقفات |"
    for an Arabic answer, or "| Airline | Price | Departure | Arrival | Stops |"
    for an English answer (and likewise for the search_flights_range table).

STRUCTURED TRIP INFORMATION
 
Trip Profile:
{json.dumps(trip_profile)}
 
Validation:
{json.dumps(validation)}

Existing itinerary (may be null if none was created yet):
{json.dumps(existing_itinerary)}
 
Use the structured trip information when deciding what to do.
Do not invent missing information.
If important information is missing or invalid, ask the user to provide or correct it.
Only require information that is necessary for the user's current request.
""",
        },
        {"role": "user", "content": user_goal},
    ]

    max_iterations = 6

    for iteration in range(max_iterations):
        state["iteration"] = iteration + 1

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            reasoning_effort="low",
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        if not assistant_message.tool_calls:
            state["status"] = "completed"
            state["final_answer"] = assistant_message.content

            return {
                "success": True,
                "answer": state["final_answer"],
                "steps": state["steps"],
                "state": state,
            }

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments)
                result = execute_tool(
                    tool_name, arguments, context=tool_context
                )
            except Exception as error:
                result = {"success": False, "error": str(error)}

            if tool_name not in state["tools_used"]:
                state["tools_used"].append(tool_name)

            # PERSIST TRIP STATE BASED ON TOOL RESULTS
            if isinstance(result, dict) and result.get("success"):
                if tool_name == "create_trip_plan":
                    state["itinerary"] = result
                    tool_context["existing_itinerary"] = result

                elif tool_name == "revise_itinerary_day":
                    updated_itinerary = result.get("itinerary")
                    if updated_itinerary:
                        state["itinerary"] = updated_itinerary
                        tool_context["existing_itinerary"] = updated_itinerary

                elif tool_name == "prepare_itinerary_email":
                    state["pending_action"] = {
                        "type": "email",
                        "recipient_email": result.get("recipient_email"),
                        "message": result.get("message"),
                    }

            step = {
                "step": len(state["steps"]) + 1,
                "iteration": state["iteration"],
                "tool": tool_name,
                "arguments": arguments,
                "result": result,
            }

            state["steps"].append(step)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result),
                }
            )

    state["status"] = "stopped"
    state["final_answer"] = (
        "The agent reached the maximum number of iterations."
    )

    return {
        "success": False,
        "answer": state["final_answer"],
        "steps": state["steps"],
        "state": state,
    }