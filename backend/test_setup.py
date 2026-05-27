"""
test_setup.py
─────────────
Run this before starting the server to validate your environment.
Usage: python test_setup.py
"""

import sys
import os

print("=" * 60)
print("  Alpha-Cure Backend — Environment Validation")
print("=" * 60)

errors = []
warnings = []

# ─── Python version ────────────────────────────────────────────────────────────
py_ver = sys.version_info
print(f"\n[1] Python version: {py_ver.major}.{py_ver.minor}.{py_ver.micro}", end=" ")
if py_ver.major == 3 and py_ver.minor >= 10:
    print("✓")
else:
    print("⚠️  Recommend Python 3.10+")
    warnings.append("Python version < 3.10")

# ─── Required packages ─────────────────────────────────────────────────────────
print("\n[2] Checking required packages:")
packages = [
    ("flask", "Flask"),
    ("flask_cors", "Flask-CORS"),
    ("flask_socketio", "Flask-SocketIO"),
    ("pymongo", "PyMongo"),
    ("jwt", "PyJWT"),
    ("bcrypt", "bcrypt"),
    ("dotenv", "python-dotenv"),
    ("numpy", "NumPy"),
    ("sklearn", "scikit-learn"),
    ("reportlab", "ReportLab"),
    ("eventlet", "eventlet"),
]
optional = [
    ("tensorflow", "TensorFlow"),
    ("openai", "OpenAI"),
]

for module, name in packages:
    try:
        __import__(module)
        print(f"    {name} ✓")
    except ImportError:
        print(f"    {name} ✗ MISSING")
        errors.append(f"{name} not installed")

print("  Optional:")
for module, name in optional:
    try:
        mod = __import__(module)
        ver = getattr(mod, '__version__', '?')
        print(f"    {name} {ver} ✓")
    except ImportError:
        print(f"    {name} ✗ (not installed — mock mode will be used)")
        warnings.append(f"{name} not installed — using fallback")

# ─── Environment variables ─────────────────────────────────────────────────────
print("\n[3] Checking environment variables:")
from dotenv import load_dotenv
load_dotenv()

required_env = ["MONGO_URI", "JWT_SECRET"]
optional_env = ["SMTP_USER", "SMTP_PASS", "OPENAI_API_KEY", "GOOGLE_MAPS_API_KEY"]

for key in required_env:
    val = os.getenv(key)
    if val:
        masked = val[:6] + "..." if len(val) > 6 else "***"
        print(f"    {key}: {masked} ✓")
    else:
        print(f"    {key}: NOT SET ✗")
        errors.append(f"Environment variable {key} not set")

for key in optional_env:
    val = os.getenv(key)
    if val and val not in ("your_openai_key_here", "your_google_maps_key_here",
                            "your_email@gmail.com", "your_app_password"):
        masked = val[:8] + "..." if len(val) > 8 else "***"
        print(f"    {key}: {masked} ✓")
    else:
        print(f"    {key}: not configured (optional feature disabled)")
        warnings.append(f"{key} not configured")

# ─── MongoDB connection ─────────────────────────────────────────────────────────
print("\n[4] Testing MongoDB connection:")
try:
    from pymongo import MongoClient
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/alphacure")
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    client.server_info()
    print(f"    Connected to MongoDB ✓")
    client.close()
except Exception as e:
    print(f"    MongoDB connection failed ✗: {e}")
    errors.append("Cannot connect to MongoDB")

# ─── Model files ───────────────────────────────────────────────────────────────
print("\n[5] Checking model files:")
model_path = os.path.join(os.path.dirname(__file__), "models", "cancer_model.h5")
artifacts_path = os.path.join(os.path.dirname(__file__), "models", "model_artifacts.pkl")

if os.path.exists(model_path):
    size = os.path.getsize(model_path) / (1024 * 1024)
    print(f"    cancer_model.h5 ({size:.1f} MB) ✓")
else:
    print(f"    cancer_model.h5 not found → MOCK MODE will be used")
    warnings.append("No trained model — using mock predictions")

if os.path.exists(artifacts_path):
    size = os.path.getsize(artifacts_path) / 1024
    print(f"    model_artifacts.pkl ({size:.0f} KB) ✓")
else:
    print(f"    model_artifacts.pkl not found → MOCK MODE will be used")

# ─── Directories ───────────────────────────────────────────────────────────────
print("\n[6] Checking directories:")
for d in ["models", "uploads", "reports"]:
    path = os.path.join(os.path.dirname(__file__), d)
    if os.path.isdir(path):
        print(f"    {d}/ ✓")
    else:
        os.makedirs(path, exist_ok=True)
        print(f"    {d}/ created ✓")

# ─── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if errors:
    print(f"  ✗ {len(errors)} ERROR(S) — Fix before starting:")
    for e in errors:
        print(f"    • {e}")
    print("\n  Server cannot start until errors are resolved.")
else:
    print(f"  ✓ All critical checks passed!")

if warnings:
    print(f"\n  ⚠️  {len(warnings)} WARNING(S) — Optional features affected:")
    for w in warnings:
        print(f"    • {w}")

print("=" * 60)

if not errors:
    print("\n  Ready to start: python app.py\n")
    sys.exit(0)
else:
    sys.exit(1)
