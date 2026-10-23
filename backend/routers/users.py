from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from core.security import get_current_user, require_roles

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/me", response_model=schemas.UserResponse)
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    """Return authenticated user's profile. Spec: USR-04."""
    return current_user


@router.get("/me/reservations")
def get_my_reservations(
    status: str = None,
    space_id: int = None,
    page: int = 1,
    page_size: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return paginated reservation history for the current user. Spec: HST-01."""
    if page_size > 100:
        page_size = 100

    query = db.query(models.Reservation).filter(
        models.Reservation.user_id == current_user.id
    )
    if status:
        try:
            status_enum = models.ReservationStatus(status)
            query = query.filter(models.Reservation.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Estado inválido: {status}")
    if space_id:
        query = query.filter(models.Reservation.space_id == space_id)

    total = query.count()
    items = (
        query.order_by(models.Reservation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": [schemas.ReservationResponse.model_validate(r) for r in items],
            "total": total, "page": page, "page_size": page_size}
