"""Authentication middleware"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuthMiddleware(BaseHTTPMiddleware):
    """Simple authentication middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health checks and public endpoints
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # TODO: Implement proper authentication
        # For now, just pass through
        return await call_next(request)
