from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import JWTError

from common.auth_middleware import validate_token
from common.template_config import CustomJinja2Templates
from services import player_profile_service, user_service
from data.models import PlayerProfile, UpdateProfile

from common.security import InputSanitizer, csrf

templates = CustomJinja2Templates(directory="templates")
web_player_router = APIRouter(prefix="/players")


@web_player_router.get("/", response_class=HTMLResponse)
async def player_list(
        request: Request,
        search: str = None,
        page: int = Query(1, ge=1),
        per_page: int = Query(9, ge=1, le=100)
):
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = await user_service.validate_token_with_session(token)
        if payload:
            user = await user_service.get_user_by_id(payload["id"])

    result = await player_profile_service.get_all(search, page, per_page)

    return templates.TemplateResponse(
        "players/list.html",
        {
            "request": request,
            "user":user,
            "players": result["players"],
            "page": result["page"],
            "total_pages": result["total_pages"],
            "total": result["total"],
            "search": search,
            "per_page": per_page,
            "csrf_token": csrf.generate_token()
        }
    )




@web_player_router.get("/new", response_class=HTMLResponse)
async def new_player_form(request: Request):
    token = request.cookies.get("access_token")
    user = None
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    try:
        payload = await user_service.validate_token_with_session(token)  
        if not payload:
            return RedirectResponse(url="/users/login", status_code=302)
            
        user = await user_service.get_user_by_id(payload["id"])
        is_admin = await user_service.is_admin(token)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        return templates.TemplateResponse(
            "players/new.html",
            {"request": request,
             "user": user,
             "csrf_token": csrf.generate_token()}
        )
    except JWTError:
        return RedirectResponse(url="/users/login", status_code=302)


@web_player_router.post("/new")
async def create_player(
    request: Request,
    sanitized_data: dict = Depends(InputSanitizer.sanitize_form_data)
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_admin = await user_service.is_admin(token)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    player_data = PlayerProfile(
        full_name=sanitized_data.get("full_name"),
        country=sanitized_data.get("country"),
        sports_club=sanitized_data.get("sports_club"),
        wins=sanitized_data.get("wins"),
        losses=sanitized_data.get("losses"),
        draws=sanitized_data.get("draws"),
    )

    player = await player_profile_service.create(player_data)
    if not player:
        return templates.TemplateResponse(
            "players/new.html",
            {"request": request, "error": "Failed to create player", "csrf_token": csrf.generate_token()}
        )
    return RedirectResponse(url="/players", status_code=302)

@web_player_router.get("/{player_id}", response_class=HTMLResponse)
async def player_detail(request: Request, player_id: int):
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = await user_service.validate_token_with_session(token)
        if payload:
            user = await user_service.get_user_by_id(payload["id"])
            
    player = await player_profile_service.get_profile_by_id(player_id)
    profile_linked_user_id = await player_profile_service.get_user_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    statistics = await player_profile_service.get_statistics(player_id)
    
    return templates.TemplateResponse(
        "players/detail.html",
        {"request": request,
         "player": player,
         "user": user,
         "profile_linked_user_id": profile_linked_user_id,
         "statistics": statistics,
         "csrf_token": csrf.generate_token()}
    )


@web_player_router.get("/{player_id}/edit", response_class=HTMLResponse)
async def edit_player_form(request: Request, player_id: int):
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = await user_service.validate_token_with_session(token)
        if payload:
            user = await user_service.get_user_by_id(payload["id"])

    player = await player_profile_service.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return templates.TemplateResponse(
        "players/edit.html",
        {"request": request, "player": player,"user":user, "csrf_token": csrf.generate_token()}
    )


@web_player_router.post("/{player_id}/edit")
async def update_player(
        request: Request,
        player_id: int,
        country: str = Form(None),
        sports_club: str = Form(None)
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    update_data = UpdateProfile(
        country=country,
        sports_club=sports_club
    )

    updated_player = await player_profile_service.update(player_id, update_data)
    if not updated_player:
        return templates.TemplateResponse(
            "players/edit.html",
            {"request": request, "error": "Failed to update player", "csrf_token": csrf.generate_token()}
        )
    return RedirectResponse(url=f"/players/{player_id}", status_code=302)


@web_player_router.post("/claim")
async def claim_player_profile(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    awaiting_approval = await user_service.claim_request(token)
    if not awaiting_approval:
        raise HTTPException(
            status_code=400,
            detail="Player profile with such name can't be claimed or does not exist"
        )
    return RedirectResponse(url="/players", status_code=302)

@web_player_router.post("/{player_id}/delete", response_class=HTMLResponse)
async def delete_player(
    request: Request,
    player_id: int,
    csrf_token: str = Form(...),
):
    # Verify CSRF token
    if not csrf.validate_token(csrf_token):
        raise HTTPException(status_code=400, detail="Invalid CSRF token")
        
   
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    payload = await user_service.validate_token_with_session(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user = await user_service.get_user_by_id(payload["id"])
    
    
    profile_linked_user_id = await player_profile_service.get_user_id(player_id)
    if not user.is_admin and user.id != profile_linked_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this profile")
    
    
    await player_profile_service.delete_player_profile(player_id)
    
    
    return RedirectResponse(url="/players", status_code=303)