import requests
import json
import time
import threading
import sys

BASE_URL = 'http://localhost:8000/api/v1'
IMAGE_PATH = r'd:\Project\wheatagent\src\web\backend\tests\test_data\images\wheat_rust.png'

def get_token():
    resp = requests.post(f'{BASE_URL}/users/login', json={'username': 'test_admin', 'password': 'test123'}, timeout=30)
    data = resp.json()
    return data.get('data', {}).get('access_token')

def test_sse_diagnosis():
    token = get_token()
    if not token:
        print("[FAIL] Cannot get token")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    start = time.time()
    
    with open(IMAGE_PATH, 'rb') as f:
        files = {'image': ('wheat_rust.png', f, 'image/png')}
        resp = requests.post(f'{BASE_URL}/diagnosis/fusion/stream', headers=headers, files=files, stream=True, timeout=600)
    
    if resp.status_code != 200:
        print(f"[FAIL] SSE status: {resp.status_code}")
        return False
    
    events = []
    complete_data = None
    for line in resp.iter_lines(decode_unicode=True):
        if line:
            if line.startswith('event:'):
                evt = line[6:].strip()
                events.append(('event', evt))
                print(f"  event: {evt}")
            elif line.startswith('data:'):
                try:
                    data = json.loads(line[5:].strip())
                    events.append(('data', data))
                    if data.get('stage') == 'complete' or data.get('event') == 'complete':
                        complete_data = data
                except:
                    pass
    
    elapsed = time.time() - start
    
    if not complete_data:
        print(f"[FAIL] No complete event received ({len(events)} events, {elapsed:.1f}s)")
        return False
    
    diagnosis = complete_data.get('diagnosis', {})
    required_fields = ['disease_name', 'disease_name_en', 'confidence', 'visual_confidence',
                       'textual_confidence', 'knowledge_confidence', 'description', 'symptoms',
                       'causes', 'recommendations', 'treatment', 'medicines', 'severity',
                       'knowledge_references', 'roi_boxes']
    
    missing = [f for f in required_fields if f not in diagnosis]
    if missing:
        print(f"[FAIL] Missing fields: {missing}")
        return False
    
    print(f"[PASS] SSE diagnosis: {diagnosis.get('disease_name')} (conf={diagnosis.get('confidence'):.3f}, severity={diagnosis.get('severity')})")
    print(f"  Fields: {len(required_fields)}/{len(required_fields)} present")
    print(f"  Events: {len(events)}, Time: {elapsed:.1f}s")
    return True

def test_event_loop_non_blocking():
    token = get_token()
    if not token:
        print("[FAIL] Cannot get token")
        return False
    
    health_ok = False
    health_times = []
    done_event = threading.Event()
    
    def health_loop():
        nonlocal health_ok
        while not done_event.is_set():
            try:
                r = requests.get('http://localhost:8000/health', timeout=5)
                if r.status_code == 200:
                    health_ok = True
                    print(f"  [Health] OK during inference")
                else:
                    print(f"  [Health] Status {r.status_code}")
            except Exception as e:
                print(f"  [Health] Error: {e}")
            done_event.wait(3)
    
    t = threading.Thread(target=health_loop, daemon=True)
    t.start()
    
    headers = {'Authorization': f'Bearer {token}'}
    start = time.time()
    with open(IMAGE_PATH, 'rb') as f:
        files = {'image': ('wheat_rust.png', f, 'image/png')}
        resp = requests.post(f'{BASE_URL}/diagnosis/fusion/stream', headers=headers, files=files, stream=True, timeout=600)
        for line in resp.iter_lines(decode_unicode=True):
            pass
    
    done_event.set()
    t.join(timeout=5)
    elapsed = time.time() - start
    
    if health_ok:
        print(f"[PASS] Event loop non-blocking: health check OK during inference ({elapsed:.1f}s)")
        return True
    else:
        print(f"[FAIL] Event loop blocked: no health check succeeded during inference")
        return False

def test_diagnosis_records_and_detail():
    token = get_token()
    if not token:
        print("[FAIL] Cannot get token")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    resp = requests.get(f'{BASE_URL}/diagnosis/records', headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"[FAIL] Records status: {resp.status_code}")
        return False
    
    data = resp.json()
    records = data.get('records', [])
    print(f"[PASS] Diagnosis records: {len(records)} records")
    
    if records:
        first_id = records[0].get('id')
        if first_id:
            detail_resp = requests.get(f'{BASE_URL}/diagnosis/{first_id}', headers=headers, timeout=30)
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                suggestions = detail.get('suggestions')
                if suggestions is None or isinstance(suggestions, list):
                    print(f"[PASS] Diagnosis detail: id={first_id}, suggestions type={type(suggestions).__name__}")
                    return True
                else:
                    print(f"[FAIL] Suggestions type: {type(suggestions).__name__}, expected list")
                    return False
            else:
                print(f"[FAIL] Detail status: {detail_resp.status_code}")
                return False
    
    print("[PASS] Diagnosis detail: no records to check (skipped)")
    return True

if __name__ == '__main__':
    print("=" * 70)
    print("  V17 Slow E2E Tests (SSE Diagnosis + Event Loop)")
    print("=" * 70)
    
    results = {}
    
    print("\n[Test 1] SSE Fusion Diagnosis")
    results['sse_diagnosis'] = test_sse_diagnosis()
    
    print("\n[Test 2] Diagnosis Records & Detail")
    results['records_detail'] = test_diagnosis_records_and_detail()
    
    print("\n[Test 3] Event Loop Non-Blocking")
    results['event_loop'] = test_event_loop_non_blocking()
    
    print("\n" + "=" * 70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"  Results: {passed}/{total} passed")
    for k, v in results.items():
        status = "PASS" if v else "FAIL"
        print(f"  [{status}] {k}")
    print("=" * 70)
    
    sys.exit(0 if passed == total else 1)
