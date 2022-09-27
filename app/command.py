import os
import json
import asyncio
import logging

from pymongo import ReturnDocument

from art import *

from topic import Topic
topic = Topic()

from redis import Cache
cache = Cache()

from database import db 


async def consume():
    # Get cluster layout and join `user-topic` and group `command_group`
    consumer = await topic.create_consumer('package-event-topic', 'command-group')
    await consumer.start()
    try:
        # Consume messages
        async for msg in consumer:
            logging.debug( "consumed: ", msg.topic, msg.partition, msg.offset,
                msg.key, msg.value, msg.timestamp)
            obj = json.loads(msg.value)
            tracking_key  = obj['tracking_key']
            
            # Creates a new object
            if obj['operation'] == 'NEW_EVENT':
                print(f"NEW_EVENT: {tracking_key}")
                del obj['operation']
                new_obj = await db["tracking"].find_one_and_update(
                    { "tracking_key": tracking_key },
                    { "$push": { "events": obj } },
                    return_document = ReturnDocument.AFTER,
                    upsert = True
                )
                # update cache
                # print(new_obj)
                await cache.set(tracking_key, new_obj)
            
            # # Updates an existing object
            # elif obj['operation'] == 'UPDATE':
            #     logging.info(f"UPDATE: {id}")
            #     del obj['operation']
            #     user = {k: v for k, v in obj.items() if v is not None}
            #     update_result = await db["users"].update_one({"_id": id}, {"$set": user})
            #     if update_result.modified_count == 1:
            #         # Update cache
            #         await cache.set(id, user)
               
            elif obj['operation'] == 'DELETE':
                logging.info(f"DELETE: {tracking_key}")
                delete_result = await db["tracking"].delete_one({"tracking_key": tracking_key})
                if delete_result.deleted_count == 1:
                    await cache.delete(tracking_key)                

    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()

# Initialization message
print(text2art("Command"))
asyncio.run(consume())