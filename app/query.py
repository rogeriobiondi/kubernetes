import os
import logging
import socket
import json

from datetime import datetime
from dateutil import parser

from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi import FastAPI, Depends

from typing import Optional, List

from .models import (
    EventModel,
    TrackingModel,
)

from .util import serialize_object, human_time

# Log configuration
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("query")

# Database
from .database import db

# Redis
from .redis import Redis
redis = Redis()

# Cache
from .cache import Cache
cache = Cache(db, redis)

# Kafka
from .topic import Topic
topic = Topic()

# Load validators
from .validator import Validator
validator = Validator(cache)    

# fastapi
app = FastAPI(title = "FastAPI + Redis sample K8s deployment")

@app.on_event("startup")
async def startup_event():
    # Initialize validators
    await validator.load()
    # Get cluster layout and initial topic/partition leadership information
    producer = await topic.create_producer()
    await producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    # Wait for all pending messages to be delivered or expire.
    producer = await topic.get_producer()
    producer.stop()

@app.get("/ping")
async def ping():
    """
        Ping operation
    """
    return { 
        "message": "I'm alive and Kickin'...",
        "server": socket.gethostname(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/v1/tracking/event", response_description="Post new event", response_model = EventModel)
async def create_event(evt: EventModel = Body(...)):
    """
        Create a new tracking event
    """
    evt = jsonable_encoder(evt)
    evt["operation"] = 'CREATE_EVENT'
    evt["timestamp"] = datetime.now().isoformat()
    # meta block mandatory
    if not evt["meta"]:
        raise HTTPException(status_code=404, detail=f"Event meta block mandatory.")
    # Validate event errors
    errors = await validator.validate(evt) 
    if len(errors) > 0:
        content = jsonable_encoder(errors)
        return JSONResponse(status_code = status.HTTP_422_UNPROCESSABLE_ENTITY, content = content)
    # Post event to the event stream    
    producer = await topic.get_producer()
    await producer.send_and_wait("package-event-topic", 
        json.dumps(evt).encode('ascii'),
        partition = 0)
    return JSONResponse(status_code = status.HTTP_201_CREATED, content = evt)

@app.get( "/v1/tracking/{tracking_key}", response_description = "Track package") # , response_model = List[ TrackingModel ])
async def track_package(tracking_key: str, moderated: bool = True):
    """
        Get the package tracking.
        Data will be cached for 30 seconds. 

        URI/PATH parameters:
        tracking_key: the tracking key of the package

        URL parameters:
        moderated: shows the raw or moderated timeline (true:false)
    """
    # Try to get data from cache
    tracking = await redis.get(tracking_key)    
    if not tracking:
        # If not found, go to the Mongo
        # TODO use the cache sync feature here
        log.debug("Data doesn't exist in cache. Getting from database...")
        tracking = await db["tracking"].find_one({ "tracking_key": tracking_key })
        if not tracking:
            raise HTTPException(status_code=404, detail=f"Package {tracking_key} not found on the tracking system.") 
        log.debug("Caching data...")
        await redis.set(tracking_key, tracking, cache_ttl=15)

    # Hide invisible events from tracking
    if moderated:
        events = []
        raw_events = tracking["events"]
        for e in raw_events:
            if e['visible']:
                events.append(e)
        tracking["events"] = events

    # Compute current package status
    current_status = 'N/A'
    events = tracking["events"]
    for e in events:
        if e['visible']:
            if e['status']:
                current_status = e['status']
    tracking["status"] = current_status

    # Replace ObjectIds
    tracking["_id"] = str(tracking["_id"])
    for e in events:
        e["_id"] = str(e["_id"])

    # Compute the number of events and time
    total_events = len(tracking["events"])
    tracking["total_events"] = total_events   
    if total_events > 0:
        # Elapsed time between the first and last event
        first  = tracking["events"][0]["timestamp"]
        dfirst = parser.parse(first)
        last   = tracking["events"][total_events - 1]["timestamp"]
        dlast  = parser.parse(last)
        dnow   = datetime.now()
        # Elapsed time
        elapsed = int((dnow - dfirst).total_seconds())
        tracking["elapsed"] = elapsed
        tracking["human_elapsed"] = human_time(elapsed)
        # last update time
        last_update = int((dnow - dlast).total_seconds())
        tracking["last_update"] = last_update
        tracking["human_last_update"] = human_time(last_update)
   
    # return tracking obj
    return tracking


@app.delete("/v1/tracking/{tracking_key}", response_description="Delete an object tracking")
async def delete_tracking(tracking_key: str):
    obj = {}
    obj["tracking_key"] = tracking_key
    obj["operation"] = 'DELETE_TRACKING'
    obj["timestamp"] = datetime.now().isoformat()
    # Update database
    producer = await topic.get_producer()
    await producer.send_and_wait("package-event-topic", 
        json.dumps(obj).encode('ascii'),
        partition = 0)
    # Remove data from cache
    await redis.delete(tracking_key)
    return JSONResponse(status_code=status.HTTP_200_OK, content = obj)
