def choose_transport(distance, budget):

    if distance < 30:
        return "Cab"

    elif distance < 300:
        return "Bus"

    elif distance < 1200:
        return "Train"

    else:
        return "Flight"