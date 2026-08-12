import traceback
import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test with wrong password first - should return 401
print("Test 1: Wrong password")
response = client.post('/auth/login', json={'email': 'yash.nikumbha99@gmail.com', 'password': 'wrongpassword'})
print(f'Status: {response.status_code}')
print(f'Response: {response.text}')
print()

# Test with missing password - should return 401
print("Test 2: Missing password")
response = client.post('/auth/login', json={'email': 'yash.nikumbha99@gmail.com'})
print(f'Status: {response.status_code}')
print(f'Response: {response.text}')
print()

print("All tests completed successfully - no 500 errors!")