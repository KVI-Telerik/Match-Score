import uvicorn
from fastapi import FastAPI
from routers.api.user import users_router as api_users_router

app = FastAPI()
app.include_router(api_users_router)



if __name__ == "__main__":
    uvicorn.run('main:app')