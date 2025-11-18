import pytest
import json
import os
from src.ct_002_data_processor import process_resource_report, start_mq_listener

# --- Mock Data for Unit Testing ---
MOCK_VALID_REPORT = {
    "timestamp": "2025-11-17T10:00:00.000000",
    "team_id": "Data Team",
    "resource_type": "Disk Usage",
    "metrics": {
        "filesystem": "/dev/root",
        "size_gb": 40.0,
        "used_gb": 32.0,
        "available_gb": 8.0,
        "usage_percent": 80
    }
}

MOCK_LOW_USAGE_REPORT = {
    "timestamp": "2025-11-17T10:00:00.000000",
    "team_id": "Data Team",
    "resource_type": "Disk Usage",
    "metrics": {
        "filesystem": "/dev/root",
        "size_gb": 100.0,
        "used_gb": 10.0,
        "available_gb": 90.0,
        "usage_percent": 10
    }
}

MOCK_INVALID_REPORT_MISSING_KEY = {
    "timestamp": "2025-11-17T10:00:00.000000",
    "team_id": "Data Team",
    "metrics": {
        "size_gb": 40.0,
        "used_gb": 32.0,
        "available_gb": 8.0,
        "usage_percent": 80
    }
}

# --- Unit Tests for Core Logic (process_resource_report) ---

def test_process_resource_report_valid_input():
    """Tests successful processing of a valid report."""
    result = process_resource_report(MOCK_VALID_REPORT)
    
    assert isinstance(result, dict)
    assert result["processing_status"] == "SUCCESS"
    assert result["metrics_processed"]["disk_usage_percent"] == 80
    assert result["actionable_insight"] == "The system is operating at 80% disk capacity. This is exactly the 80% threshold, **immediate action is required**."

def test_process_resource_report_low_usage_insight():
    """Tests the insight generation for low usage."""
    result = process_resource_report(MOCK_LOW_USAGE_REPORT)
    
    assert isinstance(result, dict)
    assert result["metrics_processed"]["disk_usage_percent"] == 10
    assert "well below the 80% threshold, indicating no immediate action is required" in result["actionable_insight"]

def test_process_resource_report_missing_top_level_key():
    """Tests error handling for missing top-level keys."""
    result = process_resource_report(MOCK_INVALID_REPORT_MISSING_KEY)
    
    assert isinstance(result, dict)
    assert "error" in result
    assert "missing required top-level keys" in result["error"]

# --- Integration Test for MQ Listener (Requires setup_test_environment fixture) ---

def test_mq_listener_integration(setup_test_environment):
    """
    Tests the full MQ publish/subscribe/consume cycle.
    This test relies on the setup_test_environment fixture for cleanup.
    """
    mq_new_dir = os.environ.get("MQ_NEW_DIR")
    mq_archive_dir = os.environ.get("MQ_ARCHIVE_DIR")
    output_file = os.environ.get("CT_OUTPUT_FILE")
    
    # 1. Simulate a publish (write a mock message to the 'new' queue)
    test_file_name = "test_message_12345.json"
    test_file_path = os.path.join(mq_new_dir, test_file_name)
    
    with open(test_file_path, 'w') as f:
        json.dump(MOCK_VALID_REPORT, f, indent=2)
        
    # 2. Run the listener (should consume the message)
    start_mq_listener()
    
    # 3. Assertions
    
    # A. Check if the message was consumed (moved to archive)
    assert not os.path.exists(test_file_path)
    assert os.path.exists(os.path.join(mq_archive_dir, test_file_name))
    
    # B. Check if the output file was created and contains the correct data
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        output_data = json.load(f)
        
    assert output_data["processing_status"] == "SUCCESS"
    assert output_data["metrics_processed"]["disk_usage_percent"] == 80
    
    # C. Check if the health check file was updated (implicitly checked by conftest setup)
    # The health check file is updated by the listener, confirming the end-to-end flow.
    
    # 4. Clean up the output file for the next test run
    os.remove(output_file)
