from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List


class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, Dict[str, List[datetime]]] = {}

        asyncio.create_task(self.clean_up())

    async def clean_up(self):
        """Periodically clean up old request records"""
        while True:
            current_time = datetime.now()
            for ip in list(self.requests.keys()):
                for endpoint in list(self.requests[ip].keys()):
                    self.requests[ip][endpoint] = [
                        request_time
                        for request_time in self.requests[ip][endpoint]
                        if request_time + timedelta(minutes=1) > current_time
                    ]

                    if not self.requests[ip][endpoint]:
                       del self.requests[ip][endpoint]
                    
                if not self.requests[ip]:
                    del self.requests[ip]
            await asyncio.sleep(60)

    async def check_rate_limit(
        self,
        request: Request,
        max_requests: int = 60):
            """Check if request should be rate limited"""

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
                if ts + timedelta(minutes=1) > current_time
            ])

            if recent_requests > max_requests:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests, slow down!"
                )


rate_limiter = RateLimiter()
async def rate_limit(request: Request, max_requests: int = 60):
    await rate_limiter.check_rate_limit(request, max_requests)


       