"""Client-side shim for invoking the server lead manager via HTTP API."""

from __future__ import annotations

import os
from typing import List, Optional

import requests


class AgentClient:
    """Client for communicating with remote Napari agent API server."""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Initialize the client.
        
        Args:
            api_url: Base URL of the API server. If None, reads from 
                    AIMINO_API_URL environment variable or defaults to 
                    http://localhost:8000
            session_id: Optional existing session ID to reuse for memory.
        """
        self.api_url = api_url or os.getenv(
            "AIMINO_API_URL", 
            "http://localhost:8000"
        ).rstrip("/")
        self.session_id: Optional[str] = session_id
    
    def invoke(self, user_input: str, context: Optional[dict] = None) -> List[dict]:
        """
        Invoke the remote agent with user input.
        
        Args:
            user_input: The user's natural language command
            context: Optional context dictionary to pass to the agent
            
        Returns:
            List of command dictionaries to execute
            
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.api_url}/invoke"
        payload = {
            "user_input": user_input,
        }
        if self.session_id:
            payload["session_id"] = self.session_id
        if context:
            payload["context"] = context
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            # Track session ID for future calls (enables memory).
            session_id = result.get("session_id")
            if isinstance(session_id, str) and session_id.strip():
                self.session_id = session_id.strip()
            return result.get("final_commands", [])
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Unable to connect to API server {self.api_url}. "
                f"Please ensure the server is running."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"API request timeout. Server {self.api_url} took too long to respond."
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"API request failed: {e.response.status_code} - {e.response.text}"
            )
