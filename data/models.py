#type: ignore
from pydantic import Field, BaseModel, constr, field_validator
from datetime import datetime
from typing import Optional, List, Literal



class User(BaseModel):
    id: Optional[int] = None
    first_name: constr(min_length=2, max_length=30) = Field(..., description="First name of the user")   
    last_name: constr(min_length=2, max_length=30) = Field(..., description="Last name of the user")   
    username: constr(min_length=4, max_length=20) = Field(..., description="Username with minimum 4 and maximum 20 characters") 
    password: constr(min_length=8) = Field(..., description="Password must have at least 8 characters")
    email: constr(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$') = Field(..., description="Email address of the user")
    admin: Optional[bool] = Field(False, description="Whether the user has admin privileges") 

    @classmethod
    def from_query_result(cls,id,first_name,last_name,username, admin,password, email):
        return cls(
            id=id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            email=email,
            admin=admin,
        )
    
class PlayerProfile(BaseModel):
    id: Optional[int] = None
    full_name: constr(min_length=2, max_length=50) = Field(..., description="Full name of the player with minimum 2 and maximum 50 characters")
    country: constr(min_length=4, max_length=56) = Field(..., description="Country of the player")
    sports_club: Optional[str] = None
    wins: Optional[int]
    losses: Optional[int]
    user_id: Optional[int]
    draws: Optional[int]

    

    @classmethod
    def from_query_result(cls, id, full_name, country, sports_club, wins, losses, user_id, draws):
        return cls(
            id=id,
            full_name=full_name,
            country=country,
            sports_club=sports_club,
            wins=wins,
            losses=losses,
            user_id=user_id,
            draws=draws
        )
    

class Match(BaseModel):
    id: Optional[int] = None
    format: constr(min_length=3, max_length=40) = Field(..., description='Format of the match')
    date: date = Field(..., description="Date of the match in YYYY-MM-DD format")
    participants: List[int] =  Field(..., description="List of participant IDs")
    tournament_id: Optional[int]
    tournament_type: Optional[Literal['league', 'knockout']] = None  
    
    @field_validator('date')
    def date_not_in_past(cls, v):
        if v < datetime.now().date():
            raise ValueError("Date of the match cannot be in the past.")
        return v
    
    @field_validator('participants')
    def check_min_participants(cls, v):
        if len(v) < 2:
            raise ValueError('There must be at least 2 participants')
        return v
    
    @classmethod
    def from_query_result(cls, id, format, date, participants, tournament_id):
        return cls(
            id=id,
            format=format,
            date=date,
            participants=participants,
            tournament_id=tournament_id
        )
    

