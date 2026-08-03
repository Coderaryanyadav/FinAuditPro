import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from database.database import get_session, init_db
from database.models import User
from security.auth import PasswordHasher

init_db()
with get_session() as session:
    user = session.query(User).filter_by(email='admin@finauditpro.com').first()
    if not user:
        pwd = PasswordHasher.hash_password('Admin@123')
        user = User(username='admin', email='admin@finauditpro.com', password_hash=pwd, role='Partner')
        session.add(user)
        session.commit()
        print('Created default admin: admin@finauditpro.com / Admin@123')
    else:
        print('Admin already exists: admin@finauditpro.com')
        # reset password just in case
        user.password_hash = PasswordHasher.hash_password('Admin@123')
        session.commit()
        print('Password reset to: Admin@123')
