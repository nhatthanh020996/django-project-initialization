import logging
import json

from django.http import HttpRequest, HttpResponse
from rest_framework import status


logger = logging.getLogger(__name__)


class InterceptMiddleware():
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        return response

    def process_exception(self, request: HttpRequest, exception):
        log_info = {
            'header': request.headers,
            'path': request.get_full_path()
        }
        logger.exception("Unexcepted Error Occurs!!!", extra=log_info)
        
        response = HttpResponse(
            json.dumps({
                "error": 'A server error occurred.',
                'trace_id': request.headers.get('x-request-id')
            }),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content_type='application/json'
        )
        return response