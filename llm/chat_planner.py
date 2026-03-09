def generate_plan_prompt(user_query):

    prompt = f"""
    Create a travel plan based on this request:

    {user_query}

    Include:
    - best transport
    - intermediate cities
    - famous tourist attractions
    - day wise itinerary
    """

    return prompt