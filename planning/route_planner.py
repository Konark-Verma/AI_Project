from geopy.distance import geodesic

def calculate_distance(src, dst):

    return geodesic(src, dst).km


def find_route(source, destination, distance):

    if distance > 9000:
        return [source, "London", destination]

    if distance > 5000:
        return [source, "Dubai", destination]

    if distance > 2000:
        return [source, "Istanbul", destination]

    return [source, destination]