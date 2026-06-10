from rest_framework import status
from rest_framework.response import Response
from mongoengine.errors import NotUniqueError


def duplicate_conflict(message, field=None):
    """Return a consistent 409 response for duplicate admin resources."""
    errors = {}
    if field:
        errors[field] = [message]
    return Response(
        {
            "success": False,
            "error": message,
            "message": message,
            "errors": errors,
        },
        status=status.HTTP_409_CONFLICT,
    )


def not_unique_conflict(exc, field="name"):
    """Map MongoEngine NotUniqueError to a friendly 409 response."""
    message = str(exc) or "This record already exists."
    if "duplicate key" in message.lower() or "notunique" in message.lower():
        if "slug" in message.lower():
            field = "slug"
        elif "code" in message.lower():
            field = "code"
        elif "title" in message.lower():
            field = "title"
        return duplicate_conflict("This record already exists.", field)
    return duplicate_conflict("This record already exists.", field)
