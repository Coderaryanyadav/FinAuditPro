import re
from typing import List, Optional
from core.exceptions import ValidationError, DuplicateRecordError, EntityNotFoundError, AuthError
from database.repositories.client_repo import ClientRepository
from database.models import Client
from security.security_manager import SecurityManager
from security.rbac import Permission

class ClientService:
    """
    Service responsible for managing Client entities with RBAC permission gates.
    """

    def __init__(self, client_repo: ClientRepository):
        self.client_repo = client_repo

    def validate_pan(self, pan: str) -> bool:
        """Validate format of Indian Permanent Account Number (PAN)."""
        pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
        return bool(re.match(pattern, pan))

    def validate_gstin(self, gstin: str) -> bool:
        """Validate format of Indian Goods and Services Tax Identification Number (GSTIN)."""
        pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
        return bool(re.match(pattern, gstin))

    def create_client(self, name: str, gst_number: str = None, pan_number: str = None, cin: str = None, industry_id: int = None, registered_address: str = None, industry_name: str = None) -> Client:
        """Create a new client with strict validation and RBAC enforcement."""
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.MANAGE_CLIENTS):
            raise AuthError("User role lacks permission MANAGE_CLIENTS to create a client.")

        if not name:
            raise ValidationError("Client name is required.")

        if gst_number and not self.validate_gstin(gst_number):
            raise ValidationError(f"Invalid GSTIN format: {gst_number}")
            
        if pan_number and not self.validate_pan(pan_number):
            raise ValidationError(f"Invalid PAN format: {pan_number}")

        # Check for duplicates based on name
        existing = self.client_repo.search(name)
        if any(c.name.lower() == name.lower() for c in existing):
            raise DuplicateRecordError(f"Client with name '{name}' already exists.")

        if industry_name and not industry_id:
            from database.models import ClientIndustry
            ind = self.client_repo.session.query(ClientIndustry).filter_by(industry_name=industry_name).first()
            if not ind:
                ind = ClientIndustry(industry_name=industry_name)
                self.client_repo.session.add(ind)
                self.client_repo.session.flush()
            industry_id = ind.id

        return self.client_repo.create(
            name=name, 
            gst_number=gst_number, 
            pan_number=pan_number, 
            cin=cin, 
            industry_id=industry_id, 
            registered_address=registered_address
        )

    def get_all_clients(self) -> List[Client]:
        """Retrieve all registered clients."""
        return self.client_repo.get_all()

    def get_client(self, client_id: int) -> Client:
        client = self.client_repo.get_by_id(client_id)
        if not client:
            raise EntityNotFoundError(f"Client with ID {client_id} not found.")
        return client

    def search_clients(self, query: str) -> List[Client]:
        return self.client_repo.search(query)

    def get_all_industries(self) -> List:
        return self.client_repo.get_all_industries()

    def update_client(self, client_id: int, gst_number: str = None, pan_number: str = None, industry: str = None) -> Client:
        """Update client statutory info with validation."""
        client = self.get_client(client_id)
        if gst_number and not self.validate_gstin(gst_number):
            raise ValidationError(f"Invalid GSTIN format: {gst_number}")

        if pan_number and not self.validate_pan(pan_number):
            raise ValidationError(f"Invalid PAN format: {pan_number}")

        if gst_number is not None:
            client.gst_number = gst_number
        if pan_number is not None:
            client.pan_number = pan_number
        if industry is not None:
            client.industry = industry

        self.client_repo.session.commit()
        return client
