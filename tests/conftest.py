import pytest
import os
import sys

# Add the project root to the path so modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load the environment variables for testing purposes
from scripts.load_env import load_env
load_env(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')))

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Fixture to ensure the necessary directories for the simulated MQ exist.
    """
    mq_base_dir = os.environ.get("MQ_BASE_DIR")
    if not mq_base_dir:
        # Fallback if .env loading failed
        mq_base_dir = "parallel_orchestration/mq"
        
    new_dir = os.path.join(mq_base_dir, os.environ.get("MQ_TOPIC_DISK_USAGE", "disk_usage"), "new")
    archive_dir = os.path.join(mq_base_dir, os.environ.get("MQ_TOPIC_DISK_USAGE", "disk_usage"), "archive")
    
    os.makedirs(new_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)
    
    # Clean up any old files before the test run
    for f in os.listdir(new_dir):
        os.remove(os.path.join(new_dir, f))
    for f in os.listdir(archive_dir):
        os.remove(os.path.join(archive_dir, f))
        
    print(f"\n[SETUP] Test environment initialized. MQ directories created/cleaned.")
    
    # Yield control to the tests
    yield
    
    # Teardown (optional cleanup after all tests)
    print("\n[TEARDOWN] Test run complete.")
