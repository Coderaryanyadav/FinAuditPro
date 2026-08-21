from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import Client, ClientIndustry

class ClientRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Client]:
        """Retrieve all clients."""
        return self.session.query(Client).all()

    def get_by_id(self, client_id: int) -> Optional[Client]:
        """Retrieve a client by ID."""
        return self.session.query(Client).filter(Client.id == client_id).first()

    def search(self, query: str) -> List[Client]:
        """Search clients by name, GST, or PAN."""
        search_term = f"%{query}%"
        return self.session.query(Client).filter(
            (Client.name.ilike(search_term)) |
            (Client.gst_number.ilike(search_term)) |
            (Client.pan_number.ilike(search_term))
        ).all()

    def create(self, name: str, gst_number: str = None, pan_number: str = None, cin: str = None, industry_id: int = None, registered_address: str = None) -> Client:
        """Create and persist a new client."""
        client = Client(
            name=name,
            gst_number=gst_number,
            pan_number=pan_number,
            cin=cin,
            industry_id=industry_id,
            registered_address=registered_address
        )
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        return client

    def get_total_count(self) -> int:
        """Get the total number of clients."""
        return self.session.query(Client).count()

    def get_all_industries(self) -> List[ClientIndustry]:
        """Retrieve all industries."""
        return self.session.query(ClientIndustry).all()
