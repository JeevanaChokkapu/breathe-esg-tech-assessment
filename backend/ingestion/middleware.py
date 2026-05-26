class AuditActorMiddleware:
    """
    Stores a human-readable actor on the request.
    In this prototype auth is intentionally thin; production would map this to a real user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.audit_actor = request.headers.get("X-Analyst-Email", "")
        return self.get_response(request)

