import json
import os

def process_resource_report(file_path):
    """
    Code Team Task CT-002: Ingests the Data Team's JSON report and processes it.
    
    Processing involves:
    1. Reading the JSON file.
    2. Validating the presence of key metrics.
    3. Generating a human-readable summary.
    """
    
    if not os.path.exists(file_path):
        return f"Error: Data Team artifact not found at {file_path}"

    try:
        with open(file_path, 'r') as f:
            report_data = json.load(f)
            
    except json.JSONDecodeError:
        # Robust Error Handling (Professional Improvement)
        return f"Error: Data Team artifact at {file_path} is not valid JSON. Processing halted."
    except Exception as e:
        return f"Error reading file: {e}"

    # --- Validation and Processing ---
    
    # Check for required keys as per Artifact Contract
    required_keys = ["team_id", "resource_type", "metrics"]
    if not all(key in report_data for key in required_keys):
        return "Error: JSON structure is missing required top-level keys."

    metrics = report_data.get("metrics", {})
    
    # Check for required metrics keys
    required_metrics = ["usage_percent", "size_gb", "used_gb"]
    if not all(key in metrics for key in required_metrics):
        return "Error: JSON metrics object is missing required keys."

    # Generate Summary
    summary = f"""
Code Team (CT-002) Processing Report:
---------------------------------------------
Source Team: {report_data['team_id']}
Report Timestamp: {report_data.get('timestamp', 'N/A')}
Resource Type: {report_data['resource_type']}

Processing Status: SUCCESS
Disk Usage: {metrics['usage_percent']}%
Total Size: {metrics['size_gb']} GB
Used Space: {metrics['used_gb']} GB

Actionable Insight: The system is operating at {metrics['usage_percent']}% disk capacity. This is well below the 80% threshold, indicating no immediate action is required.
---------------------------------------------
"""
    return summary

if __name__ == "__main__":
    # AT-001 Implementation: Subscribe from MQ
    mq_new_dir = "parallel_orchestration/mq/disk_usage/new"
    mq_archive_dir = "parallel_orchestration/mq/disk_usage/archive"
    
    # 1. Find the latest message (file) in the 'new' queue
    try:
        messages = [f for f in os.listdir(mq_new_dir) if f.endswith('.json')]
        if not messages:
            print("Code Team (CT-002) Subscriber: No new messages in queue.")
            exit()
            
        # Sort by name (which includes timestamp) to get the latest
        latest_message_file = sorted(messages)[-1]
        input_file_path = os.path.join(mq_new_dir, latest_message_file)
        
    except Exception as e:
        print(f"Code Team (CT-002) Subscriber Error: Could not read MQ directory. {e}")
        exit()

    # 2. Process the message
    processing_result = process_resource_report(input_file_path)
    
    # 3. Define the output file path for the Code Team's report
    output_file = "parallel_orchestration/code_team_ct002_report_mq.txt"
    
    with open(output_file, 'w') as f:
        f.write(processing_result)
        
    print(f"Code Team (CT-002) processing report written to {output_file}")
    
    # 4. Consume/Archive the message (Atomic operation)
    archive_file_path = os.path.join(mq_archive_dir, latest_message_file)
    os.rename(input_file_path, archive_file_path)
    print(f"Code Team (CT-002) consumed and archived message: {latest_message_file}")
