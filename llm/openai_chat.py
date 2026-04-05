import os

try:
    import openai
except ImportError:
    openai = None


def get_openai_api_key():
    return os.getenv('OPENAI_API_KEY')


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


def ask_openai(message, plan=None, history=None):
    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable is not set.')
    if openai is None:
        raise RuntimeError('The openai package is not installed. Install it with pip install openai.')

    openai.api_key = api_key

    messages = [
        {
            'role': 'system',
            'content': (
                'You are a helpful travel assistant. Answer the user clearly and politely. '
                'When travel plan context is available, use it to answer questions about the itinerary, budget, transport, weather, and attractions.'
            )
        }
    ]

    plan_context = build_plan_context(plan)
    if plan_context:
        messages.append({
            'role': 'system',
            'content': f'Here is the current trip plan context:\n{plan_context}'
        })

    if history:
        messages.extend(history)

    messages.append({'role': 'user', 'content': message})

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        temperature=0.7,
        max_tokens=500,
        n=1,
    )

    return response.choices[0].message.content.strip()
