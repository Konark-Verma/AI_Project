from flask import Flask, render_template, request, jsonify
from agents.travel_agent import plan_trip

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("travel_type.html")


@app.route("/search")
def search():
    return render_template("index.html")


@app.route("/result")
def result():
    return render_template("result.html")


@app.route("/plan", methods=["POST"])
def plan():

    data = request.json

    source = data["source"]
    destination = data["destination"]
    travelers = int(data["travelers"])
    budget = float(data["budget"])
    days = int(data["days"])

    result = plan_trip(source,destination,budget,travelers,days)

    return jsonify(result)


if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True)