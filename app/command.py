import os
import json
import asyncio
import logging

from app.util import serialize_object

from pymongo import ReturnDocument

from art import *
from bson import ObjectId

# Log configuration
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("command")

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



# Consume event-topic
async def consume():
    
    # Create the moderation producer
    producer = await topic.create_producer()
    await producer.start()

    # Get cluster layout and join `user-topic` and group `command_group`
    consumer = await topic.create_consumer('package-event-topic', 'command-group')
    await consumer.start()
    try:
        # Consume messages
        async for msg in consumer:
            log.debug( "consumed: ", msg.topic, msg.partition, msg.offset,
                msg.key, msg.value, msg.timestamp)
            obj = json.loads(msg.value)
            tracking_key  = obj['tracking_key']
            
            # Creates a new object
            if obj['operation'] == 'CREATE_EVENT':
                log.info(f"CREATE_EVENT: {tracking_key}")
                del obj['operation']
                obj['_id'] = ObjectId(obj['_id'])
                obj["visible"] = False
                obj["reason"] = "query: all checks passed. command: waiting for moderation."
                tracking = await db["tracking"].find_one_and_update(
                    { "tracking_key": tracking_key },
                    { "$push": { "events": obj } },
                    return_document = ReturnDocument.AFTER,
                    upsert = True
                )
                # dispatch request to the event-moderator
                producer = await topic.get_producer()
                await producer.send_and_wait(
                    "tracking-moderation-topic",           
                    serialize_object({ "tracking": tracking, "event": obj }).encode('ascii'),          
                    partition = 0
                )               
            elif obj['operation'] == 'DELETE_TRACKING':
                log.info(f"DELETE_TRACKING: {tracking_key}")
                delete_result = await db["tracking"].delete_one({"tracking_key": tracking_key})
                if delete_result.deleted_count == 1:
                    await cache.delete('tracking', tracking_key)

    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()

# Initialization message
print(text2art("Command"))
asyncio.run(consume())
