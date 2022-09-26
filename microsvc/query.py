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
    UserModel,
    UpdateUserModel,
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

@app.post("/", response_description="Post new user", response_model=UserModel)
async def create_user(user: UserModel = Body(...)):
    """
        Create a new user
    """
    user = jsonable_encoder(user)
    user["operation"] = 'CREATE'
    user["timestamp"] = datetime.now().isoformat()
    producer = await topic.get_producer()
    await producer.send_and_wait("user-topic", 
        json.dumps(user).encode('ascii'),
        partition = 0)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=user)


@app.get( "/", response_description = "List all USERS", response_model = List[ UserModel ])
async def list_users():
    """
        Get the list of users.
        Data will be cached for 30 seconds. 
    """
    # Try to get data from cache
    users = await cache.get("list")
    if not users:
    # If not found, go to the Mongo
        logging.debug("Data doesn't exist in cache. Getting from database...")
        users = await db["users"].find().to_list(1000)
        # Put data into the cache for 1m
        logging.debug("Caching data...")
        # Use a shorter cache for listing
        await cache.set("list", users, cache_ttl=5)
    return users


@app.get("/{id}", response_description="Get a single user", response_model=UserModel)
async def show_user(id: str):
    """
        Get info from user based on id.
        Data will be cached for 30 seconds. 
    """
    # Try to get data from cache
    user = await cache.get(id)
    if not user:
        # If not found, go to the Mongo
        print("Data doesn't exist in cache. Getting from database...")
        if (user := await db["users"].find_one({"_id": id})) is not None:
            # Put data into the cache for 1m
            print("Caching data...")
            await cache.set(id, user)
            return user
        raise HTTPException(status_code=404, detail=f"User {id} not found")
    else: 
        # Return data from cache
        print("Returning data directly from cache...")
        return user


@app.put("/{id}", response_description="Update a user", response_model=UserModel)
async def update_user(id: str, user: UpdateUserModel = Body(...)):
    user = jsonable_encoder(user)
    user["_id"] = id
    user["operation"] = 'UPDATE'
    user["timestamp"] = datetime.now().isoformat()
    # Update database
    producer = await topic.get_producer()
    await producer.send_and_wait("user-topic", 
        json.dumps(user).encode('ascii'),
        partition = 0)
    # Update cache
    await cache.set(id, user)
    return JSONResponse(status_code=status.HTTP_200_OK, content=user)

@app.delete("/{id}", response_description="Delete a user")
async def delete_user(id: str):
    user = {}
    user["_id"] = id
    user["operation"] = 'DELETE'
    user["timestamp"] = datetime.now().isoformat()
    # Update database
    producer = await topic.get_producer()
    await producer.send_and_wait("user-topic", 
        json.dumps(user).encode('ascii'),
        partition = 0)
    # Remove data from cache
    await cache.delete(id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=user)

