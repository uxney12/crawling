#drive_service.py 
import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from io import BytesIO

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Kết nối Google Drive API và trả về service."""
    creds = None
    token_path = 'token.json' 
    creds_path = r'E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\the_SHEA\client_secret_48007665362-e95q27jl2fb9gog9ftt6lq7uagph565n.apps.googleusercontent.com.json'  # File tải từ Google Cloud

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def read_csv_from_drive(file_id):
    """Đọc file CSV trực tiếp từ Google Drive."""
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    file_data = BytesIO(request.execute())

    df = pd.read_csv(file_data)

    return df
