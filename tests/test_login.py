
import sys; sys.path.append('src')
from database.database import get_session
from database.models import User
from security.auth import PasswordHasher
s=get_session()
session=s.__enter__()
user=session.query(User).filter_by(email='admin@finauditpro.com').first()
print(user.username if user else 'No user')
print(PasswordHasher.verify_password('Admin@123', user.password_hash) if user else 'N/A')

