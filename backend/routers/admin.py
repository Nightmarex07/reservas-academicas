from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from core.security import require_roles, require_sys_admin, get_current_user
from services import reservation_service as svc
from services import notification_service as notify

router = APIRouter(prefix="/admin", tags=["Administración"])

_ADMIN_ROLES = (models.UserRole.SPACE_ADMIN, models.UserRole.SYS_ADMIN)


@router.get("/reservations")
def list_all_reservations(
    status: Optional[str] = None,
    space_id: Optional[int] = None,
    user_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(*_ADMIN_ROLES)),
):
    """List all reservations with filters. Spec: APR-01, HST-03."""
    if page_size > 100:
        page_size = 100
    query = db.query(models.Reservation)
    if status:
        try:
            query = query.filter(models.Reservation.status == models.ReservationStatus(status))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Estado inválido: {status}")
    if space_id:
        query = query.filter(models.Reservation.space_id == space_id)
    if user_id:
        query = query.filter(models.Reservation.user_id == user_id)
    if date_from:
        df = date_from.replace(tzinfo=None) if date_from.tzinfo else date_from
        query = query.filter(models.Reservation.start_time >= df)
    if date_to:
        dt = date_to.replace(tzinfo=None) if date_to.tzinfo else date_to
        query = query.filter(models.Reservation.end_time <= dt)

    total = query.count()
    items = (
        query.order_by(models.Reservation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [schemas.ReservationResponse.model_validate(r) for r in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.put("/reservations/{reservation_id}/approve", response_model=schemas.ReservationResponse)
def approve_reservation(
    reservation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(*_ADMIN_ROLES)),
):
    """Approve a PENDING reservation. Spec: APR-02."""
    try:
        reservation = svc.approve_reservation(db, reservation_id, current_user.id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except svc.StateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except svc.ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Async notification — Spec: NOT-02
    owner = db.query(models.User).filter(models.User.id == reservation.user_id).first()
    space = db.query(models.Space).filter(models.Space.id == reservation.space_id).first()
    if owner:
        background_tasks.add_task(
            notify.send_reservation_approved,
            to=owner.email,
            user_name=owner.full_name,
            reservation_id=reservation.id,
            space_name=space.name if space else "",
            start_time=reservation.start_time,
            end_time=reservation.end_time,
        )
    return reservation


@router.put("/reservations/{reservation_id}/reject", response_model=schemas.ReservationResponse)
def reject_reservation(
    reservation_id: int,
    data: schemas.RejectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(*_ADMIN_ROLES)),
):
    """Reject a PENDING reservation with a reason. Spec: APR-03."""
    try:
        reservation = svc.reject_reservation(db, reservation_id, current_user.id, data.reason)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except svc.StateError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Async notification — Spec: NOT-03
    owner = db.query(models.User).filter(models.User.id == reservation.user_id).first()
    space = db.query(models.Space).filter(models.Space.id == reservation.space_id).first()
    if owner:
        background_tasks.add_task(
            notify.send_reservation_rejected,
            to=owner.email,
            user_name=owner.full_name,
            reservation_id=reservation.id,
            space_name=space.name if space else "",
            reason=data.reason,
        )
    return reservation


@router.put("/users/{user_id}/role", response_model=schemas.UserResponse)
def update_user_role(
    user_id: int,
    data: schemas.UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.SYS_ADMIN)),
):
    """Change a user's role. SYS_ADMIN only. Spec: USR-03-B."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.role = data.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/reports/usage")
def usage_report(
    space_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(*_ADMIN_ROLES)),
):
    """Basic usage report: count reservations by space and status."""
    from sqlalchemy import func
    query = db.query(
        models.Space.id,
        models.Space.name,
        models.Space.type,
        models.Reservation.status,
        func.count(models.Reservation.id).label("count"),
    ).join(models.Reservation, models.Space.id == models.Reservation.space_id, isouter=True)

    if space_id:
        query = query.filter(models.Space.id == space_id)
    if date_from:
        df = date_from.replace(tzinfo=None) if date_from.tzinfo else date_from
        query = query.filter(models.Reservation.start_time >= df)
    if date_to:
        dt = date_to.replace(tzinfo=None) if date_to.tzinfo else date_to
        query = query.filter(models.Reservation.end_time <= dt)

    rows = query.group_by(models.Space.id, models.Space.name, models.Space.type, models.Reservation.status).all()
    return [
        {"space_id": r.id, "space_name": r.name, "type": r.type, "status": r.status, "count": r.count}
        for r in rows
    ]
