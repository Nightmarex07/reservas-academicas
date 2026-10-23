import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from database import Base


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    SPACE_ADMIN = "SPACE_ADMIN"
    SYS_ADMIN = "SYS_ADMIN"


class SpaceType(str, enum.Enum):
    LABORATORY = "LABORATORY"
    AUDITORIUM = "AUDITORIUM"
    COMPUTER_ROOM = "COMPUTER_ROOM"


class ReservationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """Represents a system user. Spec: user-management USR-01."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    reservations = relationship("Reservation", back_populates="user", foreign_keys="Reservation.user_id")


class Space(Base):
    """Represents an academic space. Spec: space-management SPC-01."""
    __tablename__ = "spaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    type = Column(SAEnum(SpaceType), nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    reservations = relationship("Reservation", back_populates="space")


class Reservation(Base):
    """Represents a space reservation. Spec: reservation-core RES-01."""
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    space_id = Column(Integer, ForeignKey("spaces.id"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    purpose = Column(String(255), nullable=False)
    status = Column(
        SAEnum(ReservationStatus),
        nullable=False,
        default=ReservationStatus.PENDING
    )
    # Approval tracking
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    # Rejection tracking
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    # Cancellation tracking
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="reservations", foreign_keys=[user_id])
    space = relationship("Space", back_populates="reservations")
    approver = relationship("User", foreign_keys=[approved_by])
    rejecter = relationship("User", foreign_keys=[rejected_by])
    canceller = relationship("User", foreign_keys=[cancelled_by])
