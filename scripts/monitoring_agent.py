import json
import os
from datetime import datetime, timedelta
import time

# Define the paths based on the .env file (assuming it's loaded or paths are known)
HEALTH_CHECK_FILE = "parallel_orchestration/health_check.json"
LOG_FILE = "parallel_orchestration/code_team_ct002_report_mq.json"

def check_health_status():
    """
    Simulates checking the AT-003 Health Check File.
    """
    print("\n--- Centralized Monitoring Agent: Health Check ---")
    try:
        with open(HEALTH_CHECK_FILE, 'r') as f:
            health_data = json.load(f)
            
        status = health_data.get("status", "UNKNOWN")
        last_time_str = health_data.get("last_processed_time")
        
        if status != "HEALTHY":
            print(f"ALERT: Service is reporting status: {status}")
            return
            
        last_processed_time = datetime.fromisoformat(last_time_str)
        time_since_last_process = datetime.now() - last_processed_time
        
        # Define a threshold for "stale" data (e.g., 5 minutes)
        if time_since_last_process > timedelta(minutes=5):
            print(f"WARNING: Service is HEALTHY but data is stale. Last processed {time_since_last_process} ago.")
        else:
            print(f"OK: Service is HEALTHY and last processed {time_since_last_process.seconds} seconds ago.")
            
    except FileNotFoundError:
        print(f"CRITICAL: Health Check file not found at {HEALTH_CHECK_FILE}. Service may be down.")
    except Exception as e:
        print(f"ERROR: Could not parse Health Check file: {e}")

def analyze_latest_log():
    """
    Simulates analyzing the latest Structured Log (CR-003) for actionable insights.
    """
    print("\n--- Centralized Monitoring Agent: Log Analysis ---")
    try:
        with open(LOG_FILE, 'r') as f:
            log_data = json.load(f)
            
        insight = log_data.get("actionable_insight", "No insight found.")
        
        if "CRITICAL" in insight:
            print(f"CRITICAL ALERT: {insight}")
        elif "WARNING" in insight:
            print(f"WARNING ALERT: {insight}")
        else:
            print(f"INFO: Latest log shows acceptable status: {insight}")
            
    except FileNotFoundError:
        print(f"INFO: Log file not found at {LOG_FILE}. Waiting for first run.")
    except Exception as e:
        print(f"ERROR: Could not parse Structured Log file: {e}")

if __name__ == "__main__":
    print("Starting Simulated Centralized Monitoring Agent...")
    check_health_status()
    analyze_latest_log()
    print("Monitoring check complete.")
