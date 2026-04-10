from fastapi import APIRouter, Depends, status, HTTPException
from db.main import get_session
from .service import User_Service
from .schema import Create_User as Create_User_Model, User, Login_User, UserInfo, Password_Reset, Password_reset_Confirm, ChangePassword
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from utils import access_token, verify_password, CreationSafeLink, generate_hashed_password
from datetime import datetime, timedelta
from db.config import config
from fastapi.responses import JSONResponse
from .dependencies import RefreshToken, AccessTokenBearer, get_current_user, CheckRoler
from errors import AccessTokenRequired, UserAlreadyExists, UserNotFound, InvalidCredentials, VerificationError, DataNotFound, PasswordAlreadyReset, UserAlreadyVerify
from db.redis import add_to_blacklist, check_blacklist
from mailserver.service import send_email, mail
from celery_service.celery_tasks import bg_send_mail, bg_save_profile_picture
from db.models import User as User_DB
from pathlib import Path
import base64

auth_router = APIRouter()

user_service = User_Service()

access_token_bearer = AccessTokenBearer()

password_reset_link = CreationSafeLink(config.password_secrete_reset, 'password_reset_link')

email_verification_link = CreationSafeLink(config.jwt_secret, 'email_verification_link')

# file size checker
MAX_FILE_SIZE = 5 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024  # Read 1MB at a time



refresh = timedelta(days=config.refresh_token_expiary)

access = timedelta(minutes=config.access_token_expiary)

@auth_router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: Create_User_Model,
    session: AsyncSession = Depends(get_session)
):
    """
    Signup Flow:
    ─────────────────────────────────────────────────────────
    1. VALIDATE  — Check if email/username/phone already taken
    2. VALIDATE  — If profile picture provided, validate size (<5MB) 
                   and extension (.jpg/.jpeg/.png/.webp) BEFORE touching DB
    3. CREATE    — Insert user into DB (only after all validation passes)
    4. BACKGROUND — Dispatch profile picture save via Celery (non-blocking)
    5. BACKGROUND — Send verification email via Celery (non-blocking)
    6. RESPOND   — Return the created user object
    
    Why this order matters:
    - We validate the picture BEFORE creating the user so that if it fails
      (too large, bad extension), no orphan user is left in the DB.
    - The IntegrityError catch is a safety net for race conditions where
      the uniqueness check passes but a concurrent request inserts first.
    """
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

    email = user_data.email
    username = user_data.username
    phone = user_data.phone

    # ── Step 1: Check if user already exists ──────────────────────
    is_existed = await user_service.user_exist(email, phone, username, session)
    if is_existed:
        raise UserAlreadyExists()

    # ── Step 2: Validate profile picture BEFORE creating user ─────
    # This prevents orphan users in DB if the picture is invalid
    picture_bytes = None
    picture_ext = None

    if user_data.profile_picture:
        # Validate file extension early
        picture_ext = Path(user_data.profile_picture.filename).suffix.lower()
        if picture_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{picture_ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Read file in chunks to enforce size limit without loading all into memory
        total_size = 0
        all_chunks = []
        while True:
            chunk = await user_data.profile_picture.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
            all_chunks.append(chunk)

        picture_bytes = b''.join(all_chunks)

    # ── Step 3: Create user in DB (safe — validation already passed) ──
    try:
        new_user = await user_service.create_user(user_data, session)
    except IntegrityError:
        # Race condition: another request inserted the same user between
        # our existence check and the INSERT — treat as duplicate
        raise UserAlreadyExists()

    # ── Step 4: Dispatch profile picture save (background) ────────
    if picture_bytes:
        picture_bytes_b64 = base64.b64encode(picture_bytes).decode('utf-8')
        bg_save_profile_picture.delay(picture_bytes_b64, picture_ext, str(new_user.id))

    # ── Step 5: Send verification email (background) ─────────────
    token = email_verification_link.create_safe_url({"email": email})
    link = f'{config.domain}/auth/verify/{token}'
    bg_send_mail.delay(
        rec=[email],
        sub='verify email',
        html_path='verify_message.html',
        data_var={"link": link}
    )

    # ── Step 6: Return created user ──────────────────────────────
    return new_user



"""verify the URL to check is valid"""  
@auth_router.get("/verify/{token}")

async def activation_user(token: str, session: AsyncSession = Depends(get_session)):
    
    data = email_verification_link.de_serializ_url(token)
    
    if await check_blacklist(data['token_id']):
        raise UserAlreadyVerify()
    
    email = data['email']
    if not email:
        raise VerificationError()
    
    await user_service.activation_user(email, session)
    
    await add_to_blacklist(data['token_id'], exp=1600)

    return JSONResponse(
            content={"message": "Account verified successfully"},
            status_code=status.HTTP_200_OK,
        )    



@auth_router.post('/resend_verify_link')
async def create_url_verification(email_data: Password_Reset, session: AsyncSession = Depends(get_session)):
    email = email_data.email
    if not email:
        raise DataNotFound()
    
    user = await user_service.get_user_by_email(email, session)
    
    if user:
        token = email_verification_link.create_safe_url({"email": email})
      
        link = f'{config.domain}/auth/verify/{token}'
        
        data = {"link": link}
        
        bg_send_mail.delay(rec=[email], sub='verifying mail', html_path='verify_message.html', data_var=data)
    
    # Always return success to prevent email enumeration
    return JSONResponse(
        content={"message": "If the email exists, a verification link has been sent."},
        status_code=status.HTTP_200_OK,
    )




@auth_router.post('/login')
async def login_user(user_data: Login_User, session: AsyncSession = Depends(get_session)):
    user_data_login = user_data
    email = user_data_login.email
    phone = user_data_login.phone
    password = user_data_login.password
    
    user_existence: User_DB = await user_service.get_user_by_email(email, session)
    if not user_existence and phone:
        user_existence: User_DB = await user_service.get_user_by_phone(phone, session)
    
    if not user_existence:
        raise UserNotFound()
    
    if not password:
        raise InvalidCredentials()
    is_valid_password = verify_password(password, user_existence.password_hash) 
     
    if not is_valid_password:
        raise InvalidCredentials()
        
        # Create tokens
    access_token_str = access_token(
            user_data={
                "email": user_existence.email,
                "id": str(user_existence.id),
                "username": user_existence.username,
            },
            expire=access
        )
        
    refresh_token_str = access_token(
            user_data={
                "email": user_existence.email,
                "id": str(user_existence.id),
                "username": user_existence.username,
            },
            expire=refresh,
            refresh=True
        )  
        
    return JSONResponse(
            content={
                "message": "you have login successfully",
                "access_token": access_token_str,
                "refresh_token": refresh_token_str,
                "email": user_existence.email,
                "phone": user_existence.phone,
                "username": user_existence.username,
                "user_id": str(user_existence.id)
            },
            status_code=200
        )
    



    
@auth_router.post('/refresh_token')
async def get_acces_by_refresh(token: dict = Depends(RefreshToken())):
    
    if token:
        new_access_token = access_token(user_data=token['user'], expire=access)
        
        return JSONResponse(
               content={
                  "access_token": new_access_token
             })
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
                        detail='this token either expired or invalid')
     
    
@auth_router.post('/logout')
async def logout(token: dict = Depends(AccessTokenBearer())):
    
    if await add_to_blacklist(token['jti']):
        return JSONResponse(
            content={"message": "you have logged out successfully"},
            status_code=200,

        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout"
        )    
    
    
    """
    
    notice this for forget Password reset flow , not regular reset password this in case the user forget the original password
    
    1: user request to resent his password 
    
    2: the token or the email exctracted from but be carfull , we check if exist or not then if exist 

    3: we shall send to this user mail an uniuque link that contain a token with period expiration and this email
        
    4: when the user click on this link and the link is valid the user can now reset the password and revoke the token of authorization 
    and add to the redis black list
    
    
    5: after the user has successfully updated the password the access ,refresh and link token must be revoked and added to the redis blacklist
    
    """ 
   # Notice this is for forgetting password and not in normal reset password 
@auth_router.post('/password_reset')
async def passsword_reset(Email: Password_Reset, session: AsyncSession = Depends(get_session)):
    email = Email.email
    
    user_existence = await user_service.get_user_by_email(email, session)
    
    if not user_existence:
        raise UserNotFound()
    
    try:
        token = password_reset_link.create_safe_url({"email": email})
        
        # Point to CLIENT URL
        link = f'{config.domain}/reset-password/{token}'
        
        data = {"link": link}
        
        bg_send_mail.delay(rec=[email],
                            data_var=data, html_path='password_reset_link.html',
                            sub='Reset Email Password')
      
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )
    
    return JSONResponse(
        content={"message": "If the email exists, a reset link has been sent."},
        status_code=200
    )


@auth_router.post("/confirm_password/{token}")
async def confirm_password(passwords: Password_reset_Confirm,
                           token: str, session: AsyncSession = Depends(get_session)):
    
    data = password_reset_link.de_serializ_url(token, 600)
    
    """check if this link is beeing sent again to prevent it from consuming resourse """
    if await check_blacklist(data['token_id']):
        raise PasswordAlreadyReset()
    

    if not passwords.new_password == passwords.confirm_password:
        raise InvalidCredentials()
    
    email = data['email']
    if not email:
        raise DataNotFound()

    user_exist = await user_service.get_user_by_email(email, session)
    if not user_exist:
        raise UserNotFound()

    new_password = generate_hashed_password(passwords.new_password)
    user_exist.password_hash = new_password
    await session.commit()
    await session.refresh(user_exist)
    
    # Only blacklist the RESET token
    await add_to_blacklist(data['token_id'], exp=600)
    
    return JSONResponse(
            content={"message": "Password has been updated successfully"},
            status_code=status.HTTP_200_OK,
        )  

@auth_router.post('/change_password')
async def change_password(
    passwords: ChangePassword,
    session: AsyncSession = Depends(get_session),
    user_data: User = Depends(get_current_user)
):
    # 1. Verify current password
    user = await user_service.get_user_by_email(user_data.email, session)
    if not user:
        raise UserNotFound()
        
    if not verify_password(passwords.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    # 2. Hash new password and update
    user.password_hash = generate_hashed_password(passwords.new_password)
    
    await session.commit()
    
    return JSONResponse(
        content={"message": "Password updated successfully"},
        status_code=200
    )  
