import jwt
from django.conf import settings
from django.http import JsonResponse
from functools import wraps
from users.models import User

def authenticate(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # Detect CBV (self, request, ...)
        if hasattr(args[0], 'request'):  # self has request attr
            request = args[1]
        elif hasattr(args[0], 'META'):   # FBV, args[0] is request
            request = args[0]
        else:
            raise Exception("Cannot find request object in arguments")

        auth_header = request.META.get('HTTP_AUTHORIZATION')
        # print(request.META.get('HTTP_AUTHORIZATION'))

        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'message': 'Authorization denied'}, status=401)

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            print("payload",payload)
            request.user = {
                'id': payload.get('id'),
                'role': payload.get('role')
            }
        except jwt.ExpiredSignatureError:
            return JsonResponse({'message': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'message': 'Invalid token'}, status=401)

        return view_func(*args, **kwargs)

    return wrapper


def restrict(roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)

            if not user:
                return JsonResponse({'message': "User not authenticated"}, status=401)

            role = user.get('role')

            if role not in roles:
                return JsonResponse({'message': "You're not authorized"}, status=403)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
