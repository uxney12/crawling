from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

gauth = GoogleAuth()
drive = GoogleDrive(gauth)

local_file_path = r'E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\clean_data.csv'
fixed_file_name = 'data.csv'
targetDirID = '1YrbRu-9lhwQzEavjDnaUjoCNT4U36_EM' 

if not os.path.exists(local_file_path):
    print("Tệp cục bộ không tồn tại!")
else:
    exist_file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(targetDirID)}).GetList()

    file_id = None

    for file in exist_file_list:
        if file['title'] == fixed_file_name:
            file_id = file['id']
            break

    if file_id:
        gfile = drive.CreateFile({'id': file_id})
        gfile.SetContentFile(local_file_path)
        gfile.Upload()
        print(f"✅ File updated successfully: {gfile['title']}")
    else:
        gfile = drive.CreateFile({'parents': [{'id': targetDirID}], 'title': fixed_file_name, 'mimeType': 'text/csv'})
        gfile.SetContentFile(local_file_path)
        gfile.Upload()
        print(f"✅ New file uploaded: {gfile['title']}")

    print(f"🔗 Link: {gfile['alternateLink']}")
