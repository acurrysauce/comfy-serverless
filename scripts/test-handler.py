#!/usr/bin/env python3
"""
Test the RunPod handler locally without actually deploying
Simulates what RunPod does when calling your endpoint
"""

import json
import sys
import os

# Add the docker directory to path so we can import the handler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../docker'))

# Mock runpod module since we're testing locally
class MockRunPod:
    class serverless:
        @staticmethod
        def start(config):
            print("Handler loaded successfully!")
            print("Testing with sample workflow...")

            # Import the actual handler
            handler_func = config['handler']

            # Sample simple workflow (text-to-image)
            test_event = {
                "input": {
                    "workflow": {
                        # Add a simple test workflow here
                        # You'll need to create this from ComfyUI's "Save (API Format)"
                    },
                    "return_base64": True
                }
            }

            print("\nCalling handler with test event...")
            try:
                result = handler_func(test_event)
                print("\n=== RESULT ===")
                print(json.dumps(result, indent=2)[:500])  # First 500 chars

                if "error" in result:
                    print("\n❌ Handler returned error:", result['error'])
                    return False
                else:
                    print("\n✅ Handler executed successfully!")
                    return True

            except Exception as e:
                print(f"\n❌ Handler raised exception: {e}")
                import traceback
                traceback.print_exc()
                return False

# Mock the runpod import
sys.modules['runpod'] = MockRunPod()

# Now import and run the handler
print("Loading handler...")
try:
    import handler
    print("✅ Handler module loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load handler: {e}")
    import traceback
    traceback.print_exc()
