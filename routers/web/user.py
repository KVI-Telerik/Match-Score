from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import  HTMLResponse, RedirectResponse
from data.models import User
from services import user_service
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
web_users_router = APIRouter(prefix="/users")

@web_users_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "users/login.html",
        {"request": request}
    )

@web_users_router.post("/login")
async def login(
        request: Request,
        email: str = Form(...),
        password : str = Form(...)
):
    token = await user_service.login_user(email,password)
    if not token:
        return templates.TemplateResponse(
            "users/login.html",
            {"request": request, "error": "Invalid credentials"}
        )
    response = RedirectResponse(url ="/", status_code=302)
    response.set_cookie(key="access token", value=token["access token"])
    return response

@web_users_router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "users/register.html",
        {"request": request}
    )


@web_users_router.post("/register")
async def register(
        request: Request,
        first_name: str = Form(...),
        last_name: str = Form(...),
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
):

    user_data = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password=password
    )

    user = await user_service.create_user(user_data)
    if not user:
        return templates.TemplateResponse(
            "users/register.html",
            {"request": request, "error": "Registration failed"}
        )
    return RedirectResponse(url="/users/login", status_code=302)

@web_users_router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)
    return templates.TemplateResponse(
        "users/profile.html",
        {"request": request}
    )
@web_users_router.get("/logout")
async def logout():
    response = RedirectResponse(url="/users/login", status_code=302)
    response.delete_cookie(key="access_token")
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
        {"request": request, "requests": requests}
    )


@web_users_router.post("/admin/requests/{request_id}/approve")
async def approve_request(
        request: Request,
        request_id: int,
        request_type: str = Form(...)
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_admin = await user_service.is_admin(token)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    if request_type == "player":
        success = await user_service.approve_player_claim(request_id)
    elif request_type == "director":
        success = await user_service.approve_director_claim(request_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid request type")

    if not success:
        return templates.TemplateResponse(
            "users/admin_dashboard.html",
            {"request": request, "error": "Failed to approve request"}
        )

    return RedirectResponse(url="/users/admin", status_code=302)