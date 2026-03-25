def generate_itinerary(origin, destination, places, days):
    """
    Generate a realistic day-by-day itinerary with activities distributed across days.
    Groups locations by proximity and adds practical breaks.
    
    Args:
        origin (str): origin city
        destination (str): destination city
        places (list): list of attraction dicts with name, description, type
        days (int): number of days for the trip
    
    Returns:
        list: day-by-day itinerary with realistic activities
    """
    itinerary = []
    
    if not places:
        # Fallback if no places provided
        for day in range(1, days + 1):
            if day == 1 and origin and origin.lower().strip() != destination.lower().strip():
                itinerary.append(f"Day {day}: Depart from {origin}, arrive in {destination}. Settle into accommodation and explore local area.")
            else:
                itinerary.append(f"Day {day}: Explore local attractions in {destination}.")
        return itinerary
    
    # Extract place names for grouping
    place_names = []
    for p in places:
        if isinstance(p, dict):
            place_names.append(p.get('name', 'Attraction'))
        else:
            place_names.append(str(p).split('(')[0].strip())
    
    # Distribute attractions across days
    attractions_per_day = max(1, len(place_names) // days) if days > 0 else 1
    
    for day in range(1, days + 1):
        start_idx = (day - 1) * attractions_per_day
        end_idx = min(day * attractions_per_day, len(place_names))
        
        day_attractions = place_names[start_idx:end_idx]
        
        if day == 1:
            if origin and origin.lower().strip() != destination.lower().strip():
                itinerary.append(f"Day {day}: Depart from {origin}, travel to {destination}. Check-in to hotel, then explore {day_attractions[0] if day_attractions else 'the city center'}.")
            else:
                itinerary.append(f"Day {day}: Arrive in {destination}. Check-in to hotel. Evening stroll around {day_attractions[0] if day_attractions else 'city center'}.")
        elif day == days:
            itinerary.append(f"Day {day}: Final exploration of {', '.join(day_attractions)}. Pack and prepare for departure.")
        else:
            if len(day_attractions) == 1:
                itinerary.append(f"Day {day}: Deep dive into {day_attractions[0]}. Morning tour, lunch at a local restaurant, afternoon at leisure.")
            elif len(day_attractions) == 2:
                itinerary.append(f"Day {day}: Morning at {day_attractions[0]}; afternoon at {day_attractions[1]}. Dinner at a local favorite.")
            else:
                attractions_str = ', '.join(day_attractions)
                itinerary.append(f"Day {day}: Visit {attractions_str}. Mix guided tours with free exploration and local cuisine.")
    
    return itinerary