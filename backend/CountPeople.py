import sqlite3
import requests
import json
import cv2
import os
import numpy as np
from datetime import datetime, timedelta
from dateutil import parser
from io import BytesIO
from Detect import loadModel, detect
from Core import *
from Analytics import *
import sys, os
import random

db = SqliteDatabase('database.db', pragmas={'journal_mode': 'wal'})

# Load the YOLO model
model = loadModel()

API_LOCATIONS_URL = "https://mkt-api.gcu.edu/linecam/api/v1/locations"
API_IMAGES_URL = "https://mkt-api.gcu.edu/linecam/api/v1/images?includeImages=true&includeInactive=false&location="

DB_FILE = './database.db'
INPUT_IMAGES_PATH = './input_images'
OUTPUT_IMAGES_PATH = './static'
os.makedirs(INPUT_IMAGES_PATH, exist_ok=True)
os.makedirs(OUTPUT_IMAGES_PATH, exist_ok=True)

def pushCamera(data):
    with db.connection_context():
        camera = Camera.get(Camera.cameraId == data['id'])
        print(f"data peopleCount: {data['peopleCount']}")
        camera.peopleCount = data['peopleCount']
        camera.timestamp = data['timestamp']
        camera.image = data['imagePath']
        camera.save()
        
def pushTraffic(data):
    with db.connection_context():
        camera = Camera.get(Camera.cameraId == data['id'])
        location = Location.get(Location.name == camera.locationName)
        location.trafficLevel = calculate_busy_level(data['peopleCount'])
        location.save()

def calculate_busy_level(num_people):
    if num_people == 0:
        return "Empty"
    elif num_people < 5:
        return "Low"
    elif num_people < 15:
        return "Medium"
    else:
        return "High"
    
def get_locations():
    with db.connection_context():
        locations = (Location
                     .select(Location.building, fn.COUNT(Location.id).alias('count'))
                     .group_by(Location.building))
        return list(locations)

def process_locations():
    print('processing locations')
    locations = get_locations()
    
    for location in locations:
        cameras = fetch_camera_images(location.building)
        try:
            print(len(cameras))
            for camera in cameras:
                print(camera['description'])
                data = {
                    "id": camera['id'],
                    "timestamp": camera['updated_at'],
                    "peopleCount": 0,
                    "imagePath": ""
                }
                response = requests.get(camera['url'])
                response.raise_for_status()
                image = BytesIO(response.content)
                image_array = np.frombuffer(image.getvalue(), dtype=np.uint8)
                image_file = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                if image_file is None:
                    raise ValueError("Failed to decode image")
                image_name = f"{data['id']}_{camera['description'].replace(' ', '_')}.jpg"
                input_image_path = os.path.join(INPUT_IMAGES_PATH, image_name)
                cv2.imwrite(input_image_path, image_file)
                people_count, annotated_image = detect(input_image_path, model, OUTPUT_IMAGES_PATH, 0.15)
                output_image_path = os.path.join(OUTPUT_IMAGES_PATH, image_name)
                cv2.imwrite(output_image_path, annotated_image)
                busy_level = calculate_busy_level(people_count)
                data['peopleCount'] = people_count
                data['imagePath'] = image_name
                pushCamera(data)
                pushTraffic(data)
                pushFrame(data)
                pushAnalytics(data)
                print(f"Processed {camera['description']}: {people_count} people detected, {busy_level} busy level.")
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

if __name__ == "__main__":
    process_locations()
