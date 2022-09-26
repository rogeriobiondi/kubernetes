import os
import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

class Topic:

    def __init__(self):
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:30092')

    async def create_consumer(self, topic, group):
        return AIOKafkaConsumer( 
            topic, 
            bootstrap_servers = self.kafka_servers, 
            group_id = group
        )
    
    async def create_producer(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers = self.kafka_servers            
        )
        return self.producer

    async def get_producer(self):
        if self.producer:
            return self.producer
    
