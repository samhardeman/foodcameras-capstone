import sqlite3
import requests
import json
import cv2
import os
import numpy as np
from datetime import datetime
from io import BytesIO
from Detect import loadModel, detect

# Load the YOLO model
model = loadModel()

# API endpoints
API_LOCATIONS_URL = "https://mkt-api.gcu.edu/linecam/api/v1/locations"
API_IMAGES_URL = "https://mkt-api.gcu.edu/linecam/api/v1/images?includeImages=true&includeInactive=false&location="

# Initialize database file
DB_FILE = './database/people_data.db'

# Ensure directories for input and output images exist
INPUT_IMAGES_PATH = './input_images'
OUTPUT_IMAGES_PATH = './static'
os.makedirs(INPUT_IMAGES_PATH, exist_ok=True)
os.makedirs(OUTPUT_IMAGES_PATH, exist_ok=True)

def initialize_database():
    """Initialize the SQLite database with the required tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            longitude REAL NOT NULL,
            latitude REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY NOT NULL,
            location_id INTEGER,
            description TEXT,
            level TEXT,
            people_count INTEGER,
            image TEXT,
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
        )
    ''')
    # New analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            people_count INTEGER NOT NULL,
            FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def fetch_locations_from_api():
    """Fetch locations from the API."""
    response = requests.get(API_LOCATIONS_URL)
    response.raise_for_status()
    return response.json()

def fetch_camera_images(location_name):
    """Fetch images for a location from the API."""
    response = requests.get(f"{API_IMAGES_URL}{location_name}")
    response.raise_for_status()
    return response.json()

def add_analytics_data(camera_id, people_count, updated_at):
    """
    Insert analytics data into the database if the timestamp does not already exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if an entry with this updated_at and camera_id already exists
    cursor.execute('''
        SELECT id FROM analytics WHERE camera_id = ? AND timestamp = ?
    ''', (camera_id, updated_at))
    existing_entry = cursor.fetchone()

    if not existing_entry:
        # Insert new entry if it doesn't exist
        cursor.execute('''
            INSERT INTO analytics (camera_id, timestamp, people_count)
            VALUES (?, ?, ?)
        ''', (camera_id, updated_at, people_count))
        print(f"Added analytics data for camera {camera_id} at {updated_at}: {people_count} people.")
    else:
        print(f"Skipped adding analytics data for camera {camera_id} at {updated_at}: Entry already exists.")

    conn.commit()
    conn.close()


def add_or_update_location(longitude, latitude, name):
    """Add or update a location in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM locations WHERE name = ?", (name,))
    location = cursor.fetchone()

    if location:
        location_id = location[0]
        cursor.execute(
            "UPDATE locations SET longitude = ?, latitude = ? WHERE id = ?",
            (longitude, latitude, location_id),
        )
    else:
        cursor.execute(
            "INSERT INTO locations (longitude, latitude, name) VALUES (?, ?, ?)",
            (longitude, latitude, name),
        )
        location_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return location_id

def add_or_update_camera(id, description, level, people_count, image_path):
    """Add or update a camera in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id FROM cameras WHERE id = ? AND description = ?
    ''', (id, description))
    result = cursor.fetchone()

    if result is None:
        cursor.execute('''
            INSERT INTO cameras (id, description, level, people_count, image)
            VALUES (?, ?, ?, ?, ?)
        ''', (id, description, level, people_count, image_path))
    else:
        cursor.execute('''
            UPDATE cameras
            SET level = ?, people_count = ?, image = ?
            WHERE id = ? AND description = ?
        ''', (level, people_count, image_path, id, description))

    conn.commit()
    conn.close()

def calculate_busy_level(num_people):
    """Determine the busy level based on the number of people detected."""
    if num_people == 0:
        return "Empty"
    elif num_people < 5:
        return "Low"
    elif num_people < 15:
        return "Medium"
    else:
        return "High"

def process_locations():
    """Process locations from the API and run detection."""
    try:
        # Fetch locations from the API
        api_response = requests.get("https://mkt-api.gcu.edu/linecam/api/v1/locations")
        api_response.raise_for_status()
        locations = api_response.json()

        if not isinstance(locations, list):
            raise ValueError("Expected a list of location names, got something else.")

        for location_name in locations:
            if not isinstance(location_name, str):
                print(f"Skipping malformed location entry: {location_name}")
                continue

            location_id = add_or_update_location(0.0, 0.0, location_name)

            # Fetch cameras for the location
            cameras = fetch_camera_images(location_name)

            for camera in cameras:
                description = camera.get("description", "Unknown Camera")
                id = camera.get("id", "0")
                url = camera.get("url")
                updated_at = camera.get("updated_at")  # Use the updated_at field from the API

                if not updated_at:
                    print(f"Skipping camera '{description}' for location '{location_name}': No updated_at timestamp.")
                    continue

                if not url:
                    print(f"Skipping camera '{description}' for location '{location_name}': No image URL.")
                    continue

                try:
                    # Fetch and process image
                    response = requests.get(url)
                    response.raise_for_status()
                    image = BytesIO(response.content)
                    image_array = np.frombuffer(image.getvalue(), dtype=np.uint8)
                    image_file = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                    if image_file is None:
                        raise ValueError("Failed to decode image")

                    image_name = f"{id}_{description.replace(' ', '_')}.jpg"
                    input_image_path = os.path.join(INPUT_IMAGES_PATH, image_name)
                    cv2.imwrite(input_image_path, image_file)

                    # Run detection
                    people_count, annotated_image = detect(input_image_path, model, OUTPUT_IMAGES_PATH, 0.15)
                    output_image_path = os.path.join(OUTPUT_IMAGES_PATH, image_name)
                    cv2.imwrite(output_image_path, annotated_image)

                    # Calculate busy level
                    busy_level = calculate_busy_level(people_count)

                    # Add or update camera
                    add_or_update_camera(id, description, busy_level, people_count, image_name)

                    # Add analytics data
                    add_analytics_data(id, people_count, updated_at)

                    print(f"Processed {description}: {people_count} people detected, {busy_level} busy level.")

                except Exception as e:
                    print(f"Error processing camera {description}: {e}")

    except Exception as e:
        print(f"Error processing locations: {e}")



# Initialize database and process data
initialize_database()
process_locations()