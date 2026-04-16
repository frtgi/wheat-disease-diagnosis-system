import requests
import json

# 登录获取 token
login_resp = requests.post('http://localhost:8001/api/v1/users/login', json={'username': 'test_admin', 'password': 'test123'})
token = login_resp.json()['access_token']

# 多模态诊断测试
image_path = r'd:\Project\wheatagent\tests\integration\test_data\test_image.jpg'
with open(image_path, 'rb') as f:
    files = {'image': ('test_image.jpg', f, 'image/jpeg')}
    data = {'symptoms': 'wheat leaf yellow stripes'}
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post('http://localhost:8001/api/v1/diagnosis/multimodal', files=files, data=data, headers=headers, timeout=120)
    print(f'Status: {resp.status_code}')
    result = resp.json()
    print(f'Success: {result.get("success")}')
    if result.get('success'):
        print(f'Disease: {result.get("data", {}).get("disease_name")}')
        print(f'Confidence: {result.get("data", {}).get("confidence")}')
    else:
        print(f'Error: {result.get("error")}')
