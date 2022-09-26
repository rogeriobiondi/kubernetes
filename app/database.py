import os
import logging
import motor.motor_asyncio
from bson import ObjectId

# Connection to MongoDB
user = os.getenv('MONGODB_USER', 'user')
passwd = os.getenv('MONGODB_PASSWORD', 'pass')
host = os.getenv('MONGODB_HOST', 'localhost')
port = os.getenv('MONGODB_PORT', 32017)
dbname = os.getenv('MONGODB_NAME', '')
mongo_url = f"mongodb://{user}:{passwd}@{host}:{port}/{dbname}?retryWrites=true&w=majority"
logging.debug(f"Connecting to... {mongo_url}")
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
db = client.events
