import requests
import mimetypes
import os

# Replace with the actual URL of your endpoint
url = "http://localhost:8000/upload-image"

# Path to the photo you want to upload
photo_path = "test.jpg"  # or .jpg

# Guess the MIME type based on the file extension
mime_type, _ = mimetypes.guess_type(photo_path)
if mime_type is None:
    mime_type = "application/octet-stream"

with open(photo_path, "rb") as photo_file:
    files = {"file": (os.path.basename(photo_path), photo_file, mime_type)}
    response = requests.post(url, files=files)

print("Status code:", response.status_code)
print("Response:", response.text)