from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services import tournament_service, match_service

templates = Jinja2Templates(directory="templates")
web_home_router = APIRouter()


@web_home_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    tournaments = await tournament_service.get_all()
    matches = await match_service.get_all()

    latest_tournaments = tournaments[:2] if tournaments else []
    latest_matches = matches[:2] if matches else []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "latest_tournaments": latest_tournaments,
            "latest_matches": latest_matches
        }
    )