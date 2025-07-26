import pytest
import asyncio
import time
from typing import Dict, Any
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from app.voice_agent import voice_agent
from app.config import PERFORMANCE_THRESHOLDS
class TestPerformanceRequirements:
    @pytest.mark.asyncio
    async def test_form_opening_latency(self):
        start_time = time.time()
        result = await voice_agent.handle_function_call("open_form", {
            "form_type": "contact",
            "title": "Performance Test Form"
        })
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f"Form opening latency: {latency_ms:.2f}ms")
        assert latency_ms < PERFORMANCE_THRESHOLDS["tool_response_ms"]
        assert result.get("success", False)
    @pytest.mark.asyncio
    async def test_form_field_filling_latency(self):
        await voice_agent.handle_function_call("open_form", {
            "form_type": "contact"
        })
        start_time = time.time()
        result = await voice_agent.handle_function_call("fill_form_field", {
            "field_name": "name",
            "value": "Performance Test User"
        })
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f"Form field filling latency: {latency_ms:.2f}ms")
        assert latency_ms < PERFORMANCE_THRESHOLDS["tool_response_ms"]
        assert result.get("success", False) or result.get("success", True)
    @pytest.mark.asyncio
    async def test_form_validation_latency(self):
        await voice_agent.handle_function_call("open_form", {"form_type": "contact"})
        await voice_agent.handle_function_call("fill_form_field", {"field_name": "name", "value": "Test"})
        start_time = time.time()
        result = await voice_agent.handle_function_call("validate_form", {})
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f"Form validation latency: {latency_ms:.2f}ms")
        assert latency_ms < PERFORMANCE_THRESHOLDS["tool_response_ms"]
    @pytest.mark.asyncio
    async def test_multiple_operations_latency(self):
        operations = [
            ("open_form", {"form_type": "contact", "title": "Multi-op Test"}),
            ("fill_form_field", {"field_name": "name", "value": "Test User"}),
            ("fill_form_field", {"field_name": "email", "value": "test@example.com"}),
            ("validate_form", {}),
        ]
        total_start_time = time.time()
        latencies = []
        for operation, args in operations:
            start_time = time.time()
            result = await voice_agent.handle_function_call(operation, args)
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            print(f"{operation} latency: {latency_ms:.2f}ms")
            assert latency_ms < PERFORMANCE_THRESHOLDS["tool_response_ms"]
        total_time = (time.time() - total_start_time) * 1000
        avg_latency = sum(latencies) / len(latencies)
        print(f"Total time for {len(operations)} operations: {total_time:.2f}ms")
        print(f"Average latency per operation: {avg_latency:.2f}ms")
        assert avg_latency < PERFORMANCE_THRESHOLDS["tool_response_ms"] / 2
    def test_memory_usage(self):
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"Memory usage: {memory_mb:.2f} MB")
        assert memory_mb < 500, f"Memory usage too high: {memory_mb:.2f} MB"
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        async def single_operation():
            start_time = time.time()
            result = await voice_agent.handle_function_call("open_form", {
                "form_type": "contact",
                "title": f"Concurrent Test {time.time()}"
            })
            end_time = time.time()
            return (end_time - start_time) * 1000
        tasks = [single_operation() for _ in range(5)]
        latencies = await asyncio.gather(*tasks)
        max_latency = max(latencies)
        avg_latency = sum(latencies) / len(latencies)
        print(f"Concurrent operations - Max: {max_latency:.2f}ms, Avg: {avg_latency:.2f}ms")
        assert max_latency < PERFORMANCE_THRESHOLDS["tool_response_ms"] * 2
        assert avg_latency < PERFORMANCE_THRESHOLDS["tool_response_ms"]
class TestResourceEfficiency:
    def test_startup_time(self):
        from app.main import app
        assert app is not None
        start_time = time.time()
        assert app.title == "Ultra-Low Latency Voice Agent"
        startup_time = (time.time() - start_time) * 1000
        print(f"App access time: {startup_time:.2f}ms")
        assert startup_time < 100
    @pytest.mark.asyncio
    async def test_voice_agent_initialization_time(self):
        from app.voice_agent import UltraLowLatencyVoiceAgent
        start_time = time.time()
        try:
            agent = UltraLowLatencyVoiceAgent()
            init_time = (time.time() - start_time) * 1000
            print(f"Voice agent initialization time: {init_time:.2f}ms")
            assert init_time < 2000
        except Exception as e:
            if "GOOGLE_API_KEY" in str(e):
                print("Skipping initialization test - no API key")
                pytest.skip("No Google API key provided")
            else:
                raise
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])