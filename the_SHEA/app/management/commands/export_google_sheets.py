import gspread
import pandas as pd
import decimal
from django.core.management.base import BaseCommand
from app.models import Product
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle


GOOGLE_CREDENTIALS_FILE = r"E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\the_SHEA\client_secret_48007665362-e95q27jl2fb9gog9ftt6lq7uagph565n.apps.googleusercontent.com.json"

SPREADSHEET_ID = "1KwPzsfdENtW-AsqcbygrugKhUYqXCOOlgSpARD5Udbs" 

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]

class Command(BaseCommand):
    help = "Xuất dữ liệu từ PostgreSQL lên Google Sheets"

    def authenticate_google(self):
        """Xác thực người dùng và lưu token đăng nhập."""
        creds = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)

            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        return creds

    def handle(self, *args, **kwargs):
            
        creds = self.authenticate_google()
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.sheet1

        self.stdout.write("🗑️ Đang xóa dữ liệu cũ...")
        sheet.clear()  
        self.stdout.write(self.style.WARNING("⚠️ Đã xóa toàn bộ dữ liệu cũ trong Google Sheet!"))

        data = list(Product.objects.values())
        if not data:
            self.stdout.write(self.style.ERROR("Không có dữ liệu để xuất!"))
            return

        df = pd.DataFrame(data)

        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

        df = df.applymap(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)

        self.stdout.write("📤 Đang ghi dữ liệu mới vào Google Sheet...")
        sheet.update([df.columns.tolist()] + df.values.tolist())

        self.stdout.write(self.style.SUCCESS("✅ Xuất dữ liệu thành công vào Google Sheet cố định!"))
