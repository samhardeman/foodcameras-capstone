import requests
from peewee import *

API_LOCATIONS_URL = "https://mkt-api.gcu.edu/linecam/api/v1/locations"
API_IMAGES_URL = "https://mkt-api.gcu.edu/linecam/api/v1/images?includeImages=true&includeInactive=false&location="

# Enable WAL mode for improved concurrent writes
db = SqliteDatabase('database.db', pragmas={'journal_mode': 'wal'})

def fetch_camera_images(location_name):
    """Fetch images for a location from the API."""
    response = requests.get(f"{API_IMAGES_URL}{location_name}")
    response.raise_for_status()
    return response.json()

def fetch_locations_from_api():
    """Fetch locations from the API."""
    response = requests.get(API_LOCATIONS_URL)
    response.raise_for_status()
    return response.json()

class Location(Model):
    name = CharField()
    building = CharField()
    longitude = CharField()
    latitude = CharField()
    trafficLevel = CharField()
    
    class Meta:
        database = db
    
class Camera(Model):
    cameraId = IntegerField(default=0)
    name = CharField()
    locationName = CharField()
    peopleCount = IntegerField(default=0)
    timestamp = DateTimeField(formats='ISO-8601')
    image = CharField()
    
    class Meta:
        database = db

#db.create_tables([Location, Camera])
    
def populateLocationsAndCameras():
    with db.connection_context():
        buildings = fetch_locations_from_api()

        for building in buildings:
            locations = fetch_camera_images(building)
            
            print(building)
            
            for location in locations:
                longitude = input(f"Input Longitude for {location['description']}\n")
                latitude = input(f"Input Latitude for {location['description']}\n")
                
                place = Location.create(name=location['description'], 
                                building=building,
                                latitude=latitude,
                                longitude=longitude,
                                trafficLevel='empty')
                            
                camera = Camera.create(cameraId=location['id'],
                                name=location['description'],
                                locationName=location['description'],
                                timestamp=location['updated_at'],
                                image=f"{location['id']}_{location['description']}.jpg")
