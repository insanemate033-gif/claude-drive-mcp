import os
import json
from mcp.server.fastmcp import FastMCP
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- 1. INITIALIZE FastMCP ---
# Render assigns a dynamic port. We read it here and bind to 0.0.0.0
port = int(os.environ.get("PORT", "8000"))
mcp = FastMCP("Claude-Drive-Server", host="0.0.0.0", port=port)

# --- 2. GOOGLE DRIVE AUTHENTICATION ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# If running on the cloud, use the secret environment variable
if "GOOGLE_CREDENTIALS_JSON" in os.environ:
    creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
# If running locally on your Mac, use the downloaded file
else:
    SERVICE_ACCOUNT_FILE = 'claude-drive-acceess-d156124aa2ba.json'
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=creds)


# --- 3. CLAUDE'S TOOLS ---
@mcp.tool()
def list_files() -> str:
    """List the files available in the shared Google Drive folder."""
    try:
        results = drive_service.files().list(pageSize=10, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        if not items:
            return "No files found in the shared folder."
            
        file_list = "\n".join([f"- {item['name']} (ID: {item['id']})" for item in items])
        return f"Here are the files:\n{file_list}"
    except Exception as e:
        return f"Error listing files: {str(e)}"

@mcp.tool()
def read_file(file_id: str) -> str:
    """Read the text content of a Google Doc using its file_id."""
    try:
        content = drive_service.files().export(fileId=file_id, mimeType='text/plain').execute()
        return content.decode('utf-8')
    except Exception as e:
        return f"Error reading file (Ensure it is a Google Doc): {str(e)}"


# --- 4. RUN THE SERVER ---
if __name__ == "__main__":
    # Now it just runs the server without the extra arguments!
    mcp.run(transport='sse')