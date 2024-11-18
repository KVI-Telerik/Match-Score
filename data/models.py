
# type: ignore
from datetime import datetime, timezone
from pydantic import Field, BaseModel, constr, field_validator
from datetime import datetime, date
from typing import Optional, List, Literal



class User(BaseModel):
    id: Optional[int] = None
    first_name: constr(min_length=2, max_length=30) = Field(..., description="First name of the user")   
    last_name: constr(min_length=2, max_length=30) = Field(..., description="Last name of the user")   
    username: constr(min_length=4, max_length=20) = Field(..., description="Username with minimum 4 and maximum 20 characters") 
    password: constr(min_length=8) = Field(..., description="Password must have at least 8 characters")
    email: constr(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$') = Field(..., description="Email address of the user")
    is_admin: Optional[bool] = Field(False, description="Whether the user has admin privileges") 
    is_director: Optional[bool] = Field(False, description="Whether the user has director privileges")
    player_profile_id: Optional[int] = None

    @classmethod
    def from_query_result(cls,id,first_name,last_name,username,password, email,is_admin, is_director, player_profile_id):
        return cls(
            id=id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            email=email,
            is_admin=is_admin,
            is_director=is_director,
            player_profile_id=player_profile_id
        )
    
class PlayerProfile(BaseModel):
    id: Optional[int] = None
    full_name: constr(min_length=2, max_length=50) = Field(..., description="Full name of the player with minimum 2 and maximum 50 characters")
    country: Optional[str]   # constr(min_length=4, max_length=56)) = Field(..., description="Country of the player")
    sports_club: Optional[str] = None
    wins: Optional[int]
    losses: Optional[int]
    draws: Optional[int]
    
    @classmethod
    def from_query_result(cls, id, full_name, country, sports_club, wins, losses, draws, ):
        return cls(
            id=id,
            full_name=full_name,
            country=country,
            sports_club=sports_club,
            wins=wins,
            losses=losses,
            draws=draws,
        )


class Match(BaseModel):
    id: Optional[int] = None
    format: constr(min_length=3, max_length=40) = Field(
        ...,
        description='Format of the match Time limited duration of 60 minutes or Score limited first to 9 points'
    )
    date: datetime = Field(
        ...,
        description="Date of the match in YYYY-MM-DD format"
    )
    participants: List[str] = Field(
        ...,
        description="List of participant full names"
    )
    tournament_id: Optional[int] = Field(
        default=None,
        description="Optional tournament ID for tournament matches"
    )
    tournament_type: Optional[Literal['league', 'knockout']] = Field(
        default=None,
        description="Type of tournament if match is part of a tournament"
    )

    @field_validator('date')
    def date_not_in_past(cls, v: datetime) -> datetime:
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)

        current_time = datetime.now()
        if v < current_time:
            raise ValueError("Date of the match cannot be in the past.")
        return v

    @field_validator('participants')
    def validate_participants(cls, v: List[str]) -> List[str]:
        if len(v) < 2:
            raise ValueError("Match must have at least 2 participants")
        return v

    @field_validator('format')
    def validate_format(cls, v: str) -> str:
        valid_formats = ['Time limited', 'Score limited']
        if not any(format_type in v for format_type in valid_formats):
            raise ValueError("Format must be either 'Time limited' or 'Score limited'")
        return v
    @classmethod
    def from_query_result(cls, id, format, date, participants, tournament_id, tournament_type):
        participants_list = participants if isinstance(participants, list) else []
        return cls(
            id=id,
            format=format,
            date=date,
            participants=participants_list,
            tournament_id=tournament_id,
            tournament_type=tournament_type
        )
    

class Tournament(BaseModel):
    id: Optional[int] = None
    title: constr(min_length=3, max_length=50) = Field(..., description="Title of the tournament")
    format: Optional[Literal['league', 'knockout']] = None  
    match_format: Optional[Literal['score', 'time']] = None
    prize: Optional[int]

    @classmethod
    def from_query_result(cls, id, title, format, match_format, prize):
        return cls(
            id=id,
            title=title,
            format=format,
            match_format=match_format,
            prize=prize
        )
    

class TournamentParticipants(BaseModel):
    tournament_id: Optional[int]
    player_profile_id: Optional[int]
    wins: Optional[int]
    losses: Optional[int]
    draws: Optional[int]

    @classmethod
    def from_query_result(cls, tournament_id, player_profile_id, wins, losses, draws):
        return cls(
            tournament_id=tournament_id,
            player_profile_id=player_profile_id,
            wins=wins,
            losses=losses,
            draws=draws

        )


class UserLogin(BaseModel):
    email: str
    password: str

class MatchParticipants(BaseModel):
    match_id: Optional[int]
    player_profile_id: Optional[int]
    score: Optional[int]

    @classmethod
    def from_query_result(cls, match_id, player_profile_id, score):
        return cls(
            match_id=match_id,
            player_profile_id=player_profile_id,
            score=score
        )
    

class Requests(BaseModel):
    id: Optional[int] = None
    user_id: int = Field(..., description="Id of the user making the request")
    player_profile_id: Optional[int] = None
    approved_or_denied: Optional[bool] = None
