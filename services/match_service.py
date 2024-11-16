from typing import Optional
from data.models import Match
from data.database import DatabaseConnection


async def create(match_data: Match) -> Optional[Match]:
    pass