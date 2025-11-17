import subprocess
import json
from datetime import datetime
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.load_env import load_env

# Load environment variables (AT-002)
load_env(os.path.join(os.path.dirname(__file__), '..', '.env'))

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
            "filesystem": data_line[0],
            "size_gb": round(parse_size_to_gb(size_str), 1),
            "used_gb": round(parse_size_to_gb(used_str), 1),
            "available_gb": round(parse_size_to_gb(avail_str), 1),
            "usage_percent": int(use_percent_str)
        }
        
        return metrics

    except subprocess.CalledProcessError as e:
        print(f"Error executing 'df': {e}")
        return None
    except Exception as e:
        print(f"Error parsing 'df' output: {e}")
        return None

def generate_report():
    """
    Generates the final JSON report as per the Artifact Contract.
    """
    metrics = get_disk_usage()
    
    if metrics is None:
        # Return an error structure if data collection failed
        return {
            "timestamp": datetime.now().isoformat(),
            "team_id": "Data Team",
            "status": "ERROR",
            "message": "Failed to collect disk usage metrics."
        }

    report = {
        "timestamp": datetime.now().isoformat(),
        "team_id": "Data Team",
        "resource_type": "Disk Usage",
        "metrics": metrics
    }
    
    return report

if __name__ == "__main__":
    final_report = generate_report()
    
    # AT-001 Implementation: Publish to MQ (now using AT-002 config)
    mq_dir = os.environ.get("MQ_NEW_DIR")
    if not mq_dir:
        print("Error: MQ_NEW_DIR environment variable not set. Cannot publish.")
        exit(1)
        
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    output_path = os.path.join(mq_dir, f"disk_usage_{timestamp}.json")
    
    # Ensure atomic write: write to a temp file first, then rename
    temp_path = output_path + ".tmp"
    with open(temp_path, 'w') as f:
        json.dump(final_report, f, indent=2)
        
    os.rename(temp_path, output_path)
        
    print(f"Data Team (DT-001) published message to MQ: {output_path}")
