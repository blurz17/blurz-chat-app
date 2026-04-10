
import bcrypt
from db.config import config
from datetime import timedelta ,datetime,timezone
import jwt
from db.config import config
import uuid
from errors import InvalidToken,TokenExpired
import logging
from itsdangerous import URLSafeTimedSerializer,URLSafeSerializer,SignatureExpired,BadSignature
import uuid
def generate_hashed_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')[:72]
    
    rounds = config.BCRYPT_ROUNDS
    
    salt = bcrypt.gensalt(rounds)  
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash"""
   
    password_bytes = password.encode('utf-8')[:72]
    
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Verify
    return bcrypt.checkpw(password_bytes, hashed_bytes) # return a boolean 


def access_token(user_data:dict,expire:timedelta=None,refresh:bool=False):
    default_time = 30
    payload = {
        "user":user_data,
        "exp":datetime.now(timezone.utc)+ (expire if expire is not None else timedelta(minutes=default_time)) ,
        "jti":str(uuid.uuid4()),
        'refresh_token':refresh,
        "iat": datetime.now(timezone.utc),
    }

# remember that the exp field is a keyword in the jwt definition so don't make it as expiry this false 
    
    token = jwt.encode(
        payload =payload,
        key = config.jwt_secret,
        algorithm = config.jwt_algorithm)
    
    return token

def decode_token(token_data:str):
    try:
        return jwt.decode(jwt=token_data, 
                          key=config.jwt_secret,
                          algorithms=[config.jwt_algorithm]
                          )
    except jwt.exceptions.ExpiredSignatureError:
        logging.exception("Token expired")
        raise TokenExpired()
    except jwt.InvalidTokenError:
        raise InvalidToken()
    
    except Exception as e :
        logging.exception(f'Unknown error decoding token: {e}')    
    return None


# this calss is intedent to create a safe url for the user to verify his email or reset his password 
# and make the accounts real and active  


class CreationSafeLink(URLSafeTimedSerializer):
    def __init__(self,secret_key:str,salt:str):
        super().__init__(secret_key=secret_key,salt=salt)
        
    def create_safe_url(self,data:dict=None):
        id = str(uuid.uuid4())
        if data is None:
            data={}
            
        data['token_id'] = id
        token = self.dumps(data)
        print(token)
        return token


    def de_serializ_url(self,token:str,max_age=1800):
        try:
            data = self.loads(token,max_age=max_age)
            return data

        except SignatureExpired as e:
            logging.error(f'Token has expired: {e}')
            raise TokenExpired()  
        
        except BadSignature as e:
            logging.error(f'Invalid token signature: {e}')
            raise InvalidToken()  
        
        except Exception as e:
            logging.exception(f'Unknown error decoding token: {e}')
            raise InvalidToken()

        
