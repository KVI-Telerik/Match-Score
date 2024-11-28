import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers.api.user import users_router as api_users_router
from routers.api.player_profile import players_profiles_router as api_players_profiles_router
from routers.api.match import matches_router as api_matches_router
from routers.api.tournament import tournaments_router as api_tournaments_router
from routers.web.match import web_match_router
from routers.web.player_profile import web_player_router
from routers.web.tournament import web_tournament_router
from routers.web.user import web_users_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_users_router)
app.include_router(api_players_profiles_router)
app.include_router(api_matches_router)
app.include_router(api_tournaments_router)


app.include_router(web_users_router)
app.include_router(web_tournament_router)
app.include_router(web_match_router)
app.include_router(web_player_router)
if __name__ == "__main__":
    uvicorn.run('main:app')