from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from core.security import get_current_user
from services import reservation_service as svc
from services import notification_service as notify

router = APIRouter(prefix="/reservations", tags=["Reservas"])


@router.post("", response_model=schemas.ReservationResponse, status_code=201)
def create_reservation(
    data: schemas.ReservationCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new reservation. Spec: RES-01, RES-02, RES-03."""
    try:
        reservation = svc.create_reservation(db, current_user.id, data)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except svc.ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Async notification — does NOT block response. Spec: NOT-01.
    space = db.query(models.Space).filter(models.Space.id == reservation.space_id).first()
    background_tasks.add_task(
        notify.send_reservation_created,
        to=current_user.email,
        user_name=current_user.full_name,
        reservation_id=reservation.id,
        space_name=space.name if space else str(reservation.space_id),
        start_time=reservation.start_time,
        end_time=reservation.end_time,
    )
    return reservation


@router.get("/availability", response_model=schemas.AvailabilityCheckResponse)
def check_availability(
    space_id: int = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Check if a space is available for a given time window. Spec: RES-04."""
    conflicts = svc.get_availability(db, space_id, start_time, end_time)
    return schemas.AvailabilityCheckResponse(
        available=len(conflicts) == 0,
        conflicts=[
            schemas.AvailabilitySlot(
                reservation_id=r.id,
                start_time=r.start_time,
                end_time=r.end_time,
                status=r.status,
            )
            for r in conflicts
        ],
    )


@router.get("/{reservation_id}", response_model=schemas.ReservationResponse)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get reservation detail. Owner or admin only. Spec: HST-04."""
    reservation = db.query(models.Reservation).filter(
        models.Reservation.id == reservation_id
    ).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    is_owner = reservation.user_id == current_user.id
    is_admin = current_user.role in {models.UserRole.SPACE_ADMIN, models.UserRole.SYS_ADMIN}
    if not is_owner and not is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver esta reserva")

    return reservation


@router.delete("/{reservation_id}", response_model=schemas.ReservationResponse)
def cancel_reservation(
    reservation_id: int,
    data: Optional[schemas.CancelRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Cancel a reservation. Spec: HST-02."""
    reason = data.reason if data else None
    try:
        reservation = svc.cancel_reservation(db, reservation_id, current_user, reason)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except svc.StateError as e:
        raise HTTPException(status_code=409, detail=str(e))

    space = db.query(models.Space).filter(models.Space.id == reservation.space_id).first()
    owner = db.query(models.User).filter(models.User.id == reservation.user_id).first()
    by_admin = current_user.id != reservation.user_id
    if owner:
        background_tasks.add_task(
            notify.send_reservation_cancelled,
            to=owner.email,
            user_name=owner.full_name,
            reservation_id=reservation.id,
            space_name=space.name if space else "",
            by_admin=by_admin,
            reason=reason,
        )
    return reservation
