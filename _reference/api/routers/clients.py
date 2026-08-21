from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from api.middleware.rbac import require_permission
from api.schemas.client import ClientCreate, ClientUpdate, ClientRead
from database.models import User
from database.repositories.client_repo import ClientRepository
from services.client_service import ClientService
from security.rbac import Permission
from core.exceptions import ValidationError, DuplicateRecordError, EntityNotFoundError, AuthError

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=List[ClientRead])
def list_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all clients."""
    client_repo = ClientRepository(db)
    client_service = ClientService(client_repo)
    return client_service.get_all_clients()


@router.get("/search", response_model=List[ClientRead])
def search_clients(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search clients by name query."""
    client_repo = ClientRepository(db)
    client_service = ClientService(client_repo)
    return client_service.search_clients(q)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve single client by ID."""
    client_repo = ClientRepository(db)
    client_service = ClientService(client_repo)
    try:
        return client_service.get_client(client_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_44_NOT_FOUND, detail=str(e))


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    request: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_CLIENTS))
):
    """Create new client record."""
    client_repo = ClientRepository(db)
    client_service = ClientService(client_repo)
    try:
        return client_service.create_client(
            name=request.name,
            gst_number=request.gst_number,
            pan_number=request.pan_number,
            cin=request.cin,
            industry_id=request.industry_id,
            registered_address=request.registered_address,
            industry_name=request.industry_name
        )
    except (ValidationError, DuplicateRecordError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: int,
    request: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.MANAGE_CLIENTS))
):
    """Update client statutory info."""
    client_repo = ClientRepository(db)
    client_service = ClientService(client_repo)
    try:
        return client_service.update_client(
            client_id=client_id,
            gst_number=request.gst_number,
            pan_number=request.pan_number,
            industry=request.industry
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
