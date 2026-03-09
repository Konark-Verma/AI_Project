def generate_itinerary(destination,places,days):

    itinerary=[]

    day=1

    for place in places:

        if day>days:
            break

        itinerary.append(f"Day {day}: Explore {place} in {destination}")

        day+=1

    return itinerary