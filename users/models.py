


import mongoengine as me
import bcrypt
from bson import ObjectId
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password


def _normalize_credential(value):
    if value is None:
        return ""
    return str(value).strip()


def verify_password_with_migration(instance, raw_password, hash_password):
    """
    Verify password against stored value and support direct MongoDB Compass edits.
    Accepts bcrypt hashes, Django hashes, and plain text (auto-migrated on login).
    """
    stored_password = _normalize_credential(getattr(instance, "password", ""))
    raw_password = _normalize_credential(raw_password)

    if not stored_password or not raw_password:
        return False

    # Django-style hash (admins collection / copied hashes)
    if stored_password.startswith(("pbkdf2_", "argon2", "bcrypt_sha256")):
        if check_password(raw_password, stored_password):
            return True

    # bcrypt hash (users collection)
    if stored_password.startswith("$2"):
        try:
            if bcrypt.checkpw(
                raw_password.encode("utf-8"),
                stored_password.encode("utf-8"),
            ):
                return True
        except (ValueError, TypeError):
            pass

    # Plain text password updated directly in MongoDB Compass
    if stored_password == raw_password:
        try:
            hash_password(raw_password)
            instance.save()
        except Exception:
            # Allow login even if auto-hash migration fails after Compass edit
            pass
        return True

    return False


class User(me.Document):
    fullname = me.StringField(required=True)
    email = me.StringField(required=True, unique=True)
    phone_number = me.StringField(required=True)
    role = me.StringField(required=True, choices=['student', 'admin'], default='student')
    location = me.StringField()
    profile_picture = me.StringField(default="")  # Store base64 or URL
    password = me.StringField(required=True)  # hashed
    # confirm_password = me.StringField(required=True) 
    enrolled_courses = me.ListField(me.GenericReferenceField())  # Can hold both Course and Category references
    

    meta = {'collection': 'users'}

    def set_password(self, raw_password):
        self.password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode()

    def check_password(self, raw_password):
        return verify_password_with_migration(self, raw_password, self.set_password)


class Admin(me.Document):
    _id = me.ObjectIdField(default=ObjectId, primary_key=True)
    name = me.StringField(required=True, max_length=100)
    email = me.EmailField(required=True, unique=True)
    password = me.StringField(required=True)
    # confirm_password = me.StringField(required=True)
    role = me.StringField(default='admin')
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'admins'}

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return verify_password_with_migration(self, raw_password, self.set_password)


class PasswordResetToken(me.Document):
    email = me.StringField(required=True)
    otp = me.StringField(required=True)
    token = me.StringField(default=None, null=True)  # Optional field for backward compatibility with existing index
    created_at = me.DateTimeField(default=datetime.utcnow)
    expires_at = me.DateTimeField(required=True)
    used = me.BooleanField(default=False)
    
    meta = {
        'collection': 'password_reset_tokens',
        'indexes': [
            {'fields': ['email', 'otp', 'used'], 'unique': False},
        ]
    }
