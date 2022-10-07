import os
import json
import asyncio
import logging
import importlib
import copy
from unicodedata import name

from pymongo import ReturnDocument

from art import *
from bson import ObjectId

# Log configuration
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("moderator")

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

# Import moderators
from .moderators import first
from .moderators import only_once


# Consume event-topic
async def consume():
    
    # Update validators
    await validator.load()
    
    # Get cluster layout and join `tracking-moderation-topic` and group `tracking-moderators-group`
    consumer = await topic.create_consumer('tracking-moderation-topic', 'tracking-moderators-group')
    await consumer.start()
    try:
        # Consume messages
        async for msg in consumer:
            log.debug( "consumed: ", msg.topic, msg.partition, msg.offset,
                msg.key, msg.value, msg.timestamp)
            obj = json.loads(msg.value)
            # Get the tracking and event objects
            tracking = obj['tracking']
            event  = obj['event']            
            tracking_key = tracking['tracking_key']
            # with event type, get the validator            
            evt_validator = await validator.get(event['type'])            
            result = True
            reason = "moderation: all checks passed."
            # Execute the moderation pipeline only if they exist.
            if "moderators" in evt_validator:
                moderators = evt_validator['moderators']
                for mod in moderators:
                    name_mod = ""
                    args = []
                    # Check if the moderator has arguments (ex: depends_on)
                    if isinstance(mod, str):
                        name_mod = mod
                    if isinstance(mod, dict):
                        name_mod  = next(iter(mod))
                        args = mod[name_mod]
                    log.info(f'Invoking moderator {name_mod}...')
                    module_name = ".moderators." + name_mod
                    log.info(f"Importing {module_name}")
                    module_moderator = importlib.import_module(f'.{name_mod}', package="app.moderators")
                    moderator = module_moderator.EntryPoint()
                    result = moderator.moderate(tracking, event, args)
                    log.info(f'running moderator {name_mod}...{result}')
                    if not result:
                        reason = f"moderation: ({name_mod}) failed. "
                        # If at least one moderator fails, abort the validation
                        break
            # Update event according moderation
            query  = { "tracking_key": tracking_key, "events._id": ObjectId(event['_id']) }
            update = {   "$set": { "events.$.visible": result, "events.$.reason" : reason } }
            tracking_moderated = await db["tracking"].find_one_and_update(
                query, update, return_document = ReturnDocument.AFTER
            )
            # Invalidate cache for the tracking object
            await cache.delete(None, tracking_key)
            log.info("---")
            log.info("")
            
    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()

# Initialization message
print(text2art("Moderator"))
asyncio.run(consume())