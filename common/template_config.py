from fastapi.templating import Jinja2Templates
from common.auth_middleware import get_user_if_token


class CustomJinja2Templates(Jinja2Templates):
    def __init__(self, directory: str):
        super().__init__(directory=directory)
        # self.env.globals['get_user'] = get_user_if_token