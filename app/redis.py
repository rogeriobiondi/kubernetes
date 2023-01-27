import os
import json
import aioredis
# import datetime

from bson import ObjectId
from .util import serialize_object

# Redis
class Redis:
    """
        AsyncIo Cache
    """

    def __init__(self):
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = os.getenv('REDIS_PORT', 30379)        
        REDIS_URL = f"redis://{redis_host}:{redis_port}"
        self.cache = aioredis.from_url(REDIS_URL, decode_responses=True)
        self.cache_ttl = os.getenv('CACHE_TTL', 60)

    # def serialize_fields(self, v):
    #     return str(v) if isinstance(v, ObjectId) else v             # Serializar ObjectId
    #     return v.isoformat() if isinstance(v, datetime) else v      # Serializar datetime

    # def serialize_object(self, obj):
    #     return json.dumps(obj, default = self.serialize_fields)

    async def set(self, id, obj, cache_ttl = None):
        """
            Cache the object
        """
        if cache_ttl == None:
            cache_ttl = self.cache_ttl
        await self.cache.set(
            id,
            serialize_object(obj),
            ex = cache_ttl
        )

    async def get(self, id):
        obj = await self.cache.get(id)
        if obj:
            return json.loads(obj)

    async def delete(self, id):
        """
            Remove object from cache
        """
        await self.cache.delete(id)