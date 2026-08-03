
from database.database import init_db, get_session
from database.models import User
from security.auth import PasswordHasher


def run_login_check():
    init_db()
    with get_session() as session:
        user = session.query(User).filter_by(email='admin@finauditpro.com').first()
        print(user.username if user else 'No user')
        print(PasswordHasher.verify_password('Admin@123', user.password_hash) if user else 'N/A')


if __name__ == '__main__':
    run_login_check()


