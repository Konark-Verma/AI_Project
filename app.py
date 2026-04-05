try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import re

from flask import Flask, render_template, request, jsonify
from agents.travel_agent import plan_trip
from llm.gemini_chat import ask_gemini, detect_trip_replan_intent, generate_replan_reply, detect_trip_replan_intent, generate_replan_reply

app = Flask(__name__)


def extract_trip_details(message):
    lower = message.lower().strip()
    details = {}

    source_destination = re.search(r'from\s+([a-zA-Z ]+?)\s+to\s+([a-zA-Z ]+?)(?:\.|,|$)', lower)
    if source_destination:
        details['source'] = source_destination.group(1).strip().title()
        details['destination'] = source_destination.group(2).strip().title()
    else:
        simple_route = re.search(r'([a-zA-Z ]+?)\s+to\s+([a-zA-Z ]+?)(?:\.|,|$)', lower)
        if simple_route:
            details['source'] = simple_route.group(1).strip().title()
            details['destination'] = simple_route.group(2).strip().title()

    if 'days' not in details:
        days_match = re.search(r'(\d+)\s*(?:days|day)', lower)
        if days_match:
            details['days'] = int(days_match.group(1))

    if 'travelers' not in details:
        travelers_match = re.search(r'(\d+)\s*(?:travelers|traveller|people|persons|guests)', lower)
        if travelers_match:
            details['travelers'] = int(travelers_match.group(1))

    if 'budget' not in details:
        budget_match = re.search(r'₹\s*([\d,]+(?:\.\d+)?)', lower) or re.search(r'([\d,]+(?:\.\d+)?)\s*(?:inr|rs|rupees)', lower)
        if budget_match:
            details['budget'] = float(budget_match.group(1).replace(',', ''))

    if 'travel_type' not in details:
        details['travel_type'] = 'international' if 'international' in lower else 'city'

    return details


def normalize_trip_payload(trip):
    """Validate trip dict from the client for replanning."""
    if not trip or not isinstance(trip, dict):
        return None
    try:
        source = str(trip.get('source', '')).strip()
        destination = str(trip.get('destination', '')).strip()
        if not source or not destination:
            return None
        budget = float(trip.get('budget'))
        travelers = int(trip.get('travelers'))
        days = int(trip.get('days'))
        travel_type = str(trip.get('travel_type', 'city')).lower()
        if travel_type == 'state':
            travel_type = 'city'
        if travel_type not in ('city', 'international'):
            travel_type = 'city'
        return {
            'source': source,
            'destination': destination,
            'budget': budget,
            'travelers': travelers,
            'days': days,
            'travel_type': travel_type,
        }
    except (TypeError, ValueError):
        return None


def merge_trip_params(base, changes):
    """Apply intent `changes` onto validated trip params."""
    out = dict(base)
    if not changes:
        return out
    if changes.get('budget') is not None:
        out['budget'] = float(changes['budget'])
    if changes.get('travelers') is not None:
        out['travelers'] = int(changes['travelers'])
    if changes.get('days') is not None:
        out['days'] = int(changes['days'])
    if changes.get('travel_type') is not None:
        tt = str(changes['travel_type']).lower()
        if tt in ('city', 'international'):
            out['travel_type'] = tt
    if changes.get('transport') is not None:
        t = str(changes['transport']).strip().title()
        if t in ('Flight', 'Train', 'Bus', 'Cab'):
            out['transport'] = t
    return out


def build_chat_summary(plan):
    budget_text = plan.get('budget_plan', 'No budget data available.').split('\n')[0]
    summary_lines = [
        f"I created a {plan.get('travel_type', 'city').title()} travel plan from {plan['route'][0]} to {plan['route'][-1]}.",
        f"Mode: {plan.get('transport', 'N/A')}, Distance: {plan.get('distance', 'N/A')} km.",
        f"Budget guidance: {budget_text}",
        'Itinerary preview:'
    ]

    if plan.get('itinerary'):
        preview = plan['itinerary'][:3]
        summary_lines.extend([f"- {item}" for item in preview])

    return '\n'.join(summary_lines)


def format_list(items, limit=5):
    if not items:
        return 'No details available.'
    return ', '.join([str(item) for item in items[:limit]])


def answer_chat_question(message, plan):
    lower = message.lower()

    if any(token in lower for token in ['budget', 'cost', 'price', 'expense', 'spend']):
        return plan.get('budget_plan', 'Budget details are not available for this trip.')

    if any(token in lower for token in ['transport', 'flight', 'train', 'bus', 'mode']):
        answer = f"Recommended transport: {plan.get('transport', 'N/A')}."
        if plan.get('transport') == 'Flight' and plan.get('flights'):
            flights = plan['flights']
            answer += f" Estimated price: {flights.get('price', 'N/A')}. Duration: {flights.get('duration_range', flights.get('duration', 'Varies'))}."
        elif plan.get('transport') == 'Train' and plan.get('train'):
            train = plan['train']
            answer += f" Estimated price: {train.get('price', 'N/A')}. Duration: {train.get('duration_range', 'Varies')}."
        return answer

    if any(token in lower for token in ['weather', 'temperature', 'rain', 'sunny', 'forecast']):
        weather = plan.get('weather', {})
        if isinstance(weather, dict):
            return f"Estimated weather: {weather.get('temperature', 'N/A')}, {weather.get('weather', 'N/A')}, humidity {weather.get('humidity', 'N/A')} ."
        return str(weather)

    if any(token in lower for token in ['place', 'attraction', 'sight', 'visit', 'things to do']):
        places = plan.get('places', [])
        place_names = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in places]
        return f"Top attractions: {format_list(place_names, limit=6)}."

    if any(token in lower for token in ['itinerary', 'day', 'schedule', 'plan']):
        itinerary = plan.get('itinerary') or []
        if itinerary:
            return 'Trip itinerary:\n' + '\n'.join(itinerary[:min(len(itinerary), 6)])
        return 'I do not have itinerary details for this trip.'

    if any(token in lower for token in ['route', 'distance', 'stop', 'waypoint']):
        route = plan.get('route', [])
        distance = plan.get('distance', 'N/A')
        if route:
            return f"The route is: {' → '.join(route)}. Total distance is {distance} km."
        return 'Route information is unavailable.'

    if any(token in lower for token in ['visa', 'documents', 'passport', 'exchange']):
        if plan.get('travel_type', 'city') == 'international':
            return 'For international travel, carry a valid passport, check visa requirements, and allow extra time for currency exchange and documentation.'
        return 'For city travel, carry local ID, booking confirmation, and local payment options.'

    return 'I can answer questions about your budget, transport, itinerary, weather, attractions, or route for this trip. Ask me something specific.'


@app.route("/")
def home():
    return render_template("travel_type.html")


@app.route("/search")
def search():
    return render_template("index.html")


@app.route("/result")
def result():
    return render_template("result.html")


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/chat_api", methods=["POST"])
def chat_api():
    request_data = request.json or {}
    message = request_data.get('message', '').strip()
    if not message:
        return jsonify({"reply": "Please send a message so I can help you with your trip."})

    plan = request_data.get('plan')
    trip_payload = normalize_trip_payload(request_data.get('trip'))

    if plan and trip_payload:
        intent = None
        try:
            intent = detect_trip_replan_intent(message, plan=plan, trip_context=trip_payload)
        except Exception:
            intent = None

        if intent and intent.get('needs_replan') and intent.get('changes'):
            merged = merge_trip_params(trip_payload, intent['changes'])
            forced_transport = intent['changes'].get('transport')
            try:
                new_plan = plan_trip(
                    merged['source'],
                    merged['destination'],
                    merged['budget'],
                    merged['travelers'],
                    merged['days'],
                    travel_type=merged.get('travel_type', 'city'),
                    forced_transport=forced_transport,
                )
                reply = generate_replan_reply(message, plan, new_plan, intent['changes'])
                return jsonify({
                    'reply': reply,
                    'replanned': True,
                    'plan': new_plan,
                    'previous_plan': plan,
                    'trip': merged,
                    'applied_changes': intent['changes'],
                })
            except Exception:
                pass

    # Try Gemini first if available
    if plan:
        try:
            answer = ask_gemini(message, plan=plan)
            return jsonify({'reply': answer})
        except Exception as e:
            # Fallback to built-in trip Q&A
            answer = answer_chat_question(message, plan)
            return jsonify({'reply': answer})
    
    # For non-trip questions, try Gemini
    try:
        answer = ask_gemini(message)
        return jsonify({'reply': answer})
    except Exception as gemini_error:
        # Fallback: try to extract trip details and generate plan
        details = extract_trip_details(message)
        if details.get('source') and details.get('destination') and details.get('travelers') and details.get('budget') and details.get('days'):
            plan = plan_trip(
                details['source'],
                details['destination'],
                details['budget'],
                details['travelers'],
                details['days'],
                travel_type=details.get('travel_type', 'city')
            )
            summary = build_chat_summary(plan)
            return jsonify({
                'reply': summary,
                'plan': plan,
                'trip': {
                    'source': details['source'],
                    'destination': details['destination'],
                    'travelers': details['travelers'],
                    'budget': details['budget'],
                    'days': details['days'],
                    'travel_type': details.get('travel_type', 'city')
                }
            })

        return jsonify({
            'reply': 'I can help answer travel questions or create a travel plan. Try asking about a destination or mentioning a trip you want to plan.'
        })


@app.route("/plan", methods=["POST"])
def plan():

    data = request.json

    source = data["source"]
    destination = data["destination"]
    travelers = int(data["travelers"])
    budget = float(data["budget"])
    days = int(data["days"])
    travel_type = data.get("travelType", "city")
    # 'state' travel option was removed; normalize any legacy value.
    travel_type = str(travel_type).lower()
    if travel_type == "state":
        travel_type = "city"
    if travel_type not in ("city", "international"):
        travel_type = "city"

    result = plan_trip(source,destination,budget,travelers,days, travel_type)

    return jsonify(result)

if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True)