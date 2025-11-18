import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.load_env import load_env
from datetime import datetime

# Load environment variables (AT-002)
load_env(os.path.join(os.path.dirname(__file__), '..', '.env'))

def update_health_check(last_processed_data):
    """
    AT-003: Updates the centralized health check file upon successful processing.
    """
    health_file = os.environ.get("AT_HEALTH_CHECK_FILE")
    if not health_file:
        return

    health_data = {
        "service": "Code Team Processor (CT-002)",
        "status": "HEALTHY",
        "last_processed_time": datetime.now().isoformat(),
        "last_processed_event": last_processed_data.get("event_type", "N/A"),
        "last_processed_source_time": last_processed_data.get("source_timestamp", "N/A")
    }
    
    try:
        with open(health_file, 'w') as f:
            json.dump(health_data, f, indent=2)
        print(f"Code Team (CT-002) updated health check file: {health_file}")
    except Exception as e:
        print(f"Error updating health check file: {e}")

def process_resource_report(report_data):
    """
    Code Team Task CT-002: Processes the Data Team's JSON report (as a dictionary).
    
    Processing involves:
    1. Validating the presence of key metrics.
    2. Generating a human-readable summary.
    """
    
    # --- Validation and Processing ---

    # Check for required keys as per Artifact Contract
    required_keys = ["team_id", "resource_type", "metrics"]
    if not all(key in report_data for key in required_keys):
        return {"error": "JSON structure is missing required top-level keys."}

    metrics = report_data.get("metrics", {})
    
    # Check for required metrics keys
    required_metrics = ["usage_percent", "size_gb", "used_gb"]
    if not all(key in metrics for key in required_metrics):
        return {"error": "JSON metrics object is missing required keys."}

    # CR-003: Formalize Output as a Structured Log Event (JSON)
    output_data = {
        "event_type": "RESOURCE_ANALYSIS_COMPLETED",
        "source_team": report_data['team_id'],
        "source_timestamp": report_data.get('timestamp', 'N/A'),
        "processing_status": "SUCCESS",
        "resource_type": report_data['resource_type'],
        "metrics_processed": {
            "disk_usage_percent": metrics['usage_percent'],
            "total_size_gb": metrics['size_gb'],
            "used_space_gb": metrics['used_gb']
        },
        "actionable_insight": (
            f"The system is operating at {metrics['usage_percent']}% disk capacity. This is exactly the 80% threshold, **immediate action is required**."
            if metrics['usage_percent'] >= 80 else
            f"The system is operating at {metrics['usage_percent']}% disk capacity. This is well below the 80% threshold, indicating no immediate action is required."
        )
    }
    return output_data

def start_mq_listener():
    """
    CR-001: Handles the MQ subscription logic.
    """
    # CR-002: Configuration-Driven Paths (Preparation for AT-002)
    mq_new_dir = os.environ.get("MQ_NEW_DIR")
    mq_archive_dir = os.environ.get("MQ_ARCHIVE_DIR")
    
    if not mq_new_dir or not mq_archive_dir:
        print("Error: MQ_NEW_DIR or MQ_ARCHIVE_DIR environment variables not set. Cannot start listener.")
        return
    
    # Check for health check file path
    health_file = os.environ.get("AT_HEALTH_CHECK_FILE")
    if not health_file:
        print("Warning: AT_HEALTH_CHECK_FILE environment variable not set. Health check will be skipped.")
    
    # 1. Find the latest message (file) in the 'new' queue
    try:
        messages = [f for f in os.listdir(mq_new_dir) if f.endswith('.json')]
        if not messages:
            print("Code Team (CT-002) Subscriber: No new messages in queue.")
            return
            
        # Sort by name (which includes timestamp) to get the latest
        latest_message_file = sorted(messages)[-1]
        input_file_path = os.path.join(mq_new_dir, latest_message_file)
        
    except Exception as e:
        print(f"Code Team (CT-002) Subscriber Error: Could not read MQ directory. {e}")
        return

    # 2. Read and parse the message
    try:
        with open(input_file_path, 'r') as f:
            report_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Data Team artifact at {input_file_path} is not valid JSON. Archiving corrupted message.")
        # Archive corrupted message to prevent reprocessing
        os.rename(input_file_path, os.path.join(mq_archive_dir, latest_message_file + ".corrupted"))
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # 3. Process the message (passing the dictionary)
    processing_result_dict = process_resource_report(report_data)
    
    # Handle potential error string returned by process_resource_report
    if isinstance(processing_result_dict, str):
        print(f"Code Team (CT-002) Processing Error: {processing_result_dict}")
        update_health_check({"event_type": "PROCESSING_ERROR", "source_timestamp": datetime.now().isoformat()})
        return

    # 4. Define the output file path for the Code Team's report
    output_file = os.environ.get("CT_OUTPUT_FILE")
    if not output_file:
        print("Error: CT_OUTPUT_FILE environment variable not set. Cannot write report.")
        return
    
    with open(output_file, 'w') as f:
        json.dump(processing_result_dict, f, indent=2)
        
    print(f"Code Team (CT-002) processing report written to {output_file}")
    
    # 5. Consume/Archive the message (Atomic operation)
    archive_file_path = os.path.join(mq_archive_dir, latest_message_file)
    os.rename(input_file_path, archive_file_path)
    print(f"Code Team (CT-002) consumed and archived message: {latest_message_file}")
    
    # 6. AT-003: Update Health Check File
    update_health_check(processing_result_dict)
    
    # 6. AT-003: Update Health Check File
    update_health_check(processing_result_dict)

if __name__ == "__main__":
    start_mq_listener()
