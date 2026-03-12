from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    plan = Column(String, default="free")
    is_admin = Column(Boolean, default=False)
    can_generate = Column(Boolean, default=False)  # admin nadaje prawo ręcznie
    terms_accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    kosztorysy = relationship("Kosztorys", back_populates="owner")


class Kosztorys(Base):
    __tablename__ = "kosztorysy"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    filename = Column(String)
    positions_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)

    owner = relationship("User", back_populates="kosztorysy")

    __table_args__ = (Index("idx_kosztorysy_user_created", "user_id", "created_at"),)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable — gość też może oceniać
    rating = Column(Integer, nullable=False)   # 1–5
    message = Column(Text, nullable=True)
    context = Column(String, nullable=True)    # np. "after_generate", "general"
    created_at = Column(DateTime, default=_utcnow)


class BetaApplication(Base):
    __tablename__ = "beta_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    firma = Column(String, nullable=False)
    stanowisko = Column(String, nullable=False)
    doswiadczenie = Column(String, nullable=False)
    cel = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=_utcnow)


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String, nullable=False)
    category = Column(String, nullable=False)  # opinia / zapytanie / blad / inne
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
