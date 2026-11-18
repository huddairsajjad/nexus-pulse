"""
Verify syntax, run zero-dummy-data cleanup, run full pytest, and push to git.
"""
import subprocess, sys, py_compile, sqlite3, os

REPO = r"C:\Users\STONE\Desktop\rabbi"
DB_PATH = os.path.join(REPO, "database", "nexus_vault.db")

FILES_TO_CHECK = [
    r"core\outreach\reply_listener.py",
    r"database\db_engine.py",
]

print("=" * 60)
print("STEP 1: Python syntax check")
all_ok = True
for f in FILES_TO_CHECK:
    full = os.path.join(REPO, f)
    try:
        py_compile.compile(full, doraise=True)
        print(f"  OK: {f}")
    except py_compile.PyCompileError as e:
        print(f"  FAIL: {f} -> {e}")
        all_ok = False

if not all_ok:
    print("Syntax errors found. Aborting.")
    sys.exit(1)

print("\nSTEP 2: Zero-dummy-data DB cleanup")
try:
    conn = sqlite3.connect(DB_PATH)
    tables = ["vault_leads", "outreach_queue", "inbox_replies",
              "blacklist_rules", "suppressed_entities", "dnc_blacklist",
              "dedup_registry", "followup_sequences"]
    for tbl in tables:
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM {tbl}")
            cnt = cur.fetchone()[0]
            if cnt > 0:
                conn.execute(f"DELETE FROM {tbl}")
                print(f"  Purged {cnt} rows from {tbl}")
            else:
                print(f"  Clean: {tbl} (0 rows)")
        except sqlite3.OperationalError as e:
            print(f"  Skip {tbl}: {e}")
    # Keep operator_sessions (admin login state)
    op_cnt = conn.execute("SELECT COUNT(*) FROM operator_sessions").fetchone()[0]
    print(f"  Preserved operator_sessions ({op_cnt} rows)")
    conn.commit()
    conn.close()
    print("  DB cleanup complete.")
except Exception as e:
    print(f"  DB cleanup error (non-fatal): {e}")

print("\nSTEP 3: Full pytest run")
result = subprocess.run(
    ["python", "-m", "pytest", "-v", "--tb=short", "-q"],
    cwd=REPO,
    capture_output=True, text=True
)
print(result.stdout[-4000:] if len(result.stdout) > 4000 else result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr[-1000:])
    print("\nSome tests failed. Check output above.")
    sys.exit(1)
print("All tests passed.")

print("\nSTEP 4: Git commit and push")
cmds = [
    ["git", "add", "-A"],
    ["git", "commit", "-m",
     "feat: custom niche UI, IMAP enrolled-sender whitelist, reply-kanban sync vectors D+E, msg-id dedup, positive-engagement bypass"],
    ["git", "push", "origin", "main"]
]
for cmd in cmds:
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    print(f"  $ {' '.join(cmd)}")
    if r.stdout.strip():
        print("   ", r.stdout.strip()[:300])
    if r.returncode != 0:
        if "nothing to commit" in (r.stdout + r.stderr):
            print("  (Nothing new to commit — already up to date)")
        else:
            print("  STDERR:", r.stderr.strip()[:500])
            # Don't abort on push stderr noise (Windows git prints to stderr)
    else:
        if r.stderr.strip():
            print("   ", r.stderr.strip()[:200])

print("\nDONE.")
