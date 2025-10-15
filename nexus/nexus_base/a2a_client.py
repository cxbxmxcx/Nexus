"""A2A Protocol Client using official a2a-sdk.

⭐ PRODUCTION VERSION - Create at: nexus/nexus_base/a2a_client.py
"""

import uuid
from typing import Any, Dict, Optional
import logging

try:
    import httpx
    from a2a.client import A2ACardResolver, A2AClient  
    from a2a.types import AgentCard, MessageSendParams, SendMessageRequest, SendMessageResponse
except ImportError as e:
    logging.error("Install a2a-sdk: pip install a2a-sdk>=0.2.3")
    raise


class RemoteAgentConnection:
    """Connection wrapper for a single remote A2A agent."""

    def __init__(self, agent_card: AgentCard, agent_url: str):
        self._httpx_client = httpx.AsyncClient(timeout=30.0)
        self.agent_client = A2AClient(self._httpx_client, agent_card, url=agent_url)
        self.card = agent_card
        self.url = agent_url

    async def send_message(self, message_request: SendMessageRequest) -> SendMessageResponse:
        return await self.agent_client.send_message(message_request)

    async def close(self):
        await self._httpx_client.aclose()


class NexusA2AClient:
    """Nexus wrapper for A2A client operations."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.connections: Dict[str, RemoteAgentConnection] = {}

    async def get_agent_card(self, agent_url: str) -> Optional[AgentCard]:
        """Fetch agent card from A2A endpoint."""
        if not agent_url.startswith(('http://', 'https://')):
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                card_resolver = A2ACardResolver(client, agent_url)
                return await card_resolver.get_agent_card()
        except Exception as e:
            logging.error(f"Failed to fetch agent card from {agent_url}: {e}")
            return None

    async def create_connection(self, agent_url: str) -> Optional[RemoteAgentConnection]:
        """Create connection to remote agent."""
        card = await self.get_agent_card(agent_url)
        if card:
            connection = RemoteAgentConnection(card, agent_url)
            self.connections[card.name] = connection
            return connection
        return None

    async def send_message(self, agent_name: str, message: str, context_id: str, 
                          conversation_history: str = "", task_id: Optional[str] = None,
                          message_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message to agent via A2A protocol."""

        if agent_name not in self.connections:
            return {"success": False, "error": f"Agent {agent_name} not connected", "response": None}

        if task_id is None:
            task_id = str(uuid.uuid4())
        if message_id is None:
            message_id = str(uuid.uuid4())

        # Build message
        full_message = message
        if conversation_history:
            full_message = f"=== Context ===\n{conversation_history[-2000:]}\n\n=== Task ===\n{message}"

        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": full_message}],
                "messageId": message_id,
                "taskId": task_id,
                "contextId": context_id,
            }
        }

        try:
            connection = self.connections[agent_name]
            message_request = SendMessageRequest(
                id=message_id, params=MessageSendParams.model_validate(payload)
            )

            response = await connection.send_message(message_request)
            response_text = self._extract_text_from_response(response)

            return {"success": True, "response": response_text, "raw": response}

        except Exception as e:
            return {"success": False, "error": str(e), "response": None}

    def _extract_text_from_response(self, response: SendMessageResponse) -> str:
        """Extract text content from A2A response."""
        try:
            # Handle different response formats
            if hasattr(response, "root") and hasattr(response.root, "result"):
                artifacts = getattr(response.root.result, "artifacts", []) or []
                for artifact in artifacts:
                    for part in getattr(artifact, "parts", []) or []:
                        if hasattr(part, "text") and part.text:
                            return str(part.text).strip()

            if hasattr(response, "root") and hasattr(response.root, "message"):
                parts = getattr(response.root.message, "parts", []) or []
                for part in parts:
                    if hasattr(part, "text") and part.text:
                        return str(part.text).strip()

            return "No response content received."
        except Exception as e:
            return f"Error parsing response: {str(e)}"

    async def close(self):
        """Close all connections."""
        for connection in self.connections.values():
            await connection.close()
        self.connections.clear()
