import traceback
import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
try:
    response = client.post('/auth/login', json={'email': 'yash.nikumbha99@gmail.com', 'password': 'test'})
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
except Exception as e:
    print('Exception:')
    traceback.print_exc()
    sys.exit(1)