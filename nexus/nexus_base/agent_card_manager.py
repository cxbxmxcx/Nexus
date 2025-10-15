"""Manager for A2A Agent Cards.

⭐ PRODUCTION VERSION - Create at: nexus/nexus_base/agent_card_manager.py
"""

from typing import Dict, List, Optional
import logging

try:
    from a2a.types import AgentCard as A2AAgentCard
    from nexus.nexus_base.a2a_client import NexusA2AClient
except ImportError:
    raise ImportError("Install a2a-sdk: pip install a2a-sdk>=0.2.3")


class AgentCardInfo:
    """Wrapper for A2A Agent Card with metadata."""

    def __init__(self, a2a_card: A2AAgentCard, agent_url: str):
        self.a2a_card = a2a_card
        self.name = str(a2a_card.name) if a2a_card.name else "unnamed_agent"
        self.description = str(a2a_card.description or "No description")
        self.url = agent_url.rstrip('/')
        self.capabilities = [str(cap) for cap in (getattr(a2a_card, "capabilities", []) or [])]
        self.status = "active"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "capabilities": self.capabilities,
            "status": self.status,
        }

    def to_prompt_text(self) -> str:
        caps = ", ".join(self.capabilities) if self.capabilities else "general purpose"
        status_icon = "🟢" if self.status == "active" else "🔴"
        return f"{status_icon} **{self.name}**: {self.description}\n   Capabilities: {caps}"


class AgentCardManager:
    """Manages agent cards for orchestration."""

    def __init__(self):
        self.agent_cards: Dict[str, AgentCardInfo] = {}
        self.agent_urls: Dict[str, str] = {}
        self.a2a_client = NexusA2AClient()

    async def load_agents_from_urls(self, agent_urls: List[str]) -> Dict[str, bool]:
        """Load agent cards from URLs."""
        results = {}

        for url in agent_urls:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                results[url] = False
                continue

            try:
                connection = await self.a2a_client.create_connection(url)

                if connection and connection.card:
                    agent_card_info = AgentCardInfo(connection.card, url)
                    agent_card_info.status = await self._check_agent_health(url)

                    self.agent_cards[agent_card_info.name] = agent_card_info
                    self.agent_urls[agent_card_info.name] = url
                    results[url] = True

                    status_msg = "✅" if agent_card_info.status == "active" else "⚠️"
                    print(f"{status_msg} Loaded: {agent_card_info.name} from {url}")
                else:
                    results[url] = False
                    print(f"✗ Failed to load from {url}")

            except Exception as e:
                results[url] = False
                print(f"✗ Error loading from {url}: {e}")

        return results

    async def _check_agent_health(self, agent_url: str) -> str:
        """Check agent health."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{agent_url}/.well-known/agent.json")
                return "active" if response.status_code == 200 else "inactive"
        except:
            return "inactive"

    def get_all_agent_names(self) -> List[str]:
        return list(self.agent_cards.keys())

    def get_all_agent_cards(self) -> List[AgentCardInfo]:
        return list(self.agent_cards.values())

    def check_agent_status(self, agent_name: str) -> bool:
        card = self.agent_cards.get(agent_name)
        return card is not None and card.status == "active"

    async def close(self):
        await self.a2a_client.close()
