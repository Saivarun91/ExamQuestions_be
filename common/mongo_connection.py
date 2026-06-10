import logging
import os

import certifi
from mongoengine import connect
from mongoengine.connection import get_connection
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

_mongo_connected = False
_mongo_unavailable = False

PUBLIC_SETTINGS_FALLBACK = {
    "success": True,
    "site_name": "",
    "logo_url": "",
    "contact_email": "",
    "contact_phone": "",
    "contact_address": "",
    "contact_website": "",
    "providers_carousel_speed": 1500,
    "providers_logo_size": 80,
    "social_facebook_url": "",
    "social_twitter_url": "",
    "social_linkedin_url": "",
    "social_youtube_url": "",
    "social_instagram_url": "",
    "font_family": "Poppins",
    "font_size": "16",
}


def is_mongo_unavailable():
    return _mongo_unavailable


def connect_mongodb():
    """Connect MongoEngine once using MONGO_URI / MONGO_DB from environment."""
    global _mongo_connected, _mongo_unavailable

    if _mongo_connected:
        return True

    uri = (os.environ.get("MONGO_URI") or "").strip()
    db_name = (os.environ.get("MONGO_DB") or "mock-test").strip()

    if not uri:
        logger.warning("MONGO_URI is not set; MongoDB features are disabled.")
        _mongo_unavailable = True
        return False

    try:
        connect_kwargs = {
            "db": db_name,
            "host": uri,
            "alias": "default",
            "retryWrites": True,
            "serverSelectionTimeoutMS": 10000,
        }
        if uri.startswith("mongodb+srv://") or "mongodb.net" in uri:
            connect_kwargs["tlsCAFile"] = certifi.where()

        connect(**connect_kwargs)
        get_connection().server_info()
        _mongo_connected = True
        _mongo_unavailable = False
        logger.info("MongoDB connected (db=%s)", db_name)
        return True
    except Exception as error:
        _mongo_unavailable = True
        logger.warning("MongoDB connection failed: %s", error)
        return False


def ensure_mongo_connection():
    """Reconnect if needed; returns False when MongoDB is unavailable."""
    global _mongo_connected

    if _mongo_connected and not _mongo_unavailable:
        try:
            get_connection().server_info()
            return True
        except PyMongoError:
            _mongo_connected = False

    return connect_mongodb()
