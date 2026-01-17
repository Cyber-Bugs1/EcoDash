from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import time
import ssl

# -------------------------------
# CONFIG
# -------------------------------
SERVICE_ACCOUNT_FILE = "keys/drive_key.json"
FOLDER_NAME = "GEE_Exports"
DOWNLOAD_DIR = "data/raw"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# -------------------------------
# AUTH
# -------------------------------
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("drive", "v3", credentials=creds)

# -------------------------------
# FIND FOLDER ID
# -------------------------------
folder_query = f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder'"
folder_results = service.files().list(q=folder_query).execute()

if not folder_results["files"]:
    raise Exception("GEE_Exports folder not found")

folder_id = folder_results["files"][0]["id"]

print("Found folder:", folder_id)

# -------------------------------
# LIST FILES IN FOLDER
# -------------------------------
query = f"'{folder_id}' in parents and mimeType='text/csv'"
results = service.files().list(q=query).execute()
files = results.get("files", [])

print(f"Found {len(files)} CSV files")

# -------------------------------
# DOWNLOAD FILES
# -------------------------------
MAX_RETRIES = 5

for file in files:
    file_id = file["id"]
    file_name = file["name"]
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

    print("Downloading:", file_name)

    for attempt in range(MAX_RETRIES):
        try:
            request = service.files().get_media(fileId=file_id)
            fh = io.FileIO(file_path, "wb")
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"  Progress: {int(status.progress() * 100)}%")
            
            fh.close()
            print(f"  ✓ Downloaded successfully")
            break  # Success - exit retry loop
            
        except (ssl.SSLError, ConnectionError, TimeoutError) as e:
            fh.close()
            if attempt < MAX_RETRIES - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4, 8, 16 seconds
                print(f"  ⚠ Error: {e}. Retrying in {wait_time}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            else:
                print(f"  ✗ Failed after {MAX_RETRIES} attempts: {e}")
                raise

print("\n✓ All files downloaded successfully")
