from fastapi_mail import ConnectionConfig, MessageType, MessageSchema, FastMail
from db.config import config as Config
from pathlib import Path
from jinja2 import Template

BASE_DIR = Path(__file__).resolve().parent

Mail_Config = ConnectionConfig( 
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,
    MAIL_FROM=Config.MAIL_FROM,
    MAIL_PORT=587,
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_FROM_NAME=Config.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(BASE_DIR, "templates"),
)

mail = FastMail(config=Mail_Config)

async def welcome_message(recepients: list[str]):
    path_content = Path(BASE_DIR, "templates", 'welcome.html')
    with open(path_content, 'r', encoding='utf-8') as r:
        html_content = r.read()
        

    message = MessageSchema(recipients=recepients, subject='Welcome to Blurz Chat', subtype=MessageType.html, body=html_content)
    return message

"""notice the data_variables paramater is responsible for replacing the values in the html file like links """
def send_email(recepients: list[str], subject: str, html_message_path: str, data_variables: dict | None = None): 
    
    path_content = Path(BASE_DIR, "templates", html_message_path)
    
    with open(path_content, 'r', encoding='utf-8') as r:
        html_template = r.read()
    

    template = Template(html_template)
    html_content = template.render(**(data_variables or {}))
    
    message = MessageSchema(
        recipients=recepients,
        subject=subject,
        subtype=MessageType.html,
        body=html_content,
    )
    
    return message
