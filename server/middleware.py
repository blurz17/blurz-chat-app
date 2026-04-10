from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time 
import logging

logger = logging.getLogger(__name__)

"""simple middleware type one"""


 #   the functions of the middleware are : logging request , authuntication like in the dependencies injection 
 # , cors origins and prevent host attack  , Rate lImiting , 
 
def custome_simple_middle(app: FastAPI):
    
    @app.middleware('http')
    
    async def custome_logging(request: Request, call_next):
        
        start_time = time.time()
                
        response = await call_next(request)
        
        processed_time = time.time() - start_time
         
        message = f"{request.client.host}:{request.client.port} - {request.method} - {request.url.path} - completed after {processed_time:.3f}s"
        
        logger.info(message)
        
        return response
    
    app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://localhost:5173'],
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE', 'PUT', 'OPTIONS'],
    allow_headers=['*'],
    allow_credentials=True,
       
    )
    
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=['*'],

    )
