"""Shared login helpers for users and admins (incl. MongoDB Compass edits)."""
from users.models import User, Admin, verify_password_with_migration


def normalize_login_email(email):
    return (email or "").strip()


def normalize_login_password(password):
    return (password or "").strip()


def _password_matches(instance, password):
    try:
        instance.reload()
    except Exception:
        pass
    return verify_password_with_migration(
        instance,
        password,
        instance.set_password,
    )


def _find_user_by_email(email):
    return User.objects(email__iexact=email).first()


def _find_admin_by_email(email):
    return Admin.objects(email__iexact=email).first()


def _find_user_admin_by_email(email):
    """Admin account stored in users collection with role=admin."""
    return User.objects(email__iexact=email, role="admin").first()


def authenticate_user_or_admin(email, password):
    """
    Authenticate against users and admins collections.
    Supports plain text, bcrypt, and Django hashed passwords from Compass edits.
    Returns dict: {account_type: 'user'|'admin', account: model} or None.
    """
    email = normalize_login_email(email)
    password = normalize_login_password(password)
    if not email or not password:
        return None

    # 1) Student/general user in users collection
    user = _find_user_by_email(email)
    if user and _password_matches(user, password):
        return {"account_type": "user", "account": user}

    # 2) Admin in admins collection (Compass admins collection)
    admin = _find_admin_by_email(email)
    if admin and _password_matches(admin, password):
        if not getattr(admin, "is_active", True):
            return {"inactive_admin": True, "account": admin}
        return {"account_type": "admin", "account": admin}

    # 3) Admin stored in users collection with role=admin
    user_admin = _find_user_admin_by_email(email)
    if user_admin and user_admin.id != getattr(user, "id", None):
        if _password_matches(user_admin, password):
            return {"account_type": "user", "account": user_admin}

    return None
