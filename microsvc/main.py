import socket

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse

from typing import Optional, List

from .models import (
    UserModel,
    UpdateUserModel,
)

from .database import db

app = FastAPI()

@app.get("/ping")
async def ping():
    return { 
        "message": "I'm alive and Kickin'...",
        "server": socket.gethostname(),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/", response_description="Post new user", response_model=UserModel)
async def create_user(user: UserModel = Body(...)):
    user = jsonable_encoder(user)
    new_user = await db["users"].insert_one(user)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@app.get( "/", response_description="List all USERS", response_model=List[UserModel])
async def list_users():
    users = await db["users"].find().to_list(1000)
    return users


@app.get("/{id}", response_description="Get a single user", response_model=UserModel)
async def show_user(id: str):
    if (user := await db["users"].find_one({"_id": id})) is not None:
        return user
    raise HTTPException(status_code=404, detail=f"User {id} not found")


@app.put("/{id}", response_description="Update a user", response_model=UserModel)
async def update_user(id: str, user: UpdateUserModel = Body(...)):
    user = {k: v for k, v in user.dict().items() if v is not None}
    if len(user) >= 1:
        update_result = await db["users"].update_one({"_id": id}, {"$set": user})
        if update_result.modified_count == 1:
            if (
                updated_user := await db["user"].find_one({"_id": id})
            ) is not None:
                return updated_user
    if (existing_user := await db["users"].find_one({"_id": id})) is not None:
        return existing_user
    raise HTTPException(status_code=404, detail=f"User {id} not found")


@app.delete("/{id}", response_description="Delete a user")
async def delete_user(id: str):
    delete_result = await db["users"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"User {id} not found")