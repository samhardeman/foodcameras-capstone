from flask import Flask, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import os

app = Flask(__name__)
DB_FILE = './database/people_data.db'

# Utility function to fetch data from SQLite
def query_database(query, args=(), one=False):
    """Helper to query the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows

@app.after_request
def add_cors_headers(response):
    """Add Access-Control-Allow-Origin to every response."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# API Routes
@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Return business-level data for each camera."""
    rows = query_database("""
        SELECT l.id AS id, l.name AS location_name, l.longitude AS long, l.latitude AS lat
        FROM locations l
    """)
    response = []
    for row in rows:
        response.append({
            "id": row["id"],
            "location_name": row["location_name"],
            "longitude": row["long"],
            "latitude": row["lat"],
        })
    return jsonify(response)

@app.route('/api/image/<path:image_name>', methods=['GET'])
def get_image(image_name):
    """Return the saved image for a camera."""
    image_path = os.path.join('./static', image_name)  # Images are stored in './static'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    return jsonify({"error": "Image not found"}), 404

@app.route('/api/location/<location>', methods=['GET'])
def get_location(location):
    """Return business-level data for each camera."""
    rows = query_database("""
        SELECT c.id AS camera_id, l.name AS location_name, c.people_count, c.level, c.image
        FROM cameras c
        JOIN locations l ON c.location_id = l.id
        WHERE location_name = ?
    """, (location,))
    
    response = []
    for row in rows:
        response.append({
            "camera_id": row["camera_id"],
            "location_name": row["location_name"],
            "people": row["people_count"],
            "level": row["level"],
            "image": row["image"]
        })
        
    return jsonify(response)

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        print("Error: Database file does not exist.")
    else:
        app.run(debug=True)
