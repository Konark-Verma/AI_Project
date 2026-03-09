from geopy.geocoders import Nominatim

geo = Nominatim(user_agent="ai_travel_planner")

def get_coordinates(city):

    try:
        location = geo.geocode(city)

        if location:
            return (location.latitude, location.longitude)

    except:
        pass

    return (20.5937,78.9629)