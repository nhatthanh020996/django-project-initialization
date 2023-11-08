import logging
import json

from django.http import HttpRequest


logger = logging.getLogger(__name__)


class LoggingMiddleware():
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        log_info = {
            'header': request.headers,
            'body': json.loads(request.body.decode('utf-8')) if request.content_type == 'application/json' else {},
            'path': request.get_full_path()
        }
        logger.info('Incomming request', extra=log_info)
        response = self.get_response(request)
        return response