# Placeholder for auth middleware
class JWTVerifier:
    def verify(self, request):
        return {"user": "test-user", "scopes": ["all"]}

class JWTGenerator:
    def generate_service_token(self, service):
        return "some.jwt.token"

class APIKeyManager:
    def create_key(self, service):
        return "some_api_key"
