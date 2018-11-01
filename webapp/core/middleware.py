from django.utils.deprecation import MiddlewareMixin
from core.models import UserLog
from django.conf import settings


def get_client_ip(request):
    """
    X-Forwarded-For stores the client's ip when going
    through a proxy or load balancer
    Remote-Address is not as reliable as X-Forwarded-For, but if the
    server is not configured to include X-Forwarded-For header,
    thats the only option
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class UserLogMiddleware(MiddlewareMixin):
    """
    Middleware generates user activity logs
    """

    def process_response(self, request, response):
        # Check if method should be stored
        if request.method not in settings.USERLOG_METHODS:
            return response

        # Check if user is AnonymousUser, in that case is stores as null
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None

        UserLog.objects.create(
            user=user,
            request_path=request.path,
            request_method=request.method,
            response_code=response.status_code,
            ip_address=get_client_ip(request),
        )
        return response
