from flask import Flask, request, jsonify, make_response
import json

app = Flask(__name__)

PORT = 3202
HOST = '0.0.0.0'

with open('{}/databases/times.json'.format("."), "r") as jsf:
   schedule = json.load(jsf)["schedule"]

def write(schedule):
   with open('{}/databases/times.json'.format("."), 'w') as f:
      json.dump({"schedule": schedule}, f)

# renvoie l'entree du planning pour une date, ou None si elle n'existe pas
def find_date(date):
   for day in schedule:
      if str(day["date"]) == str(date):
         return day
   return None

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"

# tout le planning, il est public donc pas besoin d'etre admin
@app.route("/schedule", methods=['GET'])
def get_schedule():
   return make_response(jsonify(schedule), 200)

# les films diffuses a une date (utilise par Booking pour verifier un creneau)
@app.route("/schedule/<date>", methods=['GET'])
def get_date(date):
   day = find_date(date)
   if day is None:
      return make_response(jsonify({"error": "date not found"}), 404)
   return make_response(jsonify(day), 200)

# ajout d'une date, le corps contient la liste des films : {"movies": [...]}
@app.route("/schedule/<date>", methods=['POST'])
def add_date(date):
   if find_date(date) is not None:
      return make_response(jsonify({"error": "date already exists"}), 409)
   req = request.get_json()
   day = {"date": date, "movies": req["movies"]}
   schedule.append(day)
   write(schedule)
   return make_response(jsonify(day), 201)

# suppression d'une date, on renvoie l'entree supprimee
@app.route("/schedule/<date>", methods=['DELETE'])
def del_date(date):
   day = find_date(date)
   if day is None:
      return make_response(jsonify({"error": "date not found"}), 404)
   schedule.remove(day)
   write(schedule)
   return make_response(jsonify(day), 200)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
