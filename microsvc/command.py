import os
import json
import asyncio
import logging

from art import *

from topic import Topic
topic = Topic()

from redis import Cache
cache = Cache()

from database import db 

async def consume():
    # Get cluster layout and join `user-topic` and group `command_group`
    consumer = await topic.create_consumer('user-topic', 'command_group')
    await consumer.start()
    try:
        # Consume messages
        async for msg in consumer:
            logging.debug( "consumed: ", msg.topic, msg.partition, msg.offset,
                msg.key, msg.value, msg.timestamp)
            obj = json.loads(msg.value)
            id  = obj['_id']
            
            # Creates a new object
            if obj['operation'] == 'CREATE':
                logging.info(f"CREATE: {obj['_id']}")
                del obj['operation']
                # update database
                new_user = await db["users"].insert_one(obj)
                created_user = await db["users"].find_one({"_id": new_user.inserted_id})
                # update cache
                await cache.set(new_user.inserted_id, created_user)
            
            # Updates an existing object
            elif obj['operation'] == 'UPDATE':
                logging.info(f"UPDATE: {id}")
                del obj['operation']
                user = {k: v for k, v in obj.items() if v is not None}
                update_result = await db["users"].update_one({"_id": id}, {"$set": user})
                if update_result.modified_count == 1:
                    # Update cache
                    await cache.set(id, user)
               
            elif obj['operation'] == 'DELETE':
                logging.info(f"DELETE: {id}")
                delete_result = await db["users"].delete_one({"_id": id})
                if delete_result.deleted_count == 1:
                    await cache.delete(id)                

    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()

# Initialization message
print(text2art("Command"))
asyncio.run(consume())