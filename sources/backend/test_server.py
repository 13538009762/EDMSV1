import requests
import io

url = "http://127.0.0.1:5000/api/admin/master-data/import"
# We'll need a real XLSX file to test
# For now, let's just see if we can get a response from /api/admin/status
status_url = "http://127.0.0.1:5000/api/admin/status"

try:
    r = requests.get(status_url)
    print(f"Status: {r.status_code}, {r.text}")
except Exception as e:
    print(f"Could not connect to server: {e}")
