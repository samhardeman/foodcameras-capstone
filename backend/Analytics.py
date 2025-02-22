from datetime import datetime, timedelta
import math
import requests
from peewee import *
from Core import Camera, Location, db
import pytz

class Analytics(Model):
    cameraId = ForeignKeyField(Camera, backref='id')
    timestamp = DateTimeField(formats='ISO-8601')
    peopleCount = IntegerField(default=0)
    
    class Meta:
        database = db
        
class Frames(Model):
    cameraId = ForeignKeyField(Camera, backref='id')
    weekday = CharField()
    summer = CharField()
    frameStart = TimeField()
    low = IntegerField()
    high = IntegerField()
    average = IntegerField()
    
    class Meta:
        database = db

ARIZONA_TZ = pytz.timezone('America/Phoenix')

def frameStart(date_string: str, interval_minutes=30) -> datetime:
    current_time = datetime.fromisoformat(date_string)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=pytz.utc)
    current_time = current_time.astimezone(ARIZONA_TZ)
    total_minutes = current_time.hour * 60 + current_time.minute
    rounded_minutes = (total_minutes // interval_minutes) * interval_minutes
    frame_start_time = current_time.replace(hour=rounded_minutes // 60, minute=rounded_minutes % 60, second=0, microsecond=0)
    return frame_start_time

def weekday(timestamp: str) -> str:
    dt = datetime.fromisoformat(timestamp).replace(tzinfo=pytz.utc).astimezone(ARIZONA_TZ)
    return dt.strftime('%A')

def isSummer(timestamp: str) -> bool:
    dt = datetime.fromisoformat(timestamp).replace(tzinfo=pytz.utc).astimezone(ARIZONA_TZ)
    return 5 <= dt.month <= 8

def updateFrame(data, frames):
    with db.connection_context():
        for frame in frames:
            if data['peopleCount'] > frame.high:
                frame.high = data['peopleCount']
            elif data['peopleCount'] < frame.low:
                frame.low = data['peopleCount']
            frame.average = (frame.average + data['peopleCount']) / 2
            frame.save()

def pushAnalytics(data):  
    with db.connection_context():
        existing_point = Analytics.get_or_none(
            (Analytics.cameraId == data['id']) & 
            (Analytics.timestamp == data['timestamp'])
        )
        if existing_point is None:
            Analytics.create(
                cameraId=data['id'], 
                timestamp=data['timestamp'], 
                peopleCount=data['peopleCount']
            )
        else:
            print(f"Skipping duplicate entry for camera {data['id']} at {data['timestamp']}")
            
def pushFrame(data):
    # Materialize the query result while the connection is open
    with db.connection_context():
        frames = list(Frames.select().where(
            (Frames.cameraId == data['id']) &
            (Frames.frameStart == frameStart(data['timestamp'])) &
            (Frames.summer == isSummer(data['timestamp'])) &
            (Frames.weekday == weekday(data['timestamp']))
        ))
    
    if frames:
        updateFrame(data, frames)
    else:
        with db.connection_context():
            Frames.create(
                cameraId=data['id'], 
                weekday=weekday(data['timestamp']), 
                frameStart=frameStart(data['timestamp']),
                summer=isSummer(data['timestamp']),
                high=data['peopleCount'],
                low=data['peopleCount'],
                average=data['peopleCount']
            )
