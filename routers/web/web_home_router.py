from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from common.auth_middleware import validate_token
from common.template_config import CustomJinja2Templates
from services import tournament_service, match_service, user_service
from datetime import datetime
from common.security import csrf

templates = CustomJinja2Templates(directory="templates")

web_home_router = APIRouter()

@web_home_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = await user_service.validate_token_with_session(token)
        if payload:
            user = await user_service.get_user_by_id(payload["id"])


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
            "user":user,
            "latest_tournaments": latest_tournaments,
            "upcoming_matches": upcoming_matches,
            "csrf_token": csrf.generate_token()  
        }
    )
