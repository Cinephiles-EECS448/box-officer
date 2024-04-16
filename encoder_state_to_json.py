import pickle
import json

with open("encoder_state.pkl", "rb") as file:
    data = pickle.load(file)

with open("encoder_state.json", "w") as file:
    json.dump(data, file)
