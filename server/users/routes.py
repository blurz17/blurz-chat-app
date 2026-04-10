from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import get_current_user, AccessTokenBearer
from auth.schema import User, UserInfo
from .schema import other_users, Update_User, Profile_Picture_Response, Update_Profile_Picture
from .service import update_user, get_contacts, search_user
from db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from celery_service.celery_tasks import bg_save_profile_picture
from pathlib import Path
import base64

user_router = APIRouter()

# file size checker
MAX_FILE_SIZE = 5 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024  # Read 1MB at a time


@user_router.get('/me', response_model=UserInfo,
                    dependencies=[Depends(AccessTokenBearer())])
async def get_me(user_details: User = Depends(get_current_user)):
    return user_details


# update user
@user_router.patch('/update', response_model=UserInfo,
                    dependencies=[Depends(AccessTokenBearer())])
async def Update_user(update_data: Update_User,
                             user_details: User = Depends(get_current_user),
                             session: AsyncSession = Depends(get_session)):
    updated_user = await update_user(user_details.id, session, update_data)
    return updated_user


# get all contacts 
@user_router.get('/contacts', response_model=list[other_users], dependencies=[Depends(AccessTokenBearer())])
async def Get_contacts(session: AsyncSession = Depends(get_session)):
    return await get_contacts(session)


@user_router.get('/search/{query}', response_model=list[other_users], dependencies=[Depends(AccessTokenBearer())])
async def Search_user(query: str, session: AsyncSession = Depends(get_session)):
    return await search_user(query, session)


# the profile picture is uploaded in background task and return public url
@user_router.patch('/update-profile-picture', response_model=Profile_Picture_Response,
                    dependencies=[Depends(AccessTokenBearer())])
async def Update_profile_picture(update_data: Update_Profile_Picture,
                             user_details: User = Depends(get_current_user)):
    if not update_data.profile_picture:
        raise HTTPException(status_code=400, detail="No profile picture is provided")
    
    total_size = 0
    all_chunks = []
    
    while True:
        chunk = await update_data.profile_picture.read(CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds maximum allowed size")
        all_chunks.append(chunk)
    
    file_bytes = b''.join(all_chunks)
    ext = Path(update_data.profile_picture.filename).suffix.lower()
    
    # Encode bytes to base64 string for JSON serialization via Celery
    file_bytes_b64 = base64.b64encode(file_bytes).decode('utf-8')
    bg_save_profile_picture.delay(file_bytes_b64, ext, str(user_details.id))
    return {"message": "Profile picture is being uploaded"}
