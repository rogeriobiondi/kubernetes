# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# # SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()


import os
import logging
import motor.motor_asyncio

# Connection to MongoDB
user = os.getenv('MONGODB_USER', 'user')
passwd = os.getenv('MONGODB_PASSWORD', 'pass')
host = os.getenv('MONGODB_HOST', 'localhost')
port = os.getenv('MONGODB_PORT', 27017)
dbname = os.getenv('MONGODB_NAME', '')
mongo_url = f"mongodb://{user}:{passwd}@{host}:{port}/{dbname}?retryWrites=true&w=majority"
logging.debug(f"Connecting to... {mongo_url}")
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
db = client.users
