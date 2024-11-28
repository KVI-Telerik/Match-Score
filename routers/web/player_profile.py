from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from services import player_profile_service, user_service
from data.models import PlayerProfile, UpdateProfile
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
web_player_router = APIRouter(prefix="/players")


@web_player_router.get("/", response_class=HTMLResponse)
async def player_list(request: Request, search: str = None):
    players = await player_profile_service.get_all(search)
    return templates.TemplateResponse(
        "players/list.html",
        {"request": request, "players": players}
    )


@web_player_router.get("/{player_id}", response_class=HTMLResponse)
async def player_detail(request: Request, player_id: int):
    player = await player_profile_service.get_profile_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return templates.TemplateResponse(
        "players/detail.html",
        {"request": request, "player": player}
    )


@web_player_router.get("/new", response_class=HTMLResponse)
async def new_player_form(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_admin = await user_service.is_admin(token)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return templates.TemplateResponse(
        "players/new.html",
        {"request": request}
    )


@web_player_router.post("/new")
async def create_player(
        request: Request,
        full_name: str = Form(...),
        country: str = Form(None),
        sports_club: str = Form(None)
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_admin = await user_service.is_admin(token)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    player_data = PlayerProfile(
        full_name=full_name,
        country=country,
        sports_club=sports_club,
        wins=0,
        losses=0,
        draws=0
    )

    player = await player_profile_service.create(player_data)
    if not player:
        return templates.TemplateResponse(
            "players/new.html",
            {"request": request, "error": "Failed to create player"}
        )
    return RedirectResponse(url="/players", status_code=302)


@web_player_router.get("/{player_id}/edit", response_class=HTMLResponse)
async def edit_player_form(request: Request, player_id: int):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    player = await player_profile_service.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return templates.TemplateResponse(
        "players/edit.html",
        {"request": request, "player": player}
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
            {"request": request, "error": "Failed to update player"}
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