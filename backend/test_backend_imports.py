import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
def test_backend_imports():
    try:
        print("Testing main app import...")
        from app.main import app
        print("Main app imported successfully")
        print("Testing pipecat agent import...")
        from app.pipecat_agent import pipecat_agent
        print("Pipecat agent imported successfully")
        print("Testing complete pipecat agent import...")
        from app.complete_pipecat_agent import complete_pipecat_agent
        print("Complete pipecat agent imported successfully")
        print("Testing form manager import...")
        from app.tools.form_manager import FormManager
        print("Form manager imported successfully")
        print("Testing services imports...")
        from app.services.gemini_live_service import gemini_live_service
        from app.services.audio_stream_processor import audio_stream_processor
        print("Services imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == "__main__":
    success = test_backend_imports()
    sys.exit(0 if success else 1)