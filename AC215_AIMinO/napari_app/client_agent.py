"""Client-side shim for invoking the server lead manager via HTTP API."""

from __future__ import annotations

import os
from typing import List, Optional

import requests


class AgentClient:
    """Client for communicating with remote Napari agent API server."""
    
    def __init__(self, api_url: Optional[str] = None) -> None:
        """
        Initialize the client.
        
        Args:
            api_url: Base URL of the API server. If None, reads from 
                    AIMINO_API_URL environment variable or defaults to 
                    http://localhost:8000
        """
        self.api_url = api_url or os.getenv(
            "AIMINO_API_URL", 
            "http://localhost:8000"
        ).rstrip("/")
    
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
        if context:
            payload["context"] = context
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            print(result)
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
