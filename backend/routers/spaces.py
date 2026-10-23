from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from core.security import get_current_user, require_roles, require_admin

router = APIRouter(prefix="/spaces", tags=["Espacios Académicos"])


@router.post("", response_model=schemas.SpaceResponse, status_code=201)
def create_space(
    data: schemas.SpaceCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles(models.UserRole.SPACE_ADMIN, models.UserRole.SYS_ADMIN)
    ),
):
    """Create a new academic space. Spec: SPC-01."""
    existing = db.query(models.Space).filter(models.Space.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un espacio con ese nombre")

    space = models.Space(**data.model_dump())
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


@router.get("", response_model=list[schemas.SpaceResponse])
def list_spaces(
    type: Optional[models.SpaceType] = None,
    is_active: Optional[bool] = None,
    min_capacity: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List spaces with optional filters. Spec: SPC-02."""
    query = db.query(models.Space).filter(models.Space.deleted_at == None)  # noqa: E711
    if type:
        query = query.filter(models.Space.type == type)
    if is_active is not None:
        query = query.filter(models.Space.is_active == is_active)
    if min_capacity:
        query = query.filter(models.Space.capacity >= min_capacity)
    return query.order_by(models.Space.name).all()


@router.get("/{space_id}", response_model=schemas.SpaceResponse)
def get_space(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get a single space by ID. Spec: SPC-02-B."""
    space = db.query(models.Space).filter(
        models.Space.id == space_id,
        models.Space.deleted_at == None  # noqa: E711
    ).first()
    if not space:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")
    return space


@router.put("/{space_id}", response_model=schemas.SpaceResponse)
def update_space(
    space_id: int,
    data: schemas.SpaceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles(models.UserRole.SPACE_ADMIN, models.UserRole.SYS_ADMIN)
    ),
):
    """Update space. Deactivating cancels pending/approved future reservations. Spec: SPC-03."""
    space = db.query(models.Space).filter(
        models.Space.id == space_id,
        models.Space.deleted_at == None  # noqa: E711
    ).first()
    if not space:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")

    update_data = data.model_dump(exclude_unset=True)

    # Check unique name if changing
    if "name" in update_data and update_data["name"] != space.name:
        dup = db.query(models.Space).filter(models.Space.name == update_data["name"]).first()
        if dup:
            raise HTTPException(status_code=409, detail="Ya existe un espacio con ese nombre")

    # If deactivating, cancel future PENDING/APPROVED reservations (Spec: SPC-03-B)
    cancelled_count = 0
    if update_data.get("is_active") is False and space.is_active:
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        future_res = db.query(models.Reservation).filter(
            models.Reservation.space_id == space_id,
            models.Reservation.status.in_([
                models.ReservationStatus.PENDING,
                models.ReservationStatus.APPROVED
            ]),
            models.Reservation.start_time > now,
        ).all()
        for r in future_res:
            r.status = models.ReservationStatus.CANCELLED
            r.cancelled_at = now
            r.cancellation_reason = "Espacio desactivado por administrador"
            cancelled_count += 1

    for field, value in update_data.items():
        setattr(space, field, value)

    db.commit()
    db.refresh(space)
    return space


@router.delete("/{space_id}", status_code=204)
def delete_space(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles(models.UserRole.SYS_ADMIN)
    ),
):
    """Soft-delete a space. Spec: SPC-04."""
    space = db.query(models.Space).filter(
        models.Space.id == space_id,
        models.Space.deleted_at == None  # noqa: E711
    ).first()
    if not space:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")

    from datetime import timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    future_active = db.query(models.Reservation).filter(
        models.Reservation.space_id == space_id,
        models.Reservation.status.in_([
            models.ReservationStatus.PENDING,
            models.ReservationStatus.APPROVED
        ]),
        models.Reservation.start_time > now,
    ).count()

    if future_active > 0:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: el espacio tiene reservas futuras activas. Desactívelo primero.",
        )

    space.deleted_at = now
    space.is_active = False
    db.commit()


@router.get("/{space_id}/availability", response_model=schemas.AvailabilityResponse)
def get_space_availability(
    space_id: int,
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get occupied time slots for a space in a date range. Spec: SPC-05."""
    space = db.query(models.Space).filter(
        models.Space.id == space_id,
        models.Space.deleted_at == None  # noqa: E711
    ).first()
    if not space:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")

    from services.reservation_service import get_availability
    occupied = get_availability(db, space_id, date_from, date_to)
    return schemas.AvailabilityResponse(
        space_id=space_id,
        date_from=date_from,
        date_to=date_to,
        occupied_slots=[
            schemas.AvailabilitySlot(
                reservation_id=r.id,
                start_time=r.start_time,
                end_time=r.end_time,
                status=r.status,
            )
            for r in occupied
        ],
    )
