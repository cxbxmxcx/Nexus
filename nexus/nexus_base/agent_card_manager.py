"""Manager for A2A Agent Cards with Enhanced Error Handling.

⭐ ENHANCED VERSION - Replace: nexus/nexus_base/agent_card_manager.py
"""

from typing import Dict, List, Optional
import logging
import asyncio

# ✅ ADDED: Import fallbacks
try:
    from a2a.types import AgentCard as A2AAgentCard
except ImportError:
    try:
        from a2a_sdk.types import AgentCard as A2AAgentCard
    except ImportError:
        raise ImportError("Install A2A SDK: pip install a2a-sdk>=0.2.3")

try:
    from nexus.nexus_base.a2a_client import NexusA2AClient
except ImportError:
    from .a2a_client import NexusA2AClient


class AgentCardInfo:
    """Wrapper for A2A Agent Card with metadata and error handling."""

    def __init__(self, a2a_card: A2AAgentCard, agent_url: str):
        self.a2a_card = a2a_card
        self.name = str(a2a_card.name) if a2a_card.name else "unnamed_agent"
        self.description = str(a2a_card.description or "No description")
        self.url = agent_url.rstrip('/')
        self.capabilities = [str(cap) for cap in (getattr(a2a_card, "capabilities", []) or [])]
        # ✅ ADDED: Default to unknown, will be updated by health check
        self.status = "unknown"  
        self.last_error = None
        self.health_check_count = 0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "capabilities": self.capabilities,
            "status": self.status,
            "last_error": self.last_error,
            "health_checks": self.health_check_count
        }

    def to_prompt_text(self) -> str:
        caps = ", ".join(self.capabilities) if self.capabilities else "general purpose"

        # ✅ ENHANCED: Better status indicators including error state
        if self.status == "active":
            status_icon = "🟢"
        elif self.status == "inactive":
            status_icon = "🔴"
        elif self.status == "error":
            status_icon = "❌"
        else:
            status_icon = "🟡"  # unknown

        status_text = f"{status_icon} **{self.name}**: {self.description}\n"
        status_text += f"   Capabilities: {caps}"

        # Add error info if present
        if self.status == "error" and self.last_error:
            status_text += f"\n   ⚠️ Last error: {str(self.last_error)[:50]}..."

        return status_text

    # ✅ ADDED: Mark agent as having an error
    def mark_error(self, error: Exception):
        """Mark agent as having an error."""
        self.status = "error"
        self.last_error = str(error)
        logging.warning(f"Agent {self.name} marked as error: {error}")


class AgentCardManager:
    """Manages agent cards for orchestration with enhanced error handling."""

    def __init__(self):
        self.agent_cards: Dict[str, AgentCardInfo] = {}
        self.agent_urls: Dict[str, str] = {}
        self.a2a_client = NexusA2AClient()
        self.health_check_in_progress = set()

    async def load_agents_from_urls(self, agent_urls: List[str]) -> Dict[str, bool]:
        """Load agent cards from URLs with enhanced error handling."""
        results = {}

        for url in agent_urls:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                results[url] = False
                logging.warning(f"Invalid URL format: {url}")
                continue

            try:
                connection = await self.a2a_client.create_connection(url)

                if connection and connection.card:
                    agent_card_info = AgentCardInfo(connection.card, url)

                    # ✅ ENHANCED: Comprehensive health check with error handling
                    agent_card_info.status = await self._check_agent_health_with_fallback(url)
                    agent_card_info.health_check_count = 1

                    self.agent_cards[agent_card_info.name] = agent_card_info
                    self.agent_urls[agent_card_info.name] = url
                    results[url] = True

                    # Log status
                    status_msg = "✅" if agent_card_info.status == "active" else "⚠️"
                    logging.info(f"{status_msg} Loaded: {agent_card_info.name} from {url} (Status: {agent_card_info.status})")
                else:
                    results[url] = False
                    logging.error(f"Failed to load agent card from {url}")

            except Exception as e:
                results[url] = False
                logging.error(f"Error loading from {url}: {e}")

                # ✅ ADDED: Create error card for failed agents
                try:
                    error_card = AgentCardInfo(
                        type('MockCard', (), {
                            'name': f"failed_agent_{url.split('/')[-1]}",
                            'description': f"Failed to connect to {url}",
                            'capabilities': []
                        })(),
                        url
                    )
                    error_card.mark_error(e)
                    self.agent_cards[error_card.name] = error_card
                except Exception:
                    pass  # If we can't even create error card, skip it

        return results

    async def _check_agent_health_with_fallback(self, agent_url: str) -> str:
        """Check agent health with multiple fallback methods."""
        # Try primary health check
        try:
            return await self._check_agent_health(agent_url)
        except Exception as primary_error:
            logging.warning(f"Primary health check failed for {agent_url}: {primary_error}")

            # ✅ ADDED: Fallback health checks
            try:
                return await self._check_agent_health_fallback(agent_url)
            except Exception as fallback_error:
                logging.error(f"All health checks failed for {agent_url}: {fallback_error}")
                return "error"

    async def _check_agent_health(self, agent_url: str) -> str:
        """Primary agent health check method."""
        import httpx

        # Prevent concurrent health checks on same URL
        if agent_url in self.health_check_in_progress:
            return "checking"

        self.health_check_in_progress.add(agent_url)
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Try agent card endpoint first
                response = await client.get(f"{agent_url}/.well-known/agent.json")
                if response.status_code == 200:
                    return "active"
                else:
                    return "inactive"
        finally:
            self.health_check_in_progress.discard(agent_url)

    async def _check_agent_health_fallback(self, agent_url: str) -> str:
        """Fallback health check methods."""
        import httpx

        async with httpx.AsyncClient(timeout=3) as client:
            # Try different endpoints that might indicate agent is alive
            endpoints_to_try = [
                "/health",
                "/status", 
                "/",
                "/ping"
            ]

            for endpoint in endpoints_to_try:
                try:
                    response = await client.get(f"{agent_url}{endpoint}")
                    if response.status_code < 500:  # Any non-server-error response
                        return "inactive"  # Alive but not A2A compatible
                except Exception:
                    continue

            return "error"  # No endpoints responded

    def get_all_agent_names(self) -> List[str]:
        return list(self.agent_cards.keys())

    def get_all_agent_cards(self) -> List[AgentCardInfo]:
        return list(self.agent_cards.values())

    def check_agent_status(self, agent_name: str) -> bool:
        """Check if agent is available for delegation."""
        card = self.agent_cards.get(agent_name)
        return card is not None and card.status == "active"

    # ✅ ADDED: Get agents by status
    def get_agents_by_status(self, status: str) -> List[AgentCardInfo]:
        """Get agents filtered by status."""
        return [card for card in self.agent_cards.values() if card.status == status]

    # ✅ ADDED: Get error summary
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of agent errors."""
        error_agents = self.get_agents_by_status("error")
        error_types = {}

        for agent in error_agents:
            if agent.last_error:
                error_type = type(agent.last_error).__name__ if hasattr(agent.last_error, '__class__') else "Unknown"
                error_types[error_type] = error_types.get(error_type, 0) + 1

        return error_types

    # ✅ ADDED: Batch health check with progress
    async def refresh_all_agent_health(self, progress_callback=None) -> Dict[str, str]:
        """Refresh health status for all agents."""
        results = {}

        for i, (agent_name, card) in enumerate(self.agent_cards.items()):
            if progress_callback:
                progress_callback(i, len(self.agent_cards), agent_name)

            try:
                old_status = card.status
                new_status = await self._check_agent_health_with_fallback(card.url)
                card.status = new_status
                card.health_check_count += 1

                if old_status != new_status:
                    logging.info(f"Agent {agent_name} status changed: {old_status} -> {new_status}")

                results[agent_name] = new_status
            except Exception as e:
                card.mark_error(e)
                results[agent_name] = "error"

        return results

    async def close(self):
        """Clean up resources."""
        await self.a2a_client.close()
        self.health_check_in_progress.clear()
