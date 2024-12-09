from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, logger, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
import logging

from jose import JWTError

from common.rate_limiter import create_rate_limit
from common.template_config import CustomJinja2Templates
from data.models import User, UserLogin
from services import user_service
from common.security import InputSanitizer, csrf, verify_csrf_token
from services.user_service import validate_token_with_session, get_user_by_id, all_requests, claim_director_request, \
    claim_request, approve_player_claim, approve_director_claim

templates = CustomJinja2Templates(directory="templates")
web_users_router = APIRouter(prefix="/users")

@web_users_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Always include CSRF token in forms to prevent cross-site request forgery
    return templates.TemplateResponse(
        "users/login.html",
        {
            "request": request,
            "csrf_token": csrf.generate_token()
        }
    )

@web_users_router.post("/login")
async def login(
    request: Request,
    sanitized_data: dict = Depends(InputSanitizer.sanitize_form_data)
):
    # Use sanitized email but raw password (passwords shouldn't be sanitized)
    login_data = UserLogin(
        email=sanitized_data.get("email"),
        password=sanitized_data.get("password")
    )

    token = await user_service.login_user(login_data.email, login_data.password)
    if not token:
        return templates.TemplateResponse(
            "users/login.html",
            {
                "request": request,
                "error": "Invalid credentials",
                "csrf_token": csrf.generate_token()  # Always provide new token on error
            }
        )
    
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token["access_token"],
        httponly=True,  # Prevent JavaScript access to token
        secure=True,    # Only send over HTTPS
        samesite="lax"  # Protect against CSRF
    )
    return response

@web_users_router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "users/register.html",
        {
            "request": request,
            "csrf_token": csrf.generate_token()
        }
    )

@web_users_router.post("/register")
async def register(
    request: Request,
    sanitized_data: dict = Depends(InputSanitizer.sanitize_form_data)
):
    # Create user with sanitized data except for password
    user_data = User(
        first_name=sanitized_data.get("first_name"),
        last_name=sanitized_data.get("last_name"),
        username=sanitized_data.get("username"),
        email=sanitized_data.get("email"),
        password=sanitized_data.get("password")  # Raw password - will be hashed by service
    )

    user = await user_service.create_user(user_data)
    if not user:
        return templates.TemplateResponse(
            "users/register.html",
            {
                "request": request,
                "error": "Registration failed",
                "csrf_token": csrf.generate_token()
            }
        )
    return RedirectResponse(url="/users/login", status_code=302)



@web_users_router.post("/logout")
async def logout(request: Request):
    token = request.cookies.get("access_token")
    
    if token:
        try:
            # Get user ID before invalidating session
            payload = await user_service.validate_token_with_session(token)
            if payload:
                user_id = payload.get("id")
                # Clear session first
                user_service.SessionManager.clear_session(user_id)
                # Then invalidate user token
                await user_service.logout_user(token)
        except Exception as e:
            print(f"Error during logout: {str(e)}")

    # Create response that redirects to home
    response = RedirectResponse(url="/", status_code=303)  # Using 303 See Other for POST redirect
    
    # Ensure cookie is completely removed
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
    )
    
    return response

@web_users_router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_admin = await user_service.is_admin(token)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    requests = await user_service.all_requests()
    return templates.TemplateResponse(
        "users/admin_dashboard.html",
        {
            "request": request,
            "requests": requests,
            "csrf_token": csrf.generate_token()  # For approval forms
        }
    )




@web_users_router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):

    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    try:

        payload = await validate_token_with_session(token)
        if not payload:
            return RedirectResponse(url="/users/login", status_code=302)

        user_id = payload.get("id")
        user = await get_user_by_id(user_id)
        if not user:
            return RedirectResponse(url="/users/login", status_code=302)


        context = {
            "request": request,
            "user": user,
            "csrf_token": csrf.generate_token()
        }


        if user.is_admin:
            pending_requests = await all_requests()
            context["requests"] = pending_requests


        return templates.TemplateResponse(
            "users/profile.html",
            context
        )

    except JWTError:
        response = RedirectResponse(url="/users/login", status_code=302)
        response.delete_cookie("access_token")
        return response
    except Exception as e:
        print(f"Error in profile page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@web_users_router.post("/claim-player-profile", dependencies=[Depends(create_rate_limit(5))])
async def claim_player_profile(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/profile", status_code=302)

    try:
        success = await claim_request(token)
        if not success:
            return templates.TemplateResponse(
                "users/profile.html",
                {
                    "request": request,
                    "error": "Failed to claim player profile",
                    "csrf_token": csrf.generate_token()
                }
            )
        return RedirectResponse(url="/users/profile", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(
            "users/profile.html",
            {
                "request": request,
                "error": str(e),
                "csrf_token": csrf.generate_token()
            }
        )

@web_users_router.post("/claim-director", dependencies=[Depends(create_rate_limit(5))])
async def claim_director(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/profile", status_code=302)

    try:
        success = await claim_director_request(token)
        if not success:
            return templates.TemplateResponse(
                "users/profile.html",
                {
                    "request": request,
                    "error": "Failed to request director status",
                    "csrf_token": csrf.generate_token()
                }
            )
        return RedirectResponse(url="/users/profile", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(
            "users/profile.html",
            {
                "request": request,
                "error": str(e),
                "csrf_token": csrf.generate_token()
            }
        )

@web_users_router.post("/approve-request/{request_id}")
async def approve_request(
    request: Request,
    request_id: int,
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    try:
        claim_type = await user_service.claim_type(request_id)
        if claim_type == "player claim":
            success = await approve_player_claim(request_id)
        else:
            success = await approve_director_claim(request_id)

        if not success:
            return templates.TemplateResponse(
                "users/profile.html",
                {
                    "request": request,
                    "error": "Failed to approve request",
                    "csrf_token": csrf.generate_token()
                }
            )

        return RedirectResponse(url="/users/profile", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(
            "users/profile.html",
            {
                "request": request,
                "error": str(e),
                "csrf_token": csrf.generate_token()
            }
        )