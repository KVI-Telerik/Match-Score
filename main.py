import uvicorn
from fastapi import FastAPI
from routers.api.user import users_router as api_users_router
from routers.api.player_profile import players_profiles_router as api_players_profiles_router
from routers.api.match import matches_router as api_matches_router
from routers.api.tournament import tournaments_router as api_tournaments_router
app = FastAPI()
app.include_router(api_users_router)
app.include_router(api_players_profiles_router)
app.include_router(api_matches_router)
app.include_router(api_tournaments_router)


if __name__ == "__main__":
    uvicorn.run('main:app')