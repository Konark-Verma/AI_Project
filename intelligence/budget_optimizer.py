def optimize_budget(budget, travelers, days):

    per_day = budget / days

    if per_day < 100:
        return "Low Budget Travel Plan"

    if per_day < 500:
        return "Standard Travel Plan"

    return "Luxury Travel Plan"