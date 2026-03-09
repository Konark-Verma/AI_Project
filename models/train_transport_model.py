import numpy as np
from sklearn.tree import DecisionTreeClassifier
import pickle
import os
import random


# -------- CREATE MODELS DIRECTORY --------
os.makedirs("models", exist_ok=True)


# -------- GENERATE TRAINING DATA --------

X = []
y = []

for i in range(1000):

    distance = random.randint(1,10000)
    budget = random.randint(50,10000)
    travelers = random.randint(1,5)
    days = random.randint(1,14)

    # transport decision logic
    if distance < 30:
        transport = 0   # Cab

    elif distance < 300:
        transport = 1   # Bus

    elif distance < 1500:
        transport = 2   # Train

    else:
        transport = 3   # Flight


    X.append([distance,budget,travelers,days])
    y.append(transport)


X = np.array(X)
y = np.array(y)


# -------- TRAIN MODEL --------

model = DecisionTreeClassifier()

model.fit(X,y)


# -------- SAVE MODEL --------

model_path = "models/transport_model.pkl"

with open(model_path,"wb") as f:
    pickle.dump(model,f)


print("Transport ML Model trained successfully")
print("Saved at:",model_path)