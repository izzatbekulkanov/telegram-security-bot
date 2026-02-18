import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, Float
from src.config import settings

Base = declarative_base()
logger = logging.getLogger("NeuralMemoryCore")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)

    # YANGI USTUNLAR
    username = Column(String, nullable=True)  # Qidirish uchun kerak
    is_admin = Column(Boolean, default=False)  # Adminlik huquqi

    phone = Column(String, nullable=True)
    language = Column(String, default=None)
    reputation_score = Column(Float, default=100.0)
    risk_level = Column(String, default="NEUTRAL")
    check_count = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.user_id} | @{self.username} | Admin: {self.is_admin}>"


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    title = Column(String, nullable=False)
    is_log_channel = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Channel {self.title} | ID: {self.chat_id}>"


engine = create_async_engine(settings.DB_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ [SYSTEM] Database initialized with Admin, Username & Channels.")
    except Exception as e:
        logger.critical(f"❌ [FATAL] Database Error: {e}")