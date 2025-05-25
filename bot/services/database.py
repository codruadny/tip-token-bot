import logging
import json
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import declarative_base
from cryptography.fernet import Fernet

from bot.config import settings

# Initialize SQLAlchemy engine and session
engine = create_async_engine(settings.DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# Initialize encryption for private keys
# In production, use a secure key management solution
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

# Define database models (tables)
class Users(Base):
    __tablename__ = "users"
    
    user_id = sa.Column(sa.BigInteger, primary_key=True)
    username = sa.Column(sa.String, nullable=True)
    first_name = sa.Column(sa.String, nullable=True)
    last_name = sa.Column(sa.String, nullable=True)
    language = sa.Column(sa.String(2), default="en")
    wallet_address = sa.Column(sa.String, nullable=True)
    encrypted_private_key = sa.Column(sa.String, nullable=True)
    referrer_id = sa.Column(sa.BigInteger, nullable=True)
    referral_count = sa.Column(sa.Integer, default=0)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    last_active = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transactions(Base):
    __tablename__ = "transactions"
    
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    sender_id = sa.Column(sa.BigInteger, nullable=True)
    recipient_id = sa.Column(sa.BigInteger, nullable=True)
    sender_wallet = sa.Column(sa.String, nullable=True)
    recipient_wallet = sa.Column(sa.String, nullable=True)
    amount = sa.Column(sa.Float, nullable=False)
    tx_hash = sa.Column(sa.String, nullable=True)
    tx_type = sa.Column(sa.String, nullable=False)  # tip, withdraw, deposit, etc.
    status = sa.Column(sa.String, default="completed")
    idempotency_key = sa.Column(sa.String, nullable=True, unique=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

async def create_user_if_not_exists(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    language: str = "en",
    referrer_id: Optional[int] = None
) -> bool:
    """Create a new user if they don't already exist in the database.
    Returns True if a new user was created, False if user already existed.
    """
    async with async_session_maker() as session:
        # Check if user exists
        query = sa.select(Users).where(Users.user_id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            # User exists, update last active
            user.last_active = datetime.utcnow()
            if username and user.username != username:
                user.username = username
            if first_name and user.first_name != first_name:
                user.first_name = first_name
            if last_name and user.last_name != last_name:
                user.last_name = last_name
            
            await session.commit()
            return False
        
        # Create new user
        new_user = Users(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            referrer_id=referrer_id if referrer_id != user_id else None  # Prevent self-referral
        )
        session.add(new_user)
        await session.commit()
        return True

async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user data by user_id."""
    async with async_session_maker() as session:
        query = sa.select(Users).where(Users.user_id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language": user.language,
            "wallet_address": user.wallet_address,
            "referrer_id": user.referrer_id,
            "referral_count": user.referral_count,
            "created_at": user.created_at,
            "last_active": user.last_active
        }

async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user data by username."""
    async with async_session_maker() as session:
        query = sa.select(Users).where(Users.username == username)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language": user.language,
            "wallet_address": user.wallet_address,
            "referrer_id": user.referrer_id,
            "referral_count": user.referral_count,
            "created_at": user.created_at,
            "last_active": user.last_active
        }

async def update_user_language(user_id: int, language: str) -> bool:
    """Update user's preferred language."""
    async with async_session_maker() as session:
        query = sa.select(Users).where(Users.user_id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.language = language
        await session.commit()
        return True

async def get_user_language(user_id: int) -> Optional[str]:
    """Get user's preferred language."""
    async with async_session_maker() as session:
        query = sa.select(Users.language).where(Users.user_id == user_id)
        result = await session.execute(query)
        language = result.scalar_one_or_none()
        return language

async def update_user_wallet(user_id: int, wallet_address: str, private_key: str) -> bool:
    """Update user's wallet information."""
    # Encrypt the private key before storing
    encrypted_key = fernet.encrypt(private_key.encode()).decode()
    
    async with async_session_maker() as session:
        query = sa.select(Users).where(Users.user_id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.wallet_address = wallet_address
        user.encrypted_private_key = encrypted_key
        await session.commit()
        return True

async def get_user_wallet(user_id: int) -> Optional[str]:
    """Get user's wallet address."""
    async with async_session_maker() as session:
        query = sa.select(Users.wallet_address).where(Users.user_id == user_id)
        result = await session.execute(query)
        wallet_address = result.scalar_one_or_none()
        return wallet_address

async def get_user_private_key(user_id: int) -> Optional[str]:
    """Get user's decrypted private key."""
    async with async_session_maker() as session:
        query = sa.select(Users.encrypted_private_key).where(Users.user_id == user_id)
        result = await session.execute(query)
        encrypted_key = result.scalar_one_or_none()
        
        if not encrypted_key:
            return None
        
        # Decrypt the private key
        try:
            decrypted_key = fernet.decrypt(encrypted_key.encode()).decode()
            return decrypted_key
        except Exception as e:
            logging.error(f"Error decrypting private key for user {user_id}: {e}")
            return None

async def save_transaction(
    sender_id: Optional[int] = None,
    recipient_id: Optional[int] = None,
    sender_wallet: Optional[str] = None,
    recipient_wallet: Optional[str] = None,
    amount: float = 0.0,
    tx_hash: Optional[str] = None,
    tx_type: str = "tip",
    status: str = "completed",
    idempotency_key: Optional[str] = None
) -> bool:
    """Save a transaction to the database."""
    async with async_session_maker() as session:
        # Get wallet addresses if not provided
        if sender_id and not sender_wallet:
            sender_wallet = await get_user_wallet(sender_id)
        
        if recipient_id and not recipient_wallet:
            recipient_wallet = await get_user_wallet(recipient_id)
        
        # Create transaction record
        transaction = Transactions(
            sender_id=sender_id,
            recipient_id=recipient_id,
            sender_wallet=sender_wallet,
            recipient_wallet=recipient_wallet,
            amount=amount,
            tx_hash=tx_hash,
            tx_type=tx_type,
            status=status,
            idempotency_key=idempotency_key
        )
        
        session.add(transaction)
        await session.commit()
        return True

async def get_user_transactions(
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    count_only: bool = False
) -> Union[List[Dict[str, Any]], int]:
    """Get user's transaction history."""
    async with async_session_maker() as session:
        if count_only:
            # Count total transactions
            query = sa.select(sa.func.count(Transactions.id)).where(
                sa.or_(
                    Transactions.sender_id == user_id,
                    Transactions.recipient_id == user_id
                )
            )
            result = await session.execute(query)
            return result.scalar_one() or 0
        
        # Get transactions with pagination
        query = sa.select(Transactions).where(
            sa.or_(
                Transactions.sender_id == user_id,
                Transactions.recipient_id == user_id
            )
        ).order_by(
            Transactions.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await session.execute(query)
        transactions = result.scalars().all()
        
        return [
            {
                "id": tx.id,
                "sender_id": tx.sender_id,
                "recipient_id": tx.recipient_id,
                "sender_wallet": tx.sender_wallet,
                "recipient_wallet": tx.recipient_wallet,
                "amount": tx.amount,
                "tx_hash": tx.tx_hash,
                "tx_type": tx.tx_type,
                "status": tx.status,
                "created_at": tx.created_at
            }
            for tx in transactions
        ]

async def check_transaction_exists(idempotency_key: str) -> bool:
    """Check if a transaction with the given idempotency key exists."""
    if not idempotency_key:
        return False
    
    async with async_session_maker() as session:
        query = sa.select(sa.func.count(Transactions.id)).where(
            Transactions.idempotency_key == idempotency_key
        )
        result = await session.execute(query)
        count = result.scalar_one() or 0
        return count > 0

async def increment_referral_count(referrer_id: int) -> bool:
    """Increment the referral count for a user."""
    async with async_session_maker() as session:
        query = sa.select(Users).where(Users.user_id == referrer_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.referral_count = (user.referral_count or 0) + 1
        await session.commit()
        return True

async def get_user_referrals(user_id: int) -> Tuple[int, List[int]]:
    """Get user's referral count and list of referred users."""
    async with async_session_maker() as session:
        # Get referral count
        count_query = sa.select(Users.referral_count).where(Users.user_id == user_id)
        count_result = await session.execute(count_query)
        referral_count = count_result.scalar_one_or_none() or 0
        
        # Get referred users
        users_query = sa.select(Users.user_id).where(Users.referrer_id == user_id)
        users_result = await session.execute(users_query)
        referred_users = [user_id for user_id, in users_result]
        
        return referral_count, referred_users
