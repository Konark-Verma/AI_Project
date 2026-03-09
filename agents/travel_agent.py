from services.location_service import get_coordinates
from planning.route_planner import calculate_distance, find_route

from intelligence.transport_ml import predict_transport
from intelligence.budget_optimizer import optimize_budget
from intelligence.recommendation_engine import recommend_places

from intelligence.destination_finder import get_places
from llm.itinerary_llm import generate_itinerary


def plan_trip(source,destination,budget,travelers,days):

    src_coords = get_coordinates(source)
    dst_coords = get_coordinates(destination)

    distance = calculate_distance(src_coords,dst_coords)

    route = find_route(source,destination,distance)

    transport = predict_transport(distance,budget,travelers,days)

    budget_plan = optimize_budget(budget,travelers,days)

    places = get_places(destination)

    recommended_places = recommend_places(places)

    itinerary = generate_itinerary(destination,recommended_places,days)

    return {

        "transport":transport,

        "distance":round(distance,2),

        "route":route,

        "places":recommended_places,

        "itinerary":itinerary,

        "budget_plan":budget_plan,

        "coords":[src_coords,dst_coords]

    }