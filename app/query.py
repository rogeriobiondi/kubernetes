import logging
import socket
import json

from datetime import datetime

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
from .redis import Cache
cache = Cache()

# Kafka
from .topic import Topic
topic = Topic()

app = FastAPI(title = "FastAPI + Redis sample K8s deployment")


@app.on_event("startup")
async def startup_event():
    # Get cluster layout and initial topic/partition leadership information
    producer = await topic.create_producer()
    await producer.start()


@app.on_event("shutdown")
async def shutdown_event():
    # Wait for all pending messages to be delivered or expire.
    producer = await topic.get_producer()
    producer.stop()


def serialize_dates(v):
    return v.isoformat() if isinstance(v, datetime) else v

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
    tracking = await cache.get(tracking_key)    
    if not tracking:
    # If not found, go to the Mongo
        print("Data doesn't exist in cache. Getting from database...")
        tracking = await db["tracking"].find_one({ "tracking_key": tracking_key })
        if not tracking:
            raise HTTPException(status_code=404, detail=f"Package {tracking_key} not found on the tracking system.") 
        print("Caching data...")
        await cache.set(tracking_key, tracking, cache_ttl=15)
    return tracking

# @app.get("/{id}", response_description="Get a single user", response_model=UserModel)
# async def show_user(id: str):
#     """
#         Get info from user based on id.
#         Data will be cached for 30 seconds. 
#     """
#     # Try to get data from cache
#     user = await cache.get(id)
#     if not user:
#         # If not found, go to the Mongo
#         print("Data doesn't exist in cache. Getting from database...")
#         if (user := await db["users"].find_one({"_id": id})) is not None:
#             # Put data into the cache for 1m
#             print("Caching data...")
#             await cache.set(id, user)
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
#     await cache.set(id, user)
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
    await cache.delete(tracking_key)
    return JSONResponse(status_code=status.HTTP_200_OK, content = obj)
