import logging
import time
import uuid



logger = logging.getLogger("apartments.request")

class RequestLoggingMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id
        started = time.perf_counter()
        status_code = 500
        response = None

        try:
            response = self.get_response(request)
            status_code = response.status_code
            return response
        except Exception:
            logger.exception(
                "request_id=%s method=%s path=%s status=%s",
                request_id, request.method, request.path, status_code
            )
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)

            if status_code >= 500:
                logger.error(
                    "request_id=%s method=%s path=%s status=%s duration_ms=%s user=%s",
                    request_id, request.method, request.path, status_code, duration_ms,
                    getattr(getattr(request, "user", None), "id", None),
                )
            elif status_code >= 400:
                logger.warning(
                    "request_id=%s method=%s path=%s status=%s duration_ms=%s user=%s",
                    request_id, request.method, request.path, status_code, duration_ms,
                    getattr(getattr(request, "user", None), "id", None),
                )
            elif status_code >= 200:
                logger.debug("request_id=%s method=%s path=%s status=%s duration_ms=%s user=%s",
                             request_id, request.method, request.path, status_code, duration_ms,
                             getattr(getattr(request, "user", None), "id", None))
            elif duration_ms > 800:
                logger.info(
                    "slow_request request_id=%s method=%s path=%s status=%s duration_ms=%s user=%s",
                    request_id, request.method, request.path, status_code, duration_ms,
                    getattr(getattr(request, "user", None), "id", None),
                )

            if response is not None:
                response["X-Request-ID"] = request_id




