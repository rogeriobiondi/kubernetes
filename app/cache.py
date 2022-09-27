class Cache:

    def __init__(self, db, redis):
        """
            Initiates the cache.
            db: motor database object
            redis: aioredis client object
        """
        super().__init__()
        self.db = db
        self.redis = redis

    async def get(self, prefix: str, collection: str, key_field: str, key_value: str, ttl:int = 0) -> dict:
        """
            Manage the cache for an object between database and redis.

            prefix: prefix of redis collection: PREFIX:<key>
            collection: mongodb collection
            key_field: mongodb field to find in the collection
            key_value: mongodb value to find in the key_field
            ttl: cache time-to-live in seconds. 0 seconds = never expire
        """
        # Get info from cache
        print(f"Getting {{{key_field}:{key_value}}} from cache...")
        obj = await self.redis.get(f'{prefix.upper()}:{key_value}')
        if not obj:
            # object doesn't exist, get from database
            print("Object doesn't exist in cache. Getting it from db...")
            obj = await self.db[collection].find_one({ key_field: key_value })
            if obj:
                print("Caching obj information...")
                # Cache information for ttl seconds
                await self.redis.set(f'{prefix.upper()}:{key_value}', obj, ttl)
        return obj

    async def delete(self, prefix: str, key_value: str):
        """
            Remove data from cache
        """
        await self.redis.delete('{prefix}:{key_value}')
