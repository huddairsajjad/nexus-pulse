import urllib.request
import time
import json

base = 'https://nexus-pulse-production-b79d6aac.up.railway.app'
print('Monitoring Railway deployment ...')
print('Dashboard: https://railway.com/project/fb654d44-b02a-4c1c-8756-bdc8a072cdf2')
print()

success = False
for i in range(1, 31):
    try:
        req = urllib.request.Request(base + '/health', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as r:
            body = r.read().decode('utf-8')
            data = json.loads(body)
            s = data.get('status', '?')
            lic = data.get('licensed', '?')
            hw = data.get('hardware_id', '?')
            print(f'[Attempt {i:02d}] *** ACTIVE *** status={s} licensed={lic} hw={hw}')
            success = True
            break
    except urllib.error.HTTPError as e:
        snippet = ''
        try:
            snippet = e.read().decode('utf-8')[:80]
        except Exception:
            pass
        print(f'[Attempt {i:02d}] HTTP {e.code} :: {snippet}')
    except Exception as e:
        print(f'[Attempt {i:02d}] {type(e).__name__}: {e}')
    time.sleep(10)

if not success:
    print('Deployment still building or failed. Check Railway dashboard.')
