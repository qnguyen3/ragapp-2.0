import motor.motor_asyncio
from beanie import init_beanie
from .config import settings
from .models.chat import ChatSession, Message

async def init_db():
    """Initialize database connections."""
    # Create Motor client
    client = motor.motor_asyncio.AsyncIOMotorClient(
        settings.MONGODB_URL
    )
    
    # Initialize Beanie with the MongoDB client
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            ChatSession,
            Message
        ]
    )
    
    return client

async def close_db(client):
    """Close database connections."""
    client.close()
