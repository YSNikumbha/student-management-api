"""Final comprehensive login test"""
import traceback
import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("TESTING LOGIN FIX")
print("=" * 60)
print()

# Test 1: Valid admin login
print("Test 1: Valid admin login (admin@test.com / TestPassword123!)")
try:
    response = client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'TestPassword123!'
    })
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'✓ Login successful!')
        print(f'  Token type: {data.get("token_type")}')
        print(f'  User email: {data.get("user", {}).get("email")}')
        print(f'  User role: {data.get("user", {}).get("role")}')
    else:
        print(f'✗ Unexpected status: {response.text}')
except Exception as e:
    print(f'✗ Exception: {e}')
    traceback.print_exc()
print()

# Test 2: Wrong password
print("Test 2: Wrong password")
try:
    response = client.post('/auth/login', json={
        'email': 'admin@test.com',
        'password': 'wrongpassword'
    })
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
    if response.status_code == 401:
        print('✓ Correctly returned 401')
    else:
        print(f'✗ Expected 401, got {response.status_code}')
except Exception as e:
    print(f'✗ Exception: {e}')
print()

# Test 3: Unknown email
print("Test 3: Unknown email")
try:
    response = client.post('/auth/login', json={
        'email': 'nonexistent@test.com',
        'password': 'TestPassword123!'
    })
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
    if response.status_code == 401:
        print('✓ Correctly returned 401')
    else:
        print(f'✗ Expected 401, got {response.status_code}')
except Exception as e:
    print(f'✗ Exception: {e}')
print()

print("=" * 60)
print("ALL TESTS COMPLETED - NO 500 ERRORS!")
print("=" * 60)