import sys
import traceback
def test_imports():
    imports_to_test = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Config"),
        ("pipecat.frames.frames", "AudioRawFrame"),
        ("pipecat.pipeline.pipeline", "Pipeline"),
        ("pipecat.pipeline.runner", "PipelineRunner"),
        ("pipecat.services.google", "GoogleLLMService"),
        ("pipecat.services.google", "GoogleTTSService"),
        ("pipecat.services.deepgram", "DeepgramSTTService"),
        ("pipecat.processors.frameworks.rtvi", "RTVIProcessor"),
        ("numpy", "array"),
        ("google.generativeai", "GenerativeModel"),
    ]
    failed_imports = []
    successful_imports = []
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            successful_imports.append(f"{module_name}.{class_name}")
            print(f"{module_name}.{class_name}")
        except Exception as e:
            failed_imports.append(f"{module_name}.{class_name}: {str(e)}")
            print(f"{module_name}.{class_name}: {str(e)}")
    print(f"\nSummary:")
    print(f"✅ Successful imports: {len(successful_imports)}")
    print(f"❌ Failed imports: {len(failed_imports)}")
    if failed_imports:
        print("\nFailed imports:")
        for failed in failed_imports:
            print(f"  - {failed}")
        return False
    return True
if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)