from services.location_service import get_coordinates, get_weather, get_currency_rate
from planning.route_planner import calculate_distance, find_route

from intelligence.transport_ml import predict_transport
from intelligence.budget_optimizer import optimize_budget
from intelligence.recommendation_engine import recommend_places

from intelligence.destination_finder import get_places
from llm.itinerary_llm import generate_itinerary
from services.flight_service import get_flight_prices, get_accommodation_estimate
from services.train_service import get_train_info


def plan_trip(source, destination, budget, travelers, days, travel_type='city', forced_transport=None):
    """Generate a travel plan.

    Args:
        source (str): starting location name
        destination (str): destination name
        budget (float): budget in INR
        travelers (int): number of people
        days (int): trip duration
        travel_type (str): 'city' or 'international'
        forced_transport (str|None): if set, use this mode instead of ML prediction (e.g. 'Flight').
    """

    src_coords = get_coordinates(source)
    dst_coords = get_coordinates(destination)

    distance = calculate_distance(src_coords, dst_coords)
    route = find_route(source, destination, distance)

    # Get coordinates for all waypoints in the route (including intermediate stops)
    waypoint_coords = []
    for city in route:
        waypoint_coords.append(get_coordinates(city))

    # Predict transport mode; pass travel_type for international handling
    if forced_transport:
        transport = forced_transport
    else:
        transport = predict_transport(distance, budget, travelers, days, travel_type)

    # adjust budget plan if international travel involves currency conversion/fees
    budget_plan = optimize_budget(
        budget,
        travelers,
        days,
        source,
        destination,
        transport=transport,
        distance_km=distance,
        travel_type=travel_type,
    )

    # add flag for international fees or visa reminders
    notes = []
    if travel_type == 'international':
        # apply a simple 10% overhead for exchange/visa/cross-border fees
        budget_plan = optimize_budget(
            budget * 0.9,
            travelers,
            days,
            source,
            destination,
            transport=transport,
            distance_km=distance,
            travel_type=travel_type,
        )
        notes.append('✈ This is an international trip. Consider visa requirements and processing times (typically 2-12 weeks).')
        notes.append('💱 Budget reduced by 10% to account for currency exchange fees and international transaction costs.')
        notes.append('📄 Essential documents: Valid passport (6+ months validity), travel insurance, and booking confirmations.')
        notes.append(f'🕐 Estimated flight duration for {round(distance/900)} hours approximately. Book flights in advance for better rates.')
        notes.append('🛂 Check vaccination and health requirements for your destination country.')
    else:  # city travel
        notes.append('🏙 Local travel - consider public transport for cost savings and authentic experience.')
        notes.append('🚕 Peak hours: Use carpools or public transport during rush hours for better rates.')

    places = get_places(destination, source)
    recommended_places = recommend_places(places)
    itinerary = generate_itinerary(source, destination, places, days)
    
    # Fetch real-time weather and pricing data
    weather = get_weather(destination)
    flights = None
    train = None
    # Only attach mode-relevant transport info to avoid UI mismatches
    if transport == "Flight" or travel_type == "international":
        flights = get_flight_prices(source, destination, days=7)
    elif transport == "Train":
        train = get_train_info(source, destination, distance, travelers)
    accommodation = get_accommodation_estimate(destination, days)
    currency_rate = get_currency_rate("USD", "INR") if destination.lower() in ["chennai", "delhi", "mumbai"] else 1.0

    result = {
        "transport": transport,
        "distance": round(distance, 2),
        "route": route,
        "places": recommended_places,
        "itinerary": itinerary,
        "budget_plan": budget_plan,
        "coords": waypoint_coords,
        "travel_type": travel_type,
        "weather": weather,
        "flights": flights,
        "train": train,
        "accommodation": accommodation,
        "currency_rate": currency_rate,
    }
    if notes:
        result['notes'] = notes
    return result