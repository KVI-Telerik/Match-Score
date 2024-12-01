from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from common.template_config import CustomJinja2Templates
from services import tournament_service, match_service
from datetime import datetime
from common.security import csrf

templates = CustomJinja2Templates(directory="templates")

web_home_router = APIRouter()

@web_home_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    tournaments = await tournament_service.get_all()
    matches = await match_service.get_all()

    latest_tournaments = tournaments[:3] if tournaments else []
    
    upcoming_matches = [
        {
            "id": match["id"],
            "tournament_type": match["tournament_type"],
            "participants": " vs ".join([participant.split("-")[0] for participant in match["participants"]]),
            "date": match["date"]
        }
        for match in matches if match["date"] > datetime.now()
    ][:4]  

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "latest_tournaments": latest_tournaments,
            "upcoming_matches": upcoming_matches
        }
    )
