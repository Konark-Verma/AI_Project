import pickle
import numpy as np


def predict_transport(distance, budget, travelers, days, travel_type='city'):
    """Predict best transport mode based on distance, budget, and travel type.
    
    Args:
        distance (float): distance in km
        budget (float): total budget in INR
        travelers (int): number of travelers
        days (int): trip duration
        travel_type (str): 'city' or 'international'
    """
    
    # For international travel or long distances (>1500 km), flights are almost always better
    if travel_type == 'international' or distance > 1500:
        return "Flight"
    
    # For shorter distances
    if distance < 50:
        return "Cab"
    elif distance < 300:
        return "Bus"
    elif distance < 1500:
        # Train or bus for medium distances
        return "Train" if budget > 1000 else "Bus"
    
    # Fallback to ML model for edge cases
    try:
        model = pickle.load(open("models/transport_model.pkl", "rb"))
        X = np.array([[distance, budget, travelers, days]])
        prediction = model.predict(X)[0]
        mapping = {
            0: "Cab",
            1: "Bus",
            2: "Train",
            3: "Flight"
        }
        return mapping[prediction]
    except:
        return "Flight"