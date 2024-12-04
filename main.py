import uvicorn
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from common.rate_limiter import RateLimiter, rate_limiter,create_rate_limit
from common.security import csrf, verify_csrf_token
from routers.api.user import users_router as api_users_router
from routers.api.player_profile import players_profiles_router as api_players_profiles_router
from routers.api.match import matches_router as api_matches_router
from routers.api.tournament import tournaments_router as api_tournaments_router
from routers.web.match import web_match_router
from routers.web.player_profile import web_player_router
from routers.web.tournament import web_tournament_router
from routers.web.user import web_users_router
from routers.web.web_home_router import web_home_router
from services.user_service import validate_token_with_session, SessionManager
from jose import JWTError



@asynccontextmanager
async def lifespan(app: FastAPI):
    global rate_limiter
    rate_limiter = RateLimiter()
    yield
    
    SessionManager._sessions.clear()

app = FastAPI(lifespan=lifespan,docs_url="/docs")



app.mount("/static", StaticFiles(directory="static/"), name="static")

app.include_router(api_users_router)
app.include_router(api_players_profiles_router)
app.include_router(api_matches_router)
app.include_router(api_tournaments_router)

app.include_router(web_users_router)
app.include_router(web_tournament_router)
app.include_router(web_match_router)
app.include_router(web_player_router)
app.include_router(web_home_router)

@app.get("/test/rate-limit", dependencies=[Depends(create_rate_limit(5))])
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
async def session_middleware(request: Request, call_next):
    """Middleware to track user activity and validate sessions"""
    
    is_api_route = request.url.path.startswith("/api/")
    
    # Public paths that don't require authentication
    public_paths = {
        "/api/users/login",
        "/api/users/register",
        "/users/login",
        "/users/register",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
        "/tournaments",
        "/matches",
        "/players"
    }
    
    if request.url.path in public_paths:
        return await call_next(request)
        
    if is_api_route:
        # Handle API authentication
        auth_header = request.headers.get("token")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")
            
        token = auth_header
        try:
            payload = await validate_token_with_session(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Session expired")
            
            request.state.user = payload
            return await call_next(request)
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        # Handle web authentication via cookies
        token = request.cookies.get("access_token")
        if token:
            try:
                payload = await validate_token_with_session(token)
                if payload:
                    request.state.user = payload
                    return await call_next(request)
            except JWTError:
                pass
                
        if request.url.path not in public_paths:
            return RedirectResponse(url="/users/login", status_code=302)
    
    return await call_next(request)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Global security middleware"""
    # Don't apply security headers to OpenAPI endpoints
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
        
    response = await call_next(request)
   
    return response

@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    """CSRF protection middleware"""
    # Don't check CSRF for OpenAPI endpoints
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
        
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        if "web" in str(request.url.path):
            if not await verify_csrf_token(request):
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token missing or invalid"
                )
    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run('main:app')