import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
import json

from fastapi import FastAPI, Request, HTTPException, Header, status
import jwt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GitHub App Preview URL Service")

# Environmental variables
load_dotenv() # loads .env into environment variables
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_APP_PRIVATE_KEY = os.getenv("GITHUB_APP_PRIVATE_KEY")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# Validate required environment variables
if not all([GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_WEBHOOK_SECRET]):
    logger.warning("Missing required environment variables. Some features may not work.")


def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256.
    
    Reference docs: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    

    # copy implementation from reference docs above later
    pass

def generate_jwt_token() -> str:
    """
    Generate a JWT token for GitHub App authentication.
    
    Returns:
        JWT token string
    """
    if not GITHUB_APP_ID or not GITHUB_APP_PRIVATE_KEY:
        raise ValueError("GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY must be set")

    now = int(datetime.now().timestamp())
    payload = {
        "iat": now - 60,  # Issued at time (1 minute ago to account for clock skew)
        "exp": now + (10 * 60),  # Expires in 10 minutes
        "iss": GITHUB_APP_ID  # Issuer is the App ID
    }

    token = jwt.encode(payload, GITHUB_APP_PRIVATE_KEY, algorithm="RS256")
    return token

def extract_command(comment_body: str) -> Optional[dict]:
    """
    Extract /preview command

    Args:
        comment_body: the comment text

    Returns:
        Dict with command info if /preview found, None otherwise
    """
    if not comment_body:
        return None 

    lines = comment_body.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('/preview'):
            parts = line.split()
            command = {
                'command': 'preview',
                'raw': line
            }

            return command
    
    return None

@app.post("/webhook")
async def github_webhook(
    request: Request,
    github_event: str = Header(None), 
    x_hub_signature_256: str = Header(None)):
    body_bytes = await request.body()
    if not verify_webhook_signature(body_bytes, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )    
    
    logger.info(f"Received GitHub event: {github_event}")

    if github_event != "issue_comment":
        logger.debug(f"Ignoring event type:{github_event}")
        return JSONResponse(
            status_code=200,
            content={"message": f"Event type {github_event} ignored"}
        )

    # Extract event data
    action = payload.get("action")
    comment = payload.get("comment", {})
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})
    installation = payload.get("installation", {})

    if action != "created":
        logger.debug(f"Ignoring action: {action}")
        return JSONResponse(
            status_code=200,
            content={"message": f"Action {action} ignored"}
        )

    if "pull_request" not in issue.get("html_url", ""):
        logger.debug("Comment is not on a PR, ignoring")
        return JSONResponse(
            status_code=200,
            content={"message": "Comment is not on a PR"}
        )

    # Extract PR number
    pr_number = issue.get("number")
    if not pr_number:
        logger.warning("Could not extract PR number from issue")
        return JSONResponse(
            status_code=200,
            content={"message": "Could not extract PR number"}
        )

    # Extract repository information
    repo_owner = repository.get("owner", {}).get("login")
    repo_name = repository.get("name")
    installation_id = installation.get("id")
    
    if not all([repo_owner, repo_name, installation_id]):
        logger.warning("Missing required repository or installation info")
        return JSONResponse(
            status_code=200,
            content={"message": "Missing repository or installation info"}
        )
    
    # Extract comment body and check for /preview command
    comment_body = comment.get("body", "")
    preview_command = extract_command(comment_body)
    
    if not preview_command:
        logger.debug("No /preview command found in comment")
        return JSONResponse(
            status_code=200,
            content={"message": "No /preview command found"}
        )

    logger.info(f"Processing /preview command for PR #{pr_number} in {repo_owner}/{repo_name}")

    return {"message": "webhook received"}

@app.get("/")
async def root():
    return {"status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

