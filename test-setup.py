import sys
import subprocess
import os
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_backend():
    """Test backend functionality."""
    print("🧪 Testing Backend...")
    
    backend_dir = Path(__file__).parent / "backend"
    
    # Test basic imports
    print("  - Testing imports...")
    success, stdout, stderr = run_command(
        "python -c \"from app.main import app; from app.voice_agent import voice_agent; print('✅ Imports successful')\"",
        cwd=backend_dir
    )
    
    if not success:
        print(f"  ❌ Import test failed: {stderr}")
        return False
    else:
        print(f"  {stdout.strip()}")
    
    # Test configuration
    print("  - Testing configuration...")
    success, stdout, stderr = run_command(
        "python -c \"from app.config import settings; print(f'✅ Config loaded: {settings.host}:{settings.port}')\"",
        cwd=backend_dir
    )
    
    if not success:
        print(f"  ❌ Config test failed: {stderr}")
        return False
    else:
        print(f"  {stdout.strip()}")
    
    return True

def test_frontend():
    """Test frontend setup."""
    print("Testing Frontend...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Check if package.json exists
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("  ❌ package.json not found")
        return False
    
    print("  ✅ package.json found")
    
    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("  ⚠️  node_modules not found - dependencies may not be installed")
        return False
    
    print("  ✅ node_modules found")
    
    return True

def check_environment():
    """Check environment setup."""
    print("🌍 Checking Environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"  ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"  ❌ Python {python_version.major}.{python_version.minor} (3.8+ required)")
        return False
    
    # Check for Node.js
    success, stdout, stderr = run_command("node --version")
    if success:
        version = stdout.strip()
        print(f"  ✅ Node.js {version}")
    else:
        print("  ❌ Node.js not found")
        return False
    
    # Check for environment files
    backend_env = Path(__file__).parent / "backend" / ".env"
    frontend_env = Path(__file__).parent / "frontend" / ".env.local"
    
    if backend_env.exists():
        print("  ✅ Backend .env file found")
    else:
        print("  ⚠️  Backend .env file not found (copy from .env.example)")
    
    if frontend_env.exists():
        print("  ✅ Frontend .env.local file found") 
    else:
        print("  ⚠️  Frontend .env.local file not found (copy from .env.example)")
    
    return True

def main():
    """Main test runner."""
    print("🎤 Real-Time AI Voice Agent - Quick Test")
    print("=" * 50)
    
    all_passed = True
    
    # Env
    if not check_environment():
        all_passed = False
    
    print()
    
    # Backend
    if not test_backend():
        all_passed = False
    
    print()
    
    # Frontend
    if not test_frontend():
        all_passed = False
    
    print()
    print("=" * 50)
    
    if all_passed:
        print("🎉 All tests passed! Your setup looks good.")
        print()
        print("Next steps:")
        print("1. Make sure you have a Google API key in backend/.env")
        print("2. Run 'Start Full Stack' task in VS Code")
        print("3. Or run backend and frontend manually:")
        print("   - Backend: cd backend && python -m uvicorn app.main:app --reload")
        print("   - Frontend: cd frontend && npm run dev")
        print()
        print("URLs:")
        print("- Frontend: http://localhost:3000")
        print("- Backend API: http://localhost:8000")
        print("- API Docs: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the setup.")
        print()
        print("Common solutions:")
        print("1. Run the setup script: setup-dev.bat (Windows) or setup-dev.sh (Linux/Mac)")
        print("2. Install dependencies manually:")
        print("   - Backend: cd backend && pip install -r requirements.txt")
        print("   - Frontend: cd frontend && npm install")
        print("3. Copy environment files:")
        print("   - Backend: copy backend/.env.example to backend/.env")
        print("   - Frontend: copy frontend/.env.example to frontend/.env.local")
        
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
