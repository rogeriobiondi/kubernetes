from asyncio import events
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

from .util import human_time

# fastapi
app = FastAPI(title = "FastAPI + Redis sample K8s deployment")

@app.on_event("startup")
async def startup_event():
    await validator.load()
    # Get cluster layout and initial topic/partition leadership information
    producer = await topic.create_producer()
    await producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    # Wait for all pending messages to be delivered or expire.
    producer = await topic.get_producer()
    producer.stop()


# def serialize_dates(v):
#     return v.isoformat() if isinstance(v, datetime) else v

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
        Create a new user
    """
    evt = jsonable_encoder(evt)
    evt["operation"] = 'NEW_EVENT'
    evt["timestamp"] = datetime.now().isoformat()
    # Validate event errors
    errors = await validator.validate(evt)
    if len(errors) > 0:
        content = jsonable_encoder(errors)
        return JSONResponse(status_code = status.HTTP_422_UNPROCESSABLE_ENTITY, content = content)
    producer = await topic.get_producer()
    await producer.send_and_wait("package-event-topic", 
        json.dumps(evt).encode('ascii'),
        partition = 0)
    return JSONResponse(status_code = status.HTTP_201_CREATED, content = evt)


@app.get( "/v1/tracking/{tracking_key}", response_description = "Track package") # , response_model = List[ TrackingModel ])
async def track_package(tracking_key: str):
    """
        Get the list of users.
        Data will be cached for 30 seconds. 
    """
    # Try to get data from cache
    tracking = await redis.get(tracking_key)    
    if not tracking:
    # If not found, go to the Mongo
        print("Data doesn't exist in cache. Getting from database...")
        tracking = await db["tracking"].find_one({ "tracking_key": tracking_key })
        if not tracking:
            raise HTTPException(status_code=404, detail=f"Package {tracking_key} not found on the tracking system.") 
        print("Caching data...")
        await redis.set(tracking_key, tracking, cache_ttl=15)
    # Compute the number of events and time
    del tracking["_id"]
    total_events = len(tracking["events"])
    tracking["total_events"] = total_events
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

# @app.get("/{id}", response_description="Get a single user", response_model=UserModel)
# async def show_user(id: str):
#     """
#         Get info from user based on id.
#         Data will be cached for 30 seconds. 
#     """
#     # Try to get data from cache
#     user = await redis.get(id)
#     if not user:
#         # If not found, go to the Mongo
#         print("Data doesn't exist in cache. Getting from database...")
#         if (user := await db["users"].find_one({"_id": id})) is not None:
#             # Put data into the cache for 1m
#             print("Caching data...")
#             await redis.set(id, user)
#             return user
#         raise HTTPException(status_code=404, detail=f"User {id} not found")
#     else: 
#         # Return data from cache
#         print("Returning data directly from cache...")
#         return user


# @app.put("/{id}", response_description="Update a user", response_model=UserModel)
# async def update_user(id: str, user: UpdateUserModel = Body(...)):
#     user = jsonable_encoder(user)
#     user["_id"] = id
#     user["operation"] = 'UPDATE'
#     user["timestamp"] = datetime.now().isoformat()
#     # Update database
#     producer = await topic.get_producer()
#     await producer.send_and_wait("user-topic", 
#         json.dumps(user).encode('ascii'),
#         partition = 0)
#     # Update cache
#     await redis.set(id, user)
#     return JSONResponse(status_code=status.HTTP_200_OK, content=user)

@app.delete("/v1/tracking/{tracking_key}", response_description="Delete an object tracking")
async def delete_tracking(tracking_key: str):
    obj = {}
    obj["tracking_key"] = tracking_key
    obj["operation"] = 'DELETE'
    obj["timestamp"] = datetime.now().isoformat()
    # Update database
    producer = await topic.get_producer()
    await producer.send_and_wait("package-event-topic", 
        json.dumps(obj).encode('ascii'),
        partition = 0)
    # Remove data from cache
    await redis.delete(tracking_key)
    return JSONResponse(status_code=status.HTTP_200_OK, content = obj)
