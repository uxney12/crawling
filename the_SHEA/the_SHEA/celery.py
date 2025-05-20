import os
from celery import Celery

# Đặt biến môi trường để chỉ định file settings của Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the_SHEA.settings')

# Khởi tạo Celery app
app = Celery('the_SHEA')

# Cấu hình Celery từ file settings.py, với namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tự động tìm các task trong các ứng dụng Django
app.autodiscover_tasks()
