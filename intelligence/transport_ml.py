import pickle
import numpy as np


def predict_transport(distance,budget,travelers,days):

    model = pickle.load(open("models/transport_model.pkl","rb"))

    X = np.array([[distance,budget,travelers,days]])

    prediction = model.predict(X)[0]

    mapping = {
        0:"Cab",
        1:"Bus",
        2:"Train",
        3:"Flight"
    }

    return mapping[prediction]