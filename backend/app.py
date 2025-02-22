from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from Core import db, Location, Camera
from Analytics import Analytics, Frames, weekday, frameStart
from datetime import datetime, time
from CountPeople import process_locations
import threading
import time as timeforsleeping

app = Flask(__name__)
CORS(app)

@app.route('/api/locations', methods=['GET'])
def get_locations():
    with db.connection_context():
        locations = Location.select().dicts()
        return jsonify(list(locations))

@app.route('/api/image/<path:image_name>', methods=['GET'])
def get_image(image_name):
    image_path = os.path.join('./static', image_name)
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    return jsonify({"error": "Image not found"}), 404

@app.route('/api/location/<location_name>', methods=['GET'])
def get_location(location_name):
    with db.connection_context():
        try:
            location = Location.get(Location.name == location_name)
            cameras = list(Camera.select().where(Camera.locationName == location.name).dicts())
            return jsonify(cameras)
        except Location.DoesNotExist:
            return jsonify({"error": "Location not found"}), 404

@app.route('/api/analytics/<location_name>/<weekday>', methods=['GET'])
def get_analytics(location_name, weekday):
    with db.connection_context():
        try:
            location = Location.get(Location.name == location_name)
            cameras = list(Camera.select().where(Camera.locationName == location.name).dicts())
            if not cameras:
                return jsonify({"error": "No cameras found for this location"}), 404
            frames = list(Frames.select()
                           .where((Frames.cameraId == cameras[0]['cameraId']) & (Frames.weekday == weekday))
                           .order_by(Frames.frameStart.desc())
                           .limit(200)
                           .dicts())
        except Location.DoesNotExist:
            return jsonify({"error": "Location not found"}), 404
    
    for frame in frames:
        for key, value in frame.items():
            if isinstance(value, time):
                frame[key] = value.strftime("%H:%M")
    return jsonify(frames)

@app.route('/api/hours/<location>', methods=['GET'])
def get_hours(location):
    """Fetches operating hours for a given location from hours.json"""
    try:
        with open('hours.json', 'r') as f:
            data = json.load(f)

        for loc in data["locations"]:
            if loc["name"].lower() == location.lower():
                return jsonify(loc["hours"])

        return jsonify({"error": "Location hours not found"}), 404

    except FileNotFoundError:
        return jsonify({"error": "hours.json file not found"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Error decoding hours.json"}), 500

def countPeopleEvery15Minutes():
    minutes = 15
    while True:
        process_locations()        
        timeforsleeping.sleep(minutes * 60)

def start_background_task():
    thread = threading.Thread(target=countPeopleEvery15Minutes, daemon=True)
    thread.start()

if __name__ == '__main__':
    with db.connection_context():
        pass  # Ensure the database is initialized properly before starting
    start_background_task()
    app.run(debug=True)
