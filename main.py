import uvicorn
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from common.rate_limiter import RateLimiter, rate_limit
from common.security import csrf, SecurityHeaders, verify_csrf_token
from routers.api.user import users_router as api_users_router
from routers.api.player_profile import players_profiles_router as api_players_profiles_router
from routers.api.match import matches_router as api_matches_router
from routers.api.tournament import tournaments_router as api_tournaments_router
from routers.web.match import web_match_router
from routers.web.player_profile import web_player_router
from routers.web.tournament import web_tournament_router
from routers.web.user import web_users_router
from routers.web.web_home_router import web_home_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    global rate_limiter
    rate_limiter = RateLimiter()
    print("Starting up the application...")  
    yield
    
    print("Shutting down the application...")  

app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_users_router)
app.include_router(api_players_profiles_router)
app.include_router(api_matches_router)
app.include_router(api_tournaments_router)

app.include_router(web_users_router)
app.include_router(web_tournament_router)
app.include_router(web_match_router)
app.include_router(web_player_router)
app.include_router(web_home_router)

@app.get("/test/rate-limit", dependencies=[Depends(rate_limit)])
async def test_rate_limit():
    """Test endpoint with rate limiting"""
    return {"message": "Request successful"}

@app.get("/test/rate-limit-status")
async def test_rate_limit_status():
    """Check rate limiter state"""
    return {
        "active_ips": len(rate_limiter.requests),
        "request_counts": {
            ip: {endpoint: len(timestamps) 
                for endpoint, timestamps in endpoints.items()}
            for ip, endpoints in rate_limiter.requests.items()
        }
    }

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Global security middleware"""
    # Add security headers to all responses
    response = await call_next(request)
    headers = SecurityHeaders.get_security_headers()
    response.headers.update(headers)
    return response

@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    """CSRF protection middleware"""
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        if "web" in str(request.url.path):
            if not await verify_csrf_token(request):
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token missing or invalid"
                )
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"]  
)

if __name__ == "__main__":
    uvicorn.run('main:app')