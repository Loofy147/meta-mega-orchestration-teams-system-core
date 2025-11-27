import subprocess
import json
from datetime import datetime
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.load_env import load_env
import redis

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

def get_cpu_usage():
    """
    Executes 'top -bn1' and parses the output to extract CPU usage metrics.
    """
    try:
        # Execute top -bn1 and capture output
        result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        # The line starting with '%Cpu(s)' contains the data
        cpu_line = [line for line in lines if line.startswith('%Cpu(s)')][0]
        
        # Example: %Cpu(s):  0.0 us,  0.0 sy,  0.0 ni, 99.9 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
        # We want the 'id' (idle) value to calculate usage (100 - idle)
        idle_str = cpu_line.split(',')[3].strip().split(' ')[0]
        idle_percent = float(idle_str)
        usage_percent = round(100.0 - idle_percent, 1)
        
        return {"cpu_usage_percent": usage_percent}

    except Exception as e:
        print(f"Error collecting CPU usage: {e}")
        return None

def get_memory_usage():
    """
    Executes 'free -m' and parses the output to extract memory usage metrics in MB.
    """
    try:
        # Execute free -m and capture output
        result = subprocess.run(['free', '-m'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        # The second line contains the memory data (Mem:)
        mem_line = lines[1].split()
        
        total_mb = int(mem_line[1])
        used_mb = int(mem_line[2])
        free_mb = int(mem_line[3])
        
        usage_percent = round((used_mb / total_mb) * 100.0, 1) if total_mb > 0 else 0.0
        
        return {
            "mem_total_mb": total_mb,
            "mem_used_mb": used_mb,
            "mem_usage_percent": usage_percent
        }

    except Exception as e:
        print(f"Error collecting Memory usage: {e}")
        return None

def get_disk_usage():
    """
    Executes 'df -h /' and parses the output to extract disk usage metrics.
    """
    try:
        # Execute df -h / and capture output
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        # The second line contains the data
        if len(lines) < 2:
            raise ValueError("df output is shorter than expected.")
            
        # Split the data line by whitespace
        data_line = lines[1].split()
        
        # Extract raw values
        size_str = data_line[1]
        used_str = data_line[2]
        avail_str = data_line[3]
        use_percent_str = data_line[4].replace('%', '')
        
        # Helper to convert human-readable size (e.g., 40G, 8.2G) to float in GB
        def parse_size_to_gb(size_h):
            size_h = size_h.upper()
            if size_h.endswith('G'):
                return float(size_h.replace('G', ''))
            elif size_h.endswith('T'):
                return float(size_h.replace('T', '')) * 1024
            # Assume MB or less, convert to GB (rough estimate for sandbox)
            elif size_h.endswith('M'):
                return float(size_h.replace('M', '')) / 1024
            return float(size_h) / (1024**3) # Assume bytes if no unit
            
        # Format the data according to the Artifact Contract
        metrics = {
            "disk_filesystem": data_line[0],
            "disk_size_gb": round(parse_size_to_gb(size_str), 1),
            "disk_used_gb": round(parse_size_to_gb(used_str), 1),
            "disk_available_gb": round(parse_size_to_gb(avail_str), 1),
            "disk_usage_percent": int(use_percent_str)
        }
        
        return metrics

    except subprocess.CalledProcessError as e:
        print(f"Error executing 'df': {e}")
        return None
    except Exception as e:
        print(f"Error parsing 'df' output: {e}")
        return None

def validate_metrics(metrics):
    """
    DT-003: Implements data validation and quality checks.
    Returns True if valid, False otherwise.
    """
    # Disk Usage Check
    disk_percent = metrics.get("disk_usage_percent")
    if disk_percent is not None and not (0 <= disk_percent <= 100):
        print(f"Validation Error: Disk usage percent ({disk_percent}) is out of range.")
        return False

    # CPU Usage Check
    cpu_percent = metrics.get("cpu_usage_percent")
    if cpu_percent is not None and not (0.0 <= cpu_percent <= 100.0):
        print(f"Validation Error: CPU usage percent ({cpu_percent}) is out of range.")
        return False

    # Memory Usage Check
    mem_percent = metrics.get("mem_usage_percent")
    if mem_percent is not None and not (0.0 <= mem_percent <= 100.0):
        print(f"Validation Error: Memory usage percent ({mem_percent}) is out of range.")
        return False
        
    # Check for non-zero total size (basic sanity check)
    if metrics.get("disk_size_gb", 0) <= 0 or metrics.get("mem_total_mb", 0) <= 0:
        print("Validation Error: Total resource size is zero or negative.")
        return False

    return True

def generate_report():
    """
    Generates the final JSON report as per the Artifact Contract,
    now including CPU and Memory metrics (DT-002).
    """
    disk_metrics = get_disk_usage()
    cpu_metrics = get_cpu_usage()
    mem_metrics = get_memory_usage()
    
    # Combine all metrics
    all_metrics = {}
    if disk_metrics:
        all_metrics.update(disk_metrics)
    if cpu_metrics:
        all_metrics.update(cpu_metrics)
    if mem_metrics:
        all_metrics.update(mem_metrics)
        
    # DT-003: Perform Data Validation
    if not validate_metrics(all_metrics):
        return {
            "timestamp": datetime.now().isoformat(),
            "team_id": "Data Team",
            "status": "VALIDATION_ERROR",
            "message": "Collected metrics failed data quality checks (DT-003)."
        }
        
    # Check for critical failure (if no metrics were collected)
    if not all_metrics:
        return {
            "timestamp": datetime.now().isoformat(),
            "team_id": "Data Team",
            "status": "ERROR",
            "message": "Failed to collect any resource metrics (Disk, CPU, or Memory)."
        }

    report = {
        "timestamp": datetime.now().isoformat(),
        "team_id": "Data Team",
        "resource_type": "System Resources",
        "metrics": all_metrics
    }
    
    return report

def publish_to_file_system(report_data):
    """
    Fallback: Publishes the report to the file system MQ.
    """
    mq_dir = os.environ.get("MQ_NEW_DIR")
    if not mq_dir:
        print("Error: MQ_NEW_DIR environment variable not set. Cannot publish to file system.")
        return

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    output_path = os.path.join(mq_dir, f"resource_report_{timestamp}.json")
    
    # Ensure atomic write: write to a temp file first, then rename
    temp_path = output_path + ".tmp"
    with open(temp_path, 'w') as f:
        json.dump(report_data, f, indent=2)
        
    os.rename(temp_path, output_path)
        
    print(f"Data Team (DT-001) published message to File System MQ: {output_path}")

def publish_to_redis(report_data):
    """
    Primary: Publishes the report to the Redis Stream MQ.
    """
    if not REDIS_AVAILABLE:
        print("Warning: Redis not available. Cannot publish to Redis Stream.")
        return False

    stream_name = os.environ.get("REDIS_STREAM_NAME")
    if not stream_name:
        print("Error: REDIS_STREAM_NAME environment variable not set. Cannot publish to Redis.")
        return False

    try:
        # Publish the report data as a JSON string
        message_id = REDIS_CLIENT.xadd(
            stream_name,
            {'data': json.dumps(report_data)},
            maxlen=1000, # Keep stream size manageable
            approximate=True
        )
        print(f"Data Team (DT-001) published message to Redis Stream: {stream_name} with ID {message_id}")
        return True
    except Exception as e:
        print(f"CRITICAL ERROR publishing to Redis Stream: {e}")
        return False

def generate_report_and_publish():
    """
    Entry point for the Data Team's resource reporter.
    Generates the report and publishes it to the MQ using Redis-first logic.
    """
    final_report = generate_report()
    
    # Check if the report is an error structure
    if final_report.get("status") in ["ERROR", "VALIDATION_ERROR"]:
        print(f"Data Team (DT-001) failed to generate a valid report: {final_report.get('message')}")
        return

    mq_type = os.environ.get("MQ_TYPE", "FILE_SYSTEM")
    
    if mq_type == "REDIS_STREAMS":
        if publish_to_redis(final_report):
            return
        else:
            print("CRITICAL: Redis publish failed. Falling back to File System MQ.")
            publish_to_file_system(final_report)
            
    else: # Default to FILE_SYSTEM
        publish_to_file_system(final_report)

if __name__ == "__main__":
    generate_report_and_publish()
