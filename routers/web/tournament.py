from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from common.auth_middleware import validate_token
from common.security import InputSanitizer, csrf
from common.template_config import CustomJinja2Templates
from services import tournament_service, user_service
from data.models import Tournament
from fastapi.templating import Jinja2Templates

templates = CustomJinja2Templates(directory="templates")
web_tournament_router = APIRouter(prefix="/tournaments")


@web_tournament_router.get("/", response_class=HTMLResponse)
async def tournament_list(request: Request, search: str = None):
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = validate_token(token)
        user = await user_service.get_user_by_id(payload["id"])

    tournaments = await tournament_service.get_all(search)
    return templates.TemplateResponse(
        "tournaments/list.html",
        {"request": request, "tournaments": tournaments,"user":user, "csrf_token": csrf.generate_token()}
    )





@web_tournament_router.get("/new", response_class=HTMLResponse)
async def new_tournament_form(request: Request):
    token = request.cookies.get("access_token")
    payload = validate_token(token)
    user = await user_service.get_user_by_id(payload["id"])
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_authorized = await user_service.is_admin(token) or await user_service.is_director(token)
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Admin or director access required")

    return templates.TemplateResponse(
        "tournaments/new.html",
        {"request": request,
         "user":user,
        "csrf_token": csrf.generate_token()
        }

    )


@web_tournament_router.post("/new")
async def create_tournament(
    request: Request,
    sanitized_data: dict = Depends(InputSanitizer.sanitize_form_data)
):
    token = request.cookies.get("access_token")
    payload = validate_token(token)
    user = await user_service.get_user_by_id(payload["id"])
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_authorized = await user_service.is_admin(token) or await user_service.is_director(token)
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Admin or director access required")

    # Use sanitized data
    participant_list = [p.strip() for p in sanitized_data.get("participants").split(',')]
    tournament_data = Tournament(
        title=sanitized_data.get("title"),
        format=sanitized_data.get("format"),
        match_format=sanitized_data.get("match_format"),
        prize=int(sanitized_data.get("prize", 0))
    )

    result = await tournament_service.create(tournament_data, participant_list)
    if not result:
        return templates.TemplateResponse(
            "tournaments/new.html",
            {"request": request, "error": "Failed to create tournament", "csrf_token": csrf.generate_token()}
        )
    return RedirectResponse(url="/tournaments", status_code=302)

@web_tournament_router.get("/{tournament_id}", response_class=HTMLResponse)
async def tournament_detail(request: Request, tournament_id: int):
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = validate_token(token)
        user = await user_service.get_user_by_id(payload["id"])

    tournament = await tournament_service.get_by_id(tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament["format"] == "League":
        standings = await tournament_service.get_league_standings(tournament_id)
    else:
        standings = None

    return templates.TemplateResponse(
        "tournaments/detail.html",
        {
            "request": request,
            "user":user,
            "tournament": tournament,
            "standings": standings,
            "csrf_token": csrf.generate_token()
        }
    )


@web_tournament_router.post("/{id}/next_round")
async def next_round_knockout(
        request: Request,
        tournament_id: int
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_authorized = await user_service.is_admin(token) or await user_service.is_director(token)
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Admin or director access required")

    success = await tournament_service.advance_knockout_tournament(tournament_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to advance tournament")

    return RedirectResponse(url=f"/tournaments/{tournament_id}", status_code=302)