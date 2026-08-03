
"""
FinAuditPro — Administrator Password Reset & Account Recovery CLI Tool.
Usage:
    python scripts/fix_admin.py --password <NewPassword>
    python scripts/fix_admin.py --email admin@finauditpro.com --password <NewPassword>
    python scripts/fix_admin.py --unlock
"""

import sys
import os
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from database.database import init_db, get_session
from database.models import User
from security.auth import PasswordHasher


def main():
    parser = argparse.ArgumentParser(
        description="FinAuditPro Air-Gapped Administrator Recovery & Password Reset CLI Tool."
    )
    parser.add_argument(
        "--email", "-e",
        default="admin@finauditpro.com",
        help="Email address of the account to reset/create (default: admin@finauditpro.com)"
    )
    parser.add_argument(
        "--password", "-p",
        default=None,
        help="New password to assign to the target administrator account"
    )
    parser.add_argument(
        "--role", "-r",
        default="Administrator",
        help="Role for new administrator account (default: Administrator)"
    )
    parser.add_argument(
        "--unlock", "-u",
        action="store_true",
        help="Clear login lockouts and ensure user is active"
    )
    parser.add_argument(
        "--list-users", "-l",
        action="store_true",
        help="List all registered user accounts in the database"
    )

    args = parser.parse_args()

    try:
        init_db()
        with get_session() as session:
            if args.list_users:
                users = session.query(User).all()
                print(f"\nRegistered Accounts ({len(users)} total):")
                for u in users:
                    print(f"  - ID: {u.id} | Username: {u.username} | Email: {u.email} | Role: {u.role} | Active: {u.is_active}")
                return

            user = session.query(User).filter((User.email == args.email) | (User.username == args.email)).first()

            target_pass = args.password or "Admin@123"

            if not user:
                hashed = PasswordHasher.hash_password(target_pass)
                username_part = args.email.split("@")[0]
                new_user = User(
                    username=username_part,
                    email=args.email,
                    password_hash=hashed,
                    role=args.role,
                    is_active=True
                )
                session.add(new_user)
                session.commit()
                print(f"SUCCESS: Created new administrator account '{args.email}' with password '{target_pass}'.")
            else:
                if args.password:
                    user.password_hash = PasswordHasher.hash_password(target_pass)
                if args.unlock or not user.is_active:
                    user.is_active = True
                session.commit()
                print(f"SUCCESS: Updated account '{user.email}'. Password reset: {'YES' if args.password else 'NO'}. Account unlocked: YES.")

            # Clear lockout file if requested or during password reset
            lockout_file = os.path.join(os.path.dirname(__file__), "..", "data", ".login_lockouts.json")
            if os.path.exists(lockout_file):
                try:
                    os.remove(lockout_file)
                    print("SUCCESS: Cleared persistent login lockout file.")
                except Exception:
                    pass

    except Exception as e:
        print(f"ERROR: Recovery operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


