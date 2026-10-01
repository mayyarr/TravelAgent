# ✈️ Agentic Travel Assistant

An AI travel agent that turns a single message like *"5 days in Istanbul, 800 USD budget, I love food and history, I work Mon–Wed 9–5"* into a complete, day-by-day trip plan.

The agent understands your goal, picks the right tools by itself (weather, flights, places, routes, budget, currency), builds the itinerary around your work hours and preferences, and lets you revise any day or email the final plan.

## Features

- **Natural-language trip planning**: extracts destination, origin, days, budget, interests, food preferences, work schedule, and things to avoid
- **Agentic tool use**: the LLM decides which tools to call and in what order
- **Live weather** for the destination (Open-Meteo)
- **Flight search** with a date-range availability view (Duffel API, with mock offers as fallback)
- **Places & routes**: attractions, restaurants, and walking/driving routes on a map (Geoapify)
- **Budget tools**: daily budget split and live currency conversion
- **Revise a single day** with a short note ("make day 3 more relaxed")
- **Email the plan** after user approval (Gmail SMTP)

## Tools

| Tool | What it does |
|---|---|
| `get_weather` | Forecast for the destination |
| `search_flights` / `search_flights_range` | Flight offers for a date or a range of dates |
| `search_places` | Attractions, restaurants, cafés… by category |
| `get_route` | Route and travel time between two places |
| `calculate_daily_budget` | Splits the total budget per day |
| `convert_currency` | Live exchange rates |
| `create_trip_plan` | Builds the day-by-day itinerary |
| `revise_itinerary_day` | Rewrites one day based on feedback |
| `prepare_itinerary_email` | Prepares the plan to be emailed |

## Tech stack

Python · Flask · Groq (`openai/gpt-oss-20b`) · Open-Meteo · Geoapify · Duffel · ExchangeRate API · HTML/CSS/JS

## Getting started

```bash
git clone https://github.com/mayyarr/TravelAgent.git
cd TravelAgent
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

Set your environment variables (never commit keys):

```powershell
$env:GROQ_API_KEY="your_groq_key"
$env:GEOAPIFY_API_KEY="your_geoapify_key"
# optional
$env:DUFFEL_API_KEY="your_duffel_key"
$env:EMAIL_ADDRESS="you@gmail.com"
$env:EMAIL_APP_PASSWORD="your_gmail_app_password"
```

Run:

```bash
python app.py
```

Open http://127.0.0.1:5000

## Project structure

```
app.py        Flask routes (planner, flights, currency, email approval)
agent.py      the agent: trip profile extraction, tool selection, planning loop
tools.py      all tool implementations and external API calls
templates/    landing page and planner UI
static/       front-end JS and styles
```

## Author

Mayar Husam Mohammad
