import urllib.request

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3ODYzNDgwOCwianRpIjoiNWEzZjBmYWMtNDVlNy00OWJmLWIyNjgtYTBkMzlkNDNiZDA4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3Nzg2MzQ4MDgsImNzcmYiOiI1N2M3YjM4Yi0xNmZkLTRhN2MtOGZiMS0yNTAyNzZhZWIyMGIifQ.gmthseXv_WXN4HRSa10yTudu76uBNKPIC2IWkrIIRkw"
req2 = urllib.request.Request('http://127.0.0.1:5000/api/documents?scope=all', headers={'Authorization': 'Bearer ' + token})
try:
    with urllib.request.urlopen(req2) as response:
        print(response.read())
except Exception as e:
    print('Error:', e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
