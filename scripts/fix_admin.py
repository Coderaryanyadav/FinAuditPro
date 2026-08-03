
import sys; sys.path.append('src')
from database.database import get_session
from database.models import User
from security.auth import PasswordHasher
try:
    with get_session() as s:
        user = s.query(User).filter_by(email='admin@finauditpro.com').first()
        if not user:
            hashed = PasswordHasher.hash_password('Admin@123')
            admin = User(
                username='admin',
                email='admin@finauditpro.com',
                password_hash=hashed,
                role='Audit Partner',
                is_active=True
            )
            s.add(admin)
            s.commit()
            print('Admin user created successfully!')
        else:
            print('User already exists.')
except Exception as e:
    print(f'Error: {e}')

