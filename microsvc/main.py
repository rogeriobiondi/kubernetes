import logging
import os
import socket
import aioredis
import json

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse

# from fastapi_redis_cache import FastApiRedisCache, cache
# from fastapi import FastAPI, Request, Response
# from sqlalchemy.orm import Session

from fastapi import FastAPI, Depends

from typing import Optional, List

from .models import (
    UserModel,
    UpdateUserModel,
)

from .database import db

app = FastAPI(title = "FastAPI + Redis sample K8s deployment")

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', 30379)
REDIS_URL = f"redis://{redis_host}:{redis_port}"
redis = aioredis.from_url(REDIS_URL, decode_responses=True)

cache_ttl = os.getenv('CACHE_TTL', 60)

def serialize_dates(v):
    return v.isoformat() if isinstance(v, datetime) else v

@app.get("/ping")
async def ping():
    """
        Ping operation
    """
    print('Ping!')
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
    # update database
    user = jsonable_encoder(user)
    new_user = await db["users"].insert_one(user)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    # update cache
    await redis.set(new_user.inserted_id, json.dumps(created_user, default=serialize_dates), ex = cache_ttl)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@app.get( "/", response_description = "List all USERS", response_model = List[ UserModel ])
async def list_users():
    """
        Get the list of users.
        Data will be cached for 30 seconds. 
    """
    # Try to get data from cache
    users = await redis.get("ROOT")
    if not users:
        # If not found, go to the Mongo
        print("Data doesn't exist in cache. Getting from database...")
        users = await db["users"].find().to_list(1000)
        # Put data into the cache for 1m
        print("Caching data...")
        await redis.set("ROOT", json.dumps(users, default=serialize_dates), ex = cache_ttl)
        return users
    else:
        # Return data from cache
        print("Returning data directly from cache...")
        return json.loads(users)


@app.get("/{id}", response_description="Get a single user", response_model=UserModel)
async def show_user(id: str):
    """
        Get info from user based on id.
        Data will be cached for 30 seconds. 
    """
    # Try to get data from cache
    user = await redis.get(id)
    if not user:
        # If not found, go to the Mongo
        print("Data doesn't exist in cache. Getting from database...")
        if (user := await db["users"].find_one({"_id": id})) is not None:
            # Put data into the cache for 1m
            print("Caching data...")
            await redis.set(id, json.dumps(user, default=serialize_dates), ex = cache_ttl)
            return user
        raise HTTPException(status_code=404, detail=f"User {id} not found")
    else: 
        # Return data from cache
        print("Returning data directly from cache...")
        return json.loads(user)


@app.put("/{id}", response_description="Update a user", response_model=UserModel)
async def update_user(id: str, user: UpdateUserModel = Body(...)):
    user = {k: v for k, v in user.dict().items() if v is not None}
    if len(user) >= 1:
        update_result = await db["users"].update_one({"_id": id}, {"$set": user})
        if update_result.modified_count == 1:
            if (
                updated_user := await db["user"].find_one({"_id": id})
            ) is not None:
                # Update cache
                await redis.set(id, json.dumps(updated_user, default=serialize_dates), ex = cache_ttl)
                return updated_user
    if (existing_user := await db["users"].find_one({"_id": id})) is not None:
        # Update cache
        await redis.set(id, json.dumps(existing_user, default=serialize_dates), ex = cache_ttl)
        return existing_user
    raise HTTPException(status_code=404, detail=f"User {id} not found")


@app.delete("/{id}", response_description="Delete a user")
async def delete_user(id: str):
    delete_result = await db["users"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"User {id} not found")
