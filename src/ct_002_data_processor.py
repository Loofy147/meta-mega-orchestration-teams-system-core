import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.load_env import load_env
from datetime import datetime
import redis
import time

# Load environment variables (AT-002)
load_env(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize Redis client (will fail if Redis is not running, but we handle that)
try:
    REDIS_CLIENT = redis.Redis(
        host=os.environ.get("REDIS_HOST"),
        port=int(os.environ.get("REDIS_PORT")),
        decode_responses=True
    )
    REDIS_CLIENT.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

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
    
    # Check for required metrics keys (Updated for DT-002)
    required_metrics = ["disk_usage_percent", "cpu_usage_percent", "mem_usage_percent"]
    if not all(key in metrics for key in required_metrics):
        return {"error": f"JSON metrics object is missing required keys. Expected: {required_metrics}. Found: {list(metrics.keys())}"}

    # CR-003: Formalize Output as a Structured Log Event (JSON)
    
    # --- Actionable Insight Logic (Updated for DT-002) ---
    disk_percent = metrics['disk_usage_percent']
    cpu_percent = metrics['cpu_usage_percent']
    mem_percent = metrics['mem_usage_percent']
    
    insight = f"System status: Disk {disk_percent}%, CPU {cpu_percent}%, Mem {mem_percent}%. "
    
    if disk_percent >= 80:
        insight += "CRITICAL: Disk usage is at or above 80% threshold. Immediate action required."
    elif cpu_percent >= 90:
        insight += "WARNING: CPU usage is at or above 90% threshold. Investigate process load."
    elif mem_percent >= 90:
        insight += "WARNING: Memory usage is at or above 90% threshold. Investigate memory leaks."
    else:
        insight += "OK: All primary resource metrics are within acceptable limits."
        
    output_data = {
        "event_type": "RESOURCE_ANALYSIS_COMPLETED",
        "source_team": report_data['team_id'],
        "source_timestamp": report_data.get('timestamp', 'N/A'),
        "processing_status": "SUCCESS",
        "resource_type": report_data['resource_type'],
        "metrics_processed": metrics, # Use all metrics from the Data Team
        "actionable_insight": insight
    }
    return output_data

def consume_from_file_system():
    """
    Fallback: Consumes the latest message from the file system MQ.
    """
    mq_new_dir = os.environ.get("MQ_NEW_DIR")
    mq_archive_dir = os.environ.get("MQ_ARCHIVE_DIR")
    
    if not mq_new_dir or not mq_archive_dir:
        print("Error: MQ_NEW_DIR or MQ_ARCHIVE_DIR environment variables not set. Cannot start file system listener.")
        return None, None, None
    
    # 1. Find the latest message (file) in the 'new' queue
    try:
        messages = [f for f in os.listdir(mq_new_dir) if f.endswith('.json')]
        if not messages:
            return None, None, None
            
        # Sort by name (which includes timestamp) to get the latest
        latest_message_file = sorted(messages)[-1]
        input_file_path = os.path.join(mq_new_dir, latest_message_file)
        
    except Exception as e:
        print(f"Code Team (CT-002) Subscriber Error: Could not read MQ directory. {e}")
        return None, None, None

    # 2. Read and parse the message
    try:
        with open(input_file_path, 'r') as f:
            report_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Data Team artifact at {input_file_path} is not valid JSON. Archiving corrupted message.")
        # Archive corrupted message to prevent reprocessing
        os.rename(input_file_path, os.path.join(mq_archive_dir, latest_message_file + ".corrupted"))
        return None, None, None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None, None, None
        
    # Return data and consumption function
    def consume_file():
        archive_file_path = os.path.join(mq_archive_dir, latest_message_file)
        os.rename(input_file_path, archive_file_path)
        print(f"Code Team (CT-002) consumed and archived message: {latest_message_file}")
        
    return report_data, consume_file, latest_message_file

def consume_from_redis():
    """
    Primary: Consumes a message from the Redis Stream MQ.
    """
    if not REDIS_AVAILABLE:
        return None, None, None
        
    stream_name = os.environ.get("REDIS_STREAM_NAME")
    consumer_group = "ct002_group"
    consumer_name = "ct002_instance"
    
    try:
        # Ensure the consumer group exists
        try:
            REDIS_CLIENT.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
        except redis.exceptions.ResponseError as e:
            if 'BUSYGROUP' not in str(e):
                raise
                
        # Read one message from the stream
        response = REDIS_CLIENT.xreadgroup(
            consumer_group,
            consumer_name,
            {stream_name: '>'},
            count=1,
            block=1000 # Block for 1 second
        )
        
        if not response or not response[0][1]:
            return None, None, None
            
        stream_key, messages = response[0]
        message_id, message_data = messages[0]
        
        # The message data is a dictionary of bytes, convert to string/JSON
        report_data = json.loads(message_data[b'data'].decode('utf-8'))
        
        # Return data and consumption function (ACK)
        def consume_redis():
            REDIS_CLIENT.xack(stream_name, consumer_group, message_id)
            print(f"Code Team (CT-002) consumed and ACKed message: {message_id}")
            
        return report_data, consume_redis, message_id.decode('utf-8')
        
    except Exception as e:
        print(f"Code Team (CT-002) Redis Subscriber Error: {e}")
        return None, None, None

def start_mq_listener():
    """
    CR-001: Handles the MQ subscription logic with Redis fallback.
    """
    mq_type = os.environ.get("MQ_TYPE", "FILE_SYSTEM")
    
    report_data = None
    consume_func = None
    message_id = None
    
    if mq_type == "REDIS_STREAMS" and REDIS_AVAILABLE:
        print("Code Team (CT-002) Subscriber: Attempting to consume from Redis Streams...")
        report_data, consume_func, message_id = consume_from_redis()
    else:
        if mq_type == "REDIS_STREAMS":
            print("Code Team (CT-002) Subscriber: Redis Streams requested but not available. Falling back to File System MQ.")
        
        report_data, consume_func, message_id = consume_from_file_system()
        
    if not report_data:
        print("Code Team (CT-002) Subscriber: No new messages in queue.")
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
    consume_func()
    
    # 6. AT-003: Update Health Check File
    update_health_check(processing_result_dict)

if __name__ == "__main__":
    start_mq_listener()
