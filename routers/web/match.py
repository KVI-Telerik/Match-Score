from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from common.security import csrf
from common.auth_middleware import validate_token
from common.security import InputSanitizer
from common.template_config import CustomJinja2Templates
from services import match_service, user_service
from data.models import Match
from datetime import datetime


templates = CustomJinja2Templates(directory="templates")
web_match_router = APIRouter(prefix="/matches")


@web_match_router.get("/", response_class=HTMLResponse)
async def match_list(request: Request, tournament: str = None):
    # Existing user authentication logic
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = await user_service.validate_token_with_session(token)
        if payload:
            user = await user_service.get_user_by_id(payload["id"])

    # Updated to include tournament search
    matches = await match_service.get_all(tournament_search=tournament)

    return templates.TemplateResponse(
        "matches/list.html",
        {"request": request,
         "user": user,
         "matches": matches,
         "search": tournament}  # Add search term to template context
    )





@web_match_router.get("/new", response_class=HTMLResponse)
async def new_match_form(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_authorized = await user_service.is_admin(token) or await user_service.is_director(token)
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Admin or director access required")

    return templates.TemplateResponse(
        "matches/new.html",
        {"request": request, "csrf_token": csrf.generate_token()}
    )


@web_match_router.post("/new")
async def create_match(
    request: Request,
    sanitized_data: dict = Depends(InputSanitizer.sanitize_form_data)
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_authorized = await user_service.is_admin(token) or await user_service.is_director(token)
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Admin or director access required")

    participant_list = [p.strip() for p in sanitized_data.get("participants").split(',')]
    match_data = Match(
        format=sanitized_data.get("format"),
        date=datetime.fromisoformat(sanitized_data.get("date")),
        participants=participant_list,
        tournament_id=None,
        tournament_type=None
    )

    match = await match_service.create(match_data)
    if not match:
        return templates.TemplateResponse(
            "matches/new.html",
            {"request": request, "error": "Failed to create match", "csrf_token": csrf.generate_token()}
        )
    return RedirectResponse(url="/matches", status_code=302)

@web_match_router.get("/{match_id}", response_class=HTMLResponse)
async def match_detail(request: Request, match_id: int):
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = await user_service.validate_token_with_session(token)
        if payload:
            user = await user_service.get_user_by_id(payload["id"])
            
    match = await match_service.get_match_with_scores(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return templates.TemplateResponse(
        "matches/detail.html",
        {"request": request,
         "user": user,
         "match": match,
         "csrf_token": csrf.generate_token()}
    )


@web_match_router.post("/{match_id}/score")
async def update_score(
        request: Request,
        match_id: int,
        player_id: int = Form(...),
        score: int = Form(...)
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_authorized = await user_service.is_admin(token) or await user_service.is_director(token)
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Admin or director access required")

    result = await match_service.update_score(match_id, player_id, score)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to update score")
    return RedirectResponse(url=f"/matches/{match_id}", status_code=302)


@web_match_router.post("/leagues/{match_id}/end")
async def end_match(
        request: Request,
        match_id: int
):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login", status_code=302)

    is_authorized = await user_service.is_admin(token) or await user_service.is_director(token)
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Admin or director access required")

    tournament_id = await match_service.get_tournament_by_match_id(match_id)
    success = await match_service.match_end_league(match_id, tournament_id)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to end match")
    return RedirectResponse(url=f"/matches/{match_id}", status_code=302)