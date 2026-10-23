from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, model_validator
from models import UserRole, SpaceType, ReservationStatus


# ─── AUTH ───────────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─── USER ────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserRoleUpdateRequest(BaseModel):
    role: UserRole


# ─── SPACE ───────────────────────────────────────────────────────────────────

class SpaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type: SpaceType
    capacity: int = Field(..., ge=1, description="Capacidad mínima: 1")
    location: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class SpaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    type: Optional[SpaceType] = None
    capacity: Optional[int] = Field(None, ge=1)
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SpaceResponse(BaseModel):
    id: int
    name: str
    type: SpaceType
    capacity: int
    location: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailabilitySlot(BaseModel):
    reservation_id: int
    start_time: datetime
    end_time: datetime
    status: ReservationStatus


class AvailabilityResponse(BaseModel):
    space_id: int
    date_from: datetime
    date_to: datetime
    occupied_slots: List[AvailabilitySlot]


class AvailabilityCheckResponse(BaseModel):
    available: bool
    conflicts: List[AvailabilitySlot]


# ─── RESERVATION ─────────────────────────────────────────────────────────────

MAX_RESERVATION_HOURS = 4


class ReservationCreateRequest(BaseModel):
    space_id: int
    start_time: datetime
    end_time: datetime
    purpose: str = Field(..., min_length=3, max_length=255)

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        duration_seconds = (self.end_time - self.start_time).total_seconds()
        # 4 hours = 14400 seconds. Allow 1-second margin for sub-second jitter
        if duration_seconds > (MAX_RESERVATION_HOURS * 3600) + 1:
            raise ValueError(
                f"La duración máxima de una reserva es de {MAX_RESERVATION_HOURS} horas consecutivas"
            )
        return self


class ReservationResponse(BaseModel):
    id: int
    space_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    purpose: str
    status: ReservationStatus
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejected_by: Optional[int]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    cancelled_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReservationDetailResponse(ReservationResponse):
    space: SpaceResponse
    user: UserResponse


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class ApproveRequest(BaseModel):
    pass  # No body needed; ID is in path


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Motivo del rechazo (obligatorio)")


class CancelRequest(BaseModel):
    reason: Optional[str] = None
