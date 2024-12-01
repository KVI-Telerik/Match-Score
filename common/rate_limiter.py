from fastapi import FastAPI, Request, HTTPException, Depends
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, Dict[str, List[datetime]]] = {}
        
        asyncio.create_task(self._cleanup_old_requests())

    async def _check_request(self, request: Request, max_requests: int) -> None:
        client_ip = request.client.host
        endpoint = request.url.path
        current_time = datetime.now()

        if client_ip not in self.requests:
            self.requests[client_ip] = {}
        if endpoint not in self.requests[client_ip]:
            self.requests[client_ip][endpoint] = []

        self.requests[client_ip][endpoint].append(current_time)
       
        recent_requests = len([
            ts for ts in self.requests[client_ip][endpoint]
            if (current_time - ts) < timedelta(minutes=1)
        ])

        print(f"IP: {client_ip}, Endpoint: {endpoint}, Recent requests: {recent_requests}")

        if recent_requests > max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per minute."
            )

    async def _cleanup_old_requests(self):
        while True:
            try:
                current_time = datetime.now()
                for ip in list(self.requests.keys()):
                    for endpoint in list(self.requests[ip].keys()):
                        self.requests[ip][endpoint] = [
                            ts for ts in self.requests[ip][endpoint]
                            if (current_time - ts) < timedelta(minutes=1)
                        ]
                        
                        if not self.requests[ip][endpoint]:
                            del self.requests[ip][endpoint]
                    
                    if not self.requests[ip]:
                        del self.requests[ip]
            except Exception as e:
                print(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)


rate_limiter = RateLimiter()

def create_rate_limit(max_requests: int = 10):
    """Creates a rate limit dependency with specified max requests"""
    async def rate_limit_dependency(
        request: Request,
        limiter: RateLimiter = Depends(lambda: rate_limiter)
    ):
        await limiter._check_request(request, max_requests)
    return rate_limit_dependency

# Export these names
__all__ = ['rate_limiter', 'create_rate_limit']