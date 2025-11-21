import os
from pathlib import Path

# --- Helper Functions ---
def make_dirs(dir_list):
    for d in dir_list:
        Path(d).mkdir(parents=True, exist_ok=True)

def make_files(file_list):
    for f in file_list:
        Path(f).touch(exist_ok=True)

# --- Directory Structure ---
dirs = [
    "backend/app/api",
    "backend/app/core",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/ml",
    "backend/app/websocket",
    "backend/tests",
    "frontend",
    ".github/workflows",
    "docs",
    "mlflow",
    "monitoring"
]

files = [
    "backend/app/__init__.py",
    "backend/app/api/__init__.py",
    "backend/app/core/__init__.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/__init__.py",
    "backend/app/ml/__init__.py",
    "backend/app/websocket/__init__.py",
    "backend/tests/__init__.py"
]

# --- Execute ---
print("Creating project structure...")

make_dirs(dirs)
make_files(files)

# Initialize git repo
print("Initializing git repository...")

os.system("git init")
os.system("git checkout -b evans-implementation")

print("\n✅ Project structure created successfully!")
