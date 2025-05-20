import pandas as pd
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
from django.db import connection
from app.models import Product
from app.drive_service import read_csv_from_drive 

class Command(BaseCommand):
    help = "Cập nhật dữ liệu từ Google Drive vào database"

    def handle(self, *args, **kwargs):
        file_id = "1s4Ebcy_GyLKyCzMRyXVG4X2yLrqlviuH"

        df = read_csv_from_drive(file_id)
        if df.empty:
            self.stdout.write(self.style.ERROR("⚠️ File CSV không có dữ liệu!"))
            return

        total_before = len(df)
        self.stdout.write(self.style.SUCCESS(f"📌 Tổng số sản phẩm trong CSV: {total_before}"))

        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE app_product RESTART IDENTITY CASCADE;")
        self.stdout.write(self.style.WARNING("⚠️ Đã xóa toàn bộ dữ liệu cũ và reset ID về ban đầu!"))


        df[['sale', 'original_price', 'sale_price']] = df[['sale', 'original_price', 'sale_price']].fillna(0).astype(float)

        product_objects = [
            Product(
                website=row['website'],
                sku=row['sku'],
                name=row['name'],
                sale=row['sale'],
                original_price=row['original_price'],
                sale_price=row['sale_price'],
                sizes=row['sizes'],
                colors=row['colors'],
                description=row['description'],
                url=row['url'],
                images=row['images'],
                path=row['path'],
            )
            for _, row in df.iterrows()
        ]

        Product.objects.bulk_create(product_objects)

        total_in_db = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(f"📊 Tổng số sản phẩm trong database sau khi lưu: {total_in_db}"))

