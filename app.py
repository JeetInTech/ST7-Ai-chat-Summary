from flask import Flask, redirect
import subprocess
import os
import time

app = Flask(__name__)

def is_streamlit_running():
    """Check if Streamlit is already running on port 8501"""
    try:
        # Try to create a connection to the port
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 8501))
        s.close()
        return True
    except ConnectionRefusedError:
        return False

@app.route('/')
def run_streamlit():
    try:
        if not is_streamlit_running():
            # Start Streamlit in headless mode to prevent browser auto-open
            subprocess.Popen([
                'streamlit',
                'run',
                'chat.py',
                '--server.port=8501',
                '--server.headless', 'true',
                '--browser.serverAddress', '0.0.0.0'
            ])
            
            # Wait until Streamlit is ready (up to 10 seconds)
            max_retries = 10
            for _ in range(max_retries):
                if is_streamlit_running():
                    break
                time.sleep(1)
            else:
                return "Streamlit failed to start within 10 seconds"

        # Redirect to Streamlit URL
        return redirect("http://localhost:8501")
    except Exception as e:
        return f"Error starting Streamlit: {str(e)}"

if __name__ == '__main__':
    # Ensure chat.py exists
    if not os.path.exists("chat.py"):
        print("Error: chat.py not found in the current directory")
        exit(1)
    
    # Start Flask app without debug mode to prevent auto-reloader issues
    app.run(host='0.0.0.0', port=5000, debug=False)