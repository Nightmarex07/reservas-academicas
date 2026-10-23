import logging
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import models
from models import ReservationStatus
from schemas import ReservationCreateRequest, MAX_RESERVATION_HOURS

logger = logging.getLogger(__name__)

MAX_DURATION_MINUTES = MAX_RESERVATION_HOURS * 60


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _lock(query, db: Session):
    try:
        bind = db.get_bind()
        if bind and bind.dialect.name == "sqlite":
            return query
    except Exception:
        pass
    return query.with_for_update()


def check_time_conflict(
    db: Session,
    space_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_reservation_id: Optional[int] = None,
) -> List[models.Reservation]:
    """
    Detect overlapping reservations for a space.
    Conflict condition: existing.start < new.end AND existing.end > new.start
    Only checks PENDING and APPROVED reservations. Spec: RES-03.
    """
    query = db.query(models.Reservation).filter(
        models.Reservation.space_id == space_id,
        models.Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.APPROVED]),
        models.Reservation.start_time < end_time,
        models.Reservation.end_time > start_time,
    )
    if exclude_reservation_id:
        query = query.filter(models.Reservation.id != exclude_reservation_id)
    return query.all()


def create_reservation(
    db: Session,
    user_id: int,
    data: ReservationCreateRequest,
) -> models.Reservation:
    """
    Create a reservation with conflict detection.
    Uses SELECT FOR UPDATE via with_for_update() to prevent race conditions. Spec: RES-03-E.
    Duration validation is enforced at schema level (schemas.py). Spec: RES-02.
    """
    # Normalize datetimes to naive UTC
    start = data.start_time.replace(tzinfo=None) if data.start_time.tzinfo else data.start_time
    end = data.end_time.replace(tzinfo=None) if data.end_time.tzinfo else data.end_time
    now = utcnow_naive()

    if start <= now:
        raise ValueError("La fecha de inicio debe ser futura")

    # Verify space exists and is active
    space = db.query(models.Space).filter(
        models.Space.id == data.space_id,
        models.Space.is_active == True,  # noqa: E712
        models.Space.deleted_at == None,  # noqa: E711
    ).first()
    if not space:
        raise LookupError("Espacio no encontrado o no disponible")

    # Lock rows to prevent race conditions (Spec: RES-03-E)
    conflicts_query = db.query(models.Reservation).filter(
        models.Reservation.space_id == data.space_id,
        models.Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.APPROVED]),
        models.Reservation.start_time < end,
        models.Reservation.end_time > start,
    )
    conflicts = _lock(conflicts_query, db).all()

    if conflicts:
        raise ConflictError(
            "El espacio no está disponible en el horario seleccionado",
            conflicts=conflicts,
        )

    reservation = models.Reservation(
        user_id=user_id,
        space_id=data.space_id,
        start_time=start,
        end_time=end,
        purpose=data.purpose,
        status=ReservationStatus.PENDING,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def approve_reservation(
    db: Session,
    reservation_id: int,
    admin_id: int,
) -> models.Reservation:
    """Approve a PENDING reservation. Spec: APR-02."""
    reservation_query = db.query(models.Reservation).filter(models.Reservation.id == reservation_id)
    reservation = _lock(reservation_query, db).first()

    if not reservation:
        raise LookupError("Reserva no encontrada")

    if reservation.status != ReservationStatus.PENDING:
        raise StateError("Solo se pueden aprobar reservas en estado PENDING")

    # Double-check for conflicts with already-APPROVED reservations (Spec: APR-02-B)
    conflicts = check_time_conflict(
        db,
        reservation.space_id,
        reservation.start_time,
        reservation.end_time,
        exclude_reservation_id=reservation_id,
    )
    # Filter to only APPROVED conflicts
    approved_conflicts = [c for c in conflicts if c.status == ReservationStatus.APPROVED]
    if approved_conflicts:
        raise ConflictError(
            "No se puede aprobar: existe un conflicto de horario con una reserva ya aprobada",
            conflicts=approved_conflicts,
        )

    reservation.status = ReservationStatus.APPROVED
    reservation.approved_by = admin_id
    reservation.approved_at = utcnow_naive()
    db.commit()
    db.refresh(reservation)
    return reservation


def reject_reservation(
    db: Session,
    reservation_id: int,
    admin_id: int,
    reason: str,
) -> models.Reservation:
    """Reject a PENDING reservation with a reason. Spec: APR-03."""
    reservation_query = db.query(models.Reservation).filter(models.Reservation.id == reservation_id)
    reservation = _lock(reservation_query, db).first()

    if not reservation:
        raise LookupError("Reserva no encontrada")

    if reservation.status != ReservationStatus.PENDING:
        raise StateError("Solo se pueden rechazar reservas en estado PENDING")

    reservation.status = ReservationStatus.REJECTED
    reservation.rejected_by = admin_id
    reservation.rejected_at = utcnow_naive()
    reservation.rejection_reason = reason
    db.commit()
    db.refresh(reservation)
    return reservation


def cancel_reservation(
    db: Session,
    reservation_id: int,
    requesting_user: models.User,
    reason: Optional[str] = None,
) -> models.Reservation:
    """Cancel a reservation. Spec: HST-02."""
    reservation_query = db.query(models.Reservation).filter(models.Reservation.id == reservation_id)
    reservation = _lock(reservation_query, db).first()

    if not reservation:
        raise LookupError("Reserva no encontrada")

    # Authorization: owner or admin
    is_owner = reservation.user_id == requesting_user.id
    is_admin = requesting_user.role in {models.UserRole.SPACE_ADMIN, models.UserRole.SYS_ADMIN}
    if not is_owner and not is_admin:
        raise PermissionError("No tienes permisos para cancelar esta reserva")

    if reservation.status in {ReservationStatus.CANCELLED, ReservationStatus.REJECTED}:
        raise StateError("Esta reserva ya no puede ser cancelada")

    now = utcnow_naive()
    if reservation.start_time <= now:
        raise StateError("No se puede cancelar una reserva cuya fecha de inicio ya pasó")

    reservation.status = ReservationStatus.CANCELLED
    reservation.cancelled_at = now
    reservation.cancelled_by = requesting_user.id
    reservation.cancellation_reason = reason
    db.commit()
    db.refresh(reservation)
    return reservation


def get_availability(
    db: Session,
    space_id: int,
    start_time: datetime,
    end_time: datetime,
) -> List[models.Reservation]:
    """Return all active reservations overlapping the given window. Spec: RES-04."""
    start = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
    end = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
    return check_time_conflict(db, space_id, start, end)


# ─── Custom Exceptions ────────────────────────────────────────────────────────

class ConflictError(Exception):
    def __init__(self, message: str, conflicts: list = None):
        super().__init__(message)
        self.conflicts = conflicts or []


class StateError(Exception):
    pass
