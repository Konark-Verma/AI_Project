import json
import os
import re

try:
    import google.generativeai as genai
except ImportError:
    genai = None

VALID_TRANSPORTS = frozenset({'Flight', 'Train', 'Bus', 'Cab'})
VALID_TRAVEL_TYPES = frozenset({'city', 'international'})


def get_gemini_api_key():
    return os.environ.get('GEMINI_API_KEY', '').strip()


def _get_model():
    if genai is None:
        raise RuntimeError('The google-generativeai package is not installed.')
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY is not set.')
    genai.configure(api_key=api_key)
    model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    last_err = None
    for model_name in model_names:
        try:
            return genai.GenerativeModel(model_name)
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f'No compatible Gemini model found: {last_err}')


def _gemini_response_text(response):
    if not response:
        return ''
    try:
        t = response.text
        if t:
            return t.strip()
    except Exception:
        pass
    try:
        parts = []
        for c in getattr(response, 'candidates', []) or []:
            for p in getattr(c.content, 'parts', []) or []:
                if getattr(p, 'text', None):
                    parts.append(p.text)
        return '\n'.join(parts).strip()
    except Exception:
        return ''


def _parse_json_loose(text):
    if not text:
        return None
    text = text.strip()
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_trip_changes_from_message(message):
    message = message.lower()
    changes = {}

    if 'flight' in message:
        changes['transport'] = 'Flight'
    elif 'train' in message:
        changes['transport'] = 'Train'
    elif 'bus' in message:
        changes['transport'] = 'Bus'
    elif 'cab' in message or 'taxi' in message:
        changes['transport'] = 'Cab'

    budget_match = re.search(r'[₹$]?\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]+)?)\s*(?:inr|rs|rupees)?', message)
    if budget_match:
        value = budget_match.group(1).replace(',', '').replace(' ', '')
        try:
            num = float(value)
            if num > 0:
                changes['budget'] = num
        except ValueError:
            pass

    days_match = re.search(r'(\d+)\s*(?:days|day)', message)
    if days_match:
        changes['days'] = int(days_match.group(1))

    travelers_match = re.search(r'(\d+)\s*(?:travelers|traveller|people|persons|guests)', message)
    if travelers_match:
        changes['travelers'] = int(travelers_match.group(1))

    if 'international' in message:
        changes['travel_type'] = 'international'
    elif 'city travel' in message or 'domestic' in message or 'local' in message:
        changes['travel_type'] = 'city'

    return changes


def build_plan_context(plan):
    if not plan:
        return ''

    parts = [
        f"Trip type: {plan.get('travel_type', 'city')}",
        f"Route: {' → '.join(plan.get('route', []))}",
        f"Transport: {plan.get('transport', 'N/A')}",
        f"Distance: {plan.get('distance', 'N/A')} km",
        f"Budget plan: {plan.get('budget_plan', 'N/A')}",
    ]

    if plan.get('itinerary'):
        parts.append('Itinerary: ' + ' | '.join(plan.get('itinerary', [])[:6]))

    if plan.get('places'):
        places = [p.get('name') if isinstance(p, dict) else str(p) for p in plan.get('places', [])]
        parts.append('Top attractions: ' + ', '.join(places[:6]))

    if plan.get('weather'):
        weather = plan.get('weather')
        if isinstance(weather, dict):
            parts.append(f"Weather: {weather.get('temperature', 'N/A')}, {weather.get('weather', 'N/A')}")
        else:
            parts.append(f"Weather: {weather}")

    return '\n'.join(parts)


def normalize_intent_payload(raw):
    """Validate and normalize intent JSON from the model."""
    if not isinstance(raw, dict):
        return {'needs_replan': False, 'changes': {}, 'explanation': ''}

    needs = bool(raw.get('needs_replan'))
    changes = raw.get('changes') or {}
    if not isinstance(changes, dict):
        changes = {}

    out = {}
    t = changes.get('transport')
    if t is not None and str(t).strip():
        cap = str(t).strip().title()
        if cap.lower() == 'cab':
            cap = 'Cab'
        if cap in VALID_TRANSPORTS:
            out['transport'] = cap

    for key, cast in (
        ('budget', float),
        ('travelers', int),
        ('days', int),
    ):
        v = changes.get(key)
        if v is None:
            continue
        try:
            if key == 'budget':
                out[key] = float(v)
            else:
                out[key] = int(v)
        except (TypeError, ValueError):
            pass

    tt = changes.get('travel_type')
    if tt is not None:
        s = str(tt).strip().lower()
        if s in VALID_TRAVEL_TYPES:
            out['travel_type'] = s

    explanation = str(raw.get('explanation', '') or '')[:500]
    if needs and not out:
        needs = False
    return {'needs_replan': needs, 'changes': out, 'explanation': explanation}


def detect_trip_replan_intent(message, plan=None, trip_context=None):
    """
    Use Gemini to decide if the user wants to change assumptions and re-run the planner.
    Returns dict: needs_replan (bool), changes (dict), explanation (str).
    """
    model = _get_model()
    plan_context = build_plan_context(plan) if plan else ''
    trip_line = ''
    if trip_context:
        trip_line = (
            f"\nCurrent trip parameters: source={trip_context.get('source')}, "
            f"destination={trip_context.get('destination')}, budget={trip_context.get('budget')}, "
            f"travelers={trip_context.get('travelers')}, days={trip_context.get('days')}, "
            f"travel_type={trip_context.get('travel_type', 'city')}."
        )

    prompt = f"""You analyze messages about an existing travel plan.
Return ONLY a JSON object (no markdown) with this exact shape:
{{
  "needs_replan": boolean,
  "changes": {{
    "transport": null or one of "Flight","Train","Bus","Cab",
    "budget": null or number,
    "travelers": null or integer,
    "days": null or integer,
    "travel_type": null or "city" or "international"
  }},
  "explanation": "short reason"
}}

Rules:
- Set needs_replan true when the user asks to see a different scenario that requires recalculating the plan or costs: different transport (e.g. "how much for flight?", "by train"), new budget ("what if ₹100000?"), fewer/more days, more travelers, or switching domestic vs international.
- Set needs_replan false for thanks, greetings, or questions answerable from the current plan without replanning (e.g. "what is the weather?" if already in context — still false if they only want a verbal answer; use false unless they imply different inputs).
- Extract numbers from phrases like ₹1,00,000 or 100000 INR.
- If unsure, prefer needs_replan false.

Plan context:
{plan_context or '(none)'}
{trip_line}

User message: {message.strip()}
"""

    gen_config = None
    try:
        gen_config = genai.types.GenerationConfig(response_mime_type='application/json')
    except Exception:
        gen_config = None

    if gen_config:
        response = model.generate_content(prompt, generation_config=gen_config)
    else:
        response = model.generate_content(prompt)
    text = _gemini_response_text(response)
    parsed = _parse_json_loose(text)
    if parsed is None:
        parsed = {'needs_replan': False, 'changes': {}, 'explanation': 'parse_failed'}

    intent = normalize_intent_payload(parsed)
    if not intent['needs_replan'] and not intent['changes']:
        fallback_changes = extract_trip_changes_from_message(message)
        if fallback_changes:
            intent = {
                'needs_replan': True,
                'changes': fallback_changes,
                'explanation': 'fallback_detected',
            }
    return intent


def generate_replan_reply(user_message, previous_plan, new_plan, applied_changes):
    """Short natural-language summary comparing old vs new plan after replanning."""
    model = _get_model()
    prev_ctx = build_plan_context(previous_plan)
    new_ctx = build_plan_context(new_plan)
    changes_str = json.dumps(applied_changes, ensure_ascii=False)
    prompt = f"""You are a travel assistant. The trip was recalculated with new parameters.
Applied parameter changes: {changes_str}

Previous plan summary:
{prev_ctx}

New plan summary:
{new_ctx}

User asked: {user_message.strip()}

Write a concise, friendly reply (2–5 sentences) that highlights what changed, the new recommended transport if relevant, and the main budget takeaway. Do not invent numbers not present in the summaries."""

    response = model.generate_content(prompt)
    t = _gemini_response_text(response)
    return t if t else 'Here is your updated plan with the new settings.'


def ask_gemini(message, plan=None, history=None):
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY is not set.')
    if genai is None:
        raise RuntimeError('The google-generativeai package is not installed.')

    try:
        model = _get_model()

        system_prompt = (
            'You are a helpful travel assistant. Answer the user clearly and politely. '
            'When travel plan context is available, use it to answer questions about the itinerary, budget, transport, weather, and attractions.'
        )

        plan_context = build_plan_context(plan)
        if plan_context:
            system_prompt += f'\n\nHere is the current trip plan context:\n{plan_context}'

        full_message = system_prompt + '\n\nUser: ' + message

        response = model.generate_content(full_message)
        return _gemini_response_text(response)
    except Exception as e:
        raise RuntimeError(f'Gemini API error: {str(e)}')
