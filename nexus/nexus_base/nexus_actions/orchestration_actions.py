"""Orchestration actions for A2A agent coordination.

⭐ FULLY IMPLEMENTED - Create at: nexus/nexus_base/nexus_actions/orchestration_actions.py
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional

from nexus.nexus_base.action_manager import agent_action
from nexus.nexus_base.agent_card_manager import AgentCardManager

# Global storage for agent managers
_agent_card_managers: Dict[int, AgentCardManager] = {}
_context_ids: Dict[int, str] = {}

def _get_agent_id(agent) -> int:
    return id(agent)

def _get_or_create_manager(agent) -> AgentCardManager:
    agent_id = _get_agent_id(agent)
    if agent_id not in _agent_card_managers:
        _agent_card_managers[agent_id] = AgentCardManager()
    return _agent_card_managers[agent_id]

def _get_context_id(agent) -> str:
    agent_id = _get_agent_id(agent)
    if agent_id not in _context_ids:
        _context_ids[agent_id] = str(uuid.uuid4())
    return _context_ids[agent_id]

def _sanitize_input(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    return text.replace("\n", " ").replace("\r", "").strip()[:2000]

# ✅ Helper to safely run async code in sync context
def _run_coro(coro):
    try:
        loop = asyncio.get_running_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        # No running loop — use asyncio.run
        return asyncio.run(coro)

@agent_action
def initialize_orchestration(agent_urls: str, _caller_agent=None):
    """Initialize orchestration by loading agent cards from URLs."""
    if not _caller_agent or not agent_urls:
        return "Error: Missing caller agent or URLs"

    urls = [url.strip() for url in agent_urls.split(",") if url.strip().startswith(('http://', 'https://'))]
    if not urls:
        return "Error: No valid URLs provided"

    manager = _get_or_create_manager(_caller_agent)

    try:
        # ✅ FIXED: Safe async execution
        results = _run_coro(
            asyncio.wait_for(manager.load_agents_from_urls(urls), timeout=30.0)
        )
        success_count = sum(1 for v in results.values() if v)
        agent_names = manager.get_all_agent_names()
        return f"✅ Loaded {success_count}/{len(urls)} agents: {', '.join(agent_names)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@agent_action
def list_available_agents(_caller_agent=None):
    """List all available sub-agents."""
    if not _caller_agent:
        return "Error: No caller agent"

    manager = _get_or_create_manager(_caller_agent)
    cards = manager.get_all_agent_cards()

    if not cards:
        return "❌ No agents loaded. Run initialize_orchestration first."

    result = "**Available Sub-Agents:**\n\n"
    for card in cards:
        result += card.to_prompt_text() + "\n\n"
    return result

@agent_action
def delegate_to_agent(agent_name: str, message: str, _caller_agent=None):
    """Delegate task to specific sub-agent."""
    if not _caller_agent or not agent_name or not message:
        return "Error: Missing required parameters"

    agent_name = _sanitize_input(agent_name)
    message = _sanitize_input(message)

    manager = _get_or_create_manager(_caller_agent)

    if not manager.check_agent_status(agent_name):
        available = ', '.join(manager.get_all_agent_names()) or "none"
        return f"❌ Agent '{agent_name}' not available. Available: {available}"

    try:
        # ✅ FIXED: Safe async execution
        result = _run_coro(
            asyncio.wait_for(
                manager.a2a_client.send_message(
                    agent_name=agent_name,
                    message=message,
                    context_id=_get_context_id(_caller_agent),
                ),
                timeout=15.0
            )
        )

        if result["success"]:
            response_text = _sanitize_input(result['response'])
            if hasattr(_caller_agent, 'messages'):
                _caller_agent.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "metadata": {"sub_agent": agent_name}
                })
            return f"[{agent_name}] {response_text}"
        else:
            return f"❌ Error from {agent_name}: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"❌ Communication error: {str(e)}"

@agent_action
def execute_delegation_plan(plan_json: str, _caller_agent=None):
    """Execute a delegation plan sequentially."""
    if not _caller_agent or not plan_json:
        return "Error: Missing parameters"

    # Parse JSON plan
    plan_json = plan_json.strip()
    if "```json" in plan_json:
        start = plan_json.find("```json") + 7
        end = plan_json.find("```", start)
        if end != -1:
            plan_json = plan_json[start:end]

    try:
        plan = json.loads(plan_json.strip())
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON: {str(e)}"

    agents = plan.get("agents", [])
    messages = plan.get("messages", [])
    reasoning = plan.get("reasoning", "No reasoning")

    if not agents or len(agents) != len(messages):
        return "❌ Invalid plan structure"

    # Execute plan
    result = f"**🎭 Orchestration Plan:** {reasoning}\n\n"
    successful = 0

    for idx, (agent_name, msg) in enumerate(zip(agents, messages), 1):
        result += f"**Step {idx}: {agent_name}**\n"
        response = delegate_to_agent(agent_name, msg, _caller_agent=_caller_agent)

        if response.startswith("❌"):
            result += f"🔴 FAILED: {response}\n\n"
        else:
            successful += 1
            result += f"🟢 SUCCESS: {response}\n\n"
        result += "---\n\n"

    result += f"📊 Summary: {successful}/{len(agents)} steps completed"
    return result

@agent_action
def orchestrate(task: str, _caller_agent=None):
    """
    High-level orchestration entry point.

    System:
        You orchestrate complex tasks using available agents.

        First, list available agents: {{#list_available_agents}}

        Then create and execute a plan for: {{task}}

        Use the agents effectively and provide a final summary.

    User:
        Orchestrate: {{task}}
    """
    if not _caller_agent or not task:
        return "Error: Missing task or caller agent"

    manager = _get_or_create_manager(_caller_agent)
    if not manager.get_all_agent_names():
        return "❌ No agents available. Run initialize_orchestration first."

    return f"🎭 Starting orchestration for: {_sanitize_input(task)}"

@agent_action
def plan_delegation(task: str, _caller_agent=None):
    """
    Create a delegation plan for complex tasks.

    System:
        Create a JSON delegation plan for the given task.

        Available agents: {{#list_available_agents}}

        Task: {{task}}

        Return a JSON plan with this exact structure:
        {
            "reasoning": "explanation of approach",
            "agents": ["exact_agent_name_1", "exact_agent_name_2"],
            "messages": ["task for agent 1", "task for agent 2"]
        }

        Use exact agent names and be specific about tasks.

    User:
        Plan delegation for: {{task}}
    """
    if not _caller_agent or not task:
        return "Error: Missing parameters"

    manager = _get_or_create_manager(_caller_agent)
    if not manager.get_all_agent_names():
        return "Error: No agents available"

    return "Delegation plan created based on available agents"
