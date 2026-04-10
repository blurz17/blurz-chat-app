from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from fastapi import UploadFile
from typing import Optional

# this class will be the response of other users when u search or open the profile of this user
class other_users(BaseModel):
    id: uuid.UUID
    username: str
    first_name: str
    last_name: str
    profile_url: Optional[str] = None
    created_at: datetime | None = None


class Update_User(BaseModel): 
    username: str | None = Field(max_length=20, default=None)
    first_name: str | None = None
    last_name: str | None = None



class Update_Profile_Picture(BaseModel):
    profile_picture: UploadFile


class Profile_Picture_Response(BaseModel):
    message: str
