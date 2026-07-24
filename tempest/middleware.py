import logging
from django.shortcuts import render
from django_ratelimit.exceptions import Ratelimited

logger = logging.getLogger(__name__)

class RealIPMiddleware:
    """
    Resolves client IP addresses correctly when behind reverse proxies
    (specifically Cloudflare and Fly.io) to prevent IP spoofing and fix rate limiting.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Prioritize Cloudflare connecting IP
        cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_ip:
            request.META['REMOTE_ADDR'] = cf_ip.strip()
        else:
            # Fallback to Fly.io Client IP
            fly_ip = request.META.get('HTTP_FLY_CLIENT_IP')
            if fly_ip:
                request.META['REMOTE_ADDR'] = fly_ip.strip()
            else:
                # Standard X-Forwarded-For (grab the leftmost client IP)
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0].strip()
                    request.META['REMOTE_ADDR'] = ip
        return self.get_response(request)


class RatelimitMiddleware:
    """
    Catches django-ratelimit's `Ratelimited` exceptions and renders a premium
    custom 429 Too Many Requests HTML template.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            logger.warning(f"Rate limit triggered for IP: {request.META.get('REMOTE_ADDR')} on {request.path}")
            return render(request, '429.html', status=429)
        return None
