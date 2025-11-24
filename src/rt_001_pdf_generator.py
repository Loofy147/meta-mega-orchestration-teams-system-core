import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.load_env import load_env

# Load environment variables
load_env(os.path.join(os.path.dirname(__file__), '..', '.env'))

def generate_pdf_report():
    """
    RT-001: Consumes the Features Team's Markdown summary and converts it to a PDF.
    """
    # Input and Output paths from .env
    markdown_input_path = os.environ.get("FT_OUTPUT_FILE")
    pdf_output_path = "parallel_orchestration/executive_summary.pdf"
    
    if not markdown_input_path:
        print("Error: FT_OUTPUT_FILE environment variable not set.")
        return

    if not os.path.exists(markdown_input_path):
        print(f"Error: Features Team output file not found at {markdown_input_path}. Cannot generate PDF.")
        return

    print(f"Reporting Team (RT-001) converting {markdown_input_path} to PDF...")
    
    # Use the pre-installed utility to convert Markdown to PDF
    try:
        command = f"manus-md-to-pdf {markdown_input_path} {pdf_output_path}"
        # Execute the command using the shell tool
        os.system(command)
        
        if os.path.exists(pdf_output_path):
            print(f"Reporting Team (RT-001) successfully generated PDF report to {pdf_output_path}")
        else:
            print(f"Error: PDF file was not created at {pdf_output_path}. Check manus-md-to-pdf utility.")
            
    except Exception as e:
        print(f"CRITICAL ERROR during PDF generation: {e}")

if __name__ == "__main__":
    generate_pdf_report()
