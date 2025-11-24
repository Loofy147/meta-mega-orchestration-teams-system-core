import os
import json
from datetime import datetime

# Define the critical security variable to check
SECRET_VAR_NAME = "CRITICAL_SECRET_KEY"
ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
AUDIT_REPORT_PATH = "parallel_orchestration/security_audit_report.json"

def run_security_audit():
    """
    ST-001: Runs a security audit on the configuration file.
    Checks for the presence and non-empty value of a critical secret key.
    """
    audit_result = {
        "audit_time": datetime.now().isoformat(),
        "team": "Security Team (ST-001)",
        "check": f"Presence and value of {SECRET_VAR_NAME} in .env",
        "status": "FAIL",
        "message": f"CRITICAL: {SECRET_VAR_NAME} is missing or empty in .env file."
    }

    try:
        with open(ENV_FILE_PATH, 'r') as f:
            env_content = f.read()
            
        # Simple check for presence and non-empty value
        if f"{SECRET_VAR_NAME}=" in env_content:
            # Check if it has a value after the equals sign
            line = next((line for line in env_content.splitlines() if line.startswith(f"{SECRET_VAR_NAME}=")), None)
            if line and len(line.split('=', 1)[1].strip()) > 0:
                audit_result["status"] = "PASS"
                audit_result["message"] = f"PASS: {SECRET_VAR_NAME} is present and has a non-empty value."
            
    except FileNotFoundError:
        audit_result["message"] = f"CRITICAL: .env file not found at {ENV_FILE_PATH}."
    except Exception as e:
        audit_result["message"] = f"ERROR during audit: {e}"

    # Write the audit report
    with open(AUDIT_REPORT_PATH, 'w') as f:
        json.dump(audit_result, f, indent=2)
        
    print(f"Security Team (ST-001) audit complete. Report written to {AUDIT_REPORT_PATH}")
    return audit_result

if __name__ == "__main__":
    run_security_audit()
