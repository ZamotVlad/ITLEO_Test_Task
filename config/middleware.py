class FixDuplicateOriginMiddleware:
    """
    OpenLiteSpeed reverse proxy іноді дублює заголовок Origin,
    що ламає CSRF перевірку Django. Цей middleware бере лише
    перше значення якщо заголовок продубльований через кому.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.META.get("HTTP_ORIGIN")
        if origin and "," in origin:
            request.META["HTTP_ORIGIN"] = origin.split(",")[0].strip()
        return self.get_response(request)
