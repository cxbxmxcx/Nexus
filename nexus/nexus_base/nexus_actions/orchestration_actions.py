"""Orchestration actions for A2A agent coordination.

⭐ ENHANCED AND STABILIZED VERSION - Replaces: nexus/nexus_base/nexus_actions/orchestration_actions.py
This version removes global state management in favor of instance-based state on the calling agent.
"""

import asyncio
import json
import uuid
import concurrent.futures
from typing import Dict, List, Optional

from nexus.nexus_base.action_manager import agent_action
from nexus.nexus_base.agent_card_manager import AgentCardManager

# --- Helper Functions ---

def _get_manager(agent) -> Optional[AgentCardManager]:
    """Safely retrieves the orchestration manager from the agent instance."""
    return getattr(agent, 'orchestration_manager', None)

def _get_context_id(agent) -> str:
    """Gets or creates a unique context ID on the agent instance."""
    if not hasattr(agent, 'orchestration_context_id') or not agent.orchestration_context_id:
        agent.orchestration_context_id = str(uuid.uuid4())
    return agent.orchestration_context_id

def _sanitize_input(text: str) -> str:
    """Sanitizes text to prevent injection and formatting issues."""
    if not isinstance(text, str):
        return str(text)
    return text.replace("\n", " ").replace("\r", "").strip()[:2000]

def _run_coro(coro):
    """Safely execute async code in a sync context, handling nested event loops."""
    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        return asyncio.run(coro)

# --- Core Agent Actions ---

@agent_action
def initialize_orchestration(agent_urls: str, _caller_agent=None):
    """
    Initialize orchestration for the calling agent by loading sub-agent cards from URLs.
    This creates an orchestration manager on the agent instance.
    """
    if not _caller_agent:
        return "Error: Calling agent is missing. This action must be called by an agent."
    if not isinstance(agent_urls, str) or not agent_urls:
        return "Error: agent_urls parameter must be a non-empty string."

    urls = [url.strip() for url in agent_urls.split(',') if url.strip().startswith(('http://', 'https://'))]
    if not urls:
        return "Error: No valid URLs were provided."

    # Create and assign the manager directly to the agent instance
    manager = AgentCardManager()
    _caller_agent.orchestration_manager = manager

    try:
        results = _run_coro(
            asyncio.wait_for(manager.load_agents_from_urls(urls), timeout=30.0)
        )
        success_count = sum(1 for v in results.values() if v)
        agent_names = manager.get_all_agent_names()
        return f"✅ Orchestration initialized. Loaded {success_count}/{len(urls)} agents: {', '.join(agent_names)}"
    except Exception as e:
        _caller_agent.orchestration_manager = None
        return f"❌ Error during initialization: {str(e)}"

@agent_action
def list_available_agents(_caller_agent=None):
    """List all available sub-agents managed by the calling agent."""
    manager = _get_manager(_caller_agent)
    if not manager:
        return "Error: Orchestration is not initialized. Call initialize_orchestration first."

    cards = manager.get_all_agent_cards()
    if not cards:
        return "❌ No agents loaded."

    result = "**Available Sub-Agents:**\n\n"
    for card in cards:
        result += card.to_prompt_text() + "\n\n"
    return result

@agent_action
def delegate_to_agent(agent_name: str, message: str, _caller_agent=None):
    """Delegate a task to a specific sub-agent."""
    manager = _get_manager(_caller_agent)
    if not manager:
        return "Error: Orchestration is not initialized."
    if not agent_name or not message:
        return "Error: agent_name and message parameters are required."

    agent_name = _sanitize_input(agent_name)
    message = _sanitize_input(message)

    if not manager.check_agent_status(agent_name):
        available = ', '.join(manager.get_all_agent_names()) or "none"
        return f"❌ Agent '{agent_name}' not available. Available agents: {available}"

    context_id = _get_context_id(_caller_agent)
    try:
        conversation_history = _get_conversation_history(_caller_agent)
        result = _run_coro(
            asyncio.wait_for(
                manager.a2a_client.send_message(
                    agent_name=agent_name,
                    message=message,
                    context_id=context_id,
                    conversation_history=conversation_history
                ),
                timeout=15.0
            )
        )

        if result.get("success"):
            response_text = _sanitize_input(result.get('response', ''))
            if hasattr(_caller_agent, 'messages') and isinstance(_caller_agent.messages, list):
                _caller_agent.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "metadata": {"sub_agent": agent_name}
                })
            return f"[{agent_name}] {response_text}"
        else:
            return f"❌ Error from {agent_name}: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"❌ Communication error with {agent_name}: {str(e)}"

@agent_action
def execute_delegation_plan(plan_json: str, _caller_agent=None):
    """Execute a multi-step delegation plan sequentially."""
    manager = _get_manager(_caller_agent)
    if not manager:
        return "Error: Orchestration is not initialized."
    if not plan_json:
        return "Error: plan_json parameter is missing."

    plan_json = plan_json.strip()
    if "```json" in plan_json:
        start_index = plan_json.find("```json") + 7
        end_index = plan_json.rfind("```")
        if end_index > start_index:
            plan_json = plan_json[start_index:end_index].strip()

    try:
        plan = json.loads(plan_json)
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON in plan: {str(e)}"

    agents = plan.get("agents", [])
    messages = plan.get("messages", [])
    if not isinstance(agents, list) or not isinstance(messages, list) or len(agents) != len(messages):
        return "❌ Invalid plan structure: 'agents' and 'messages' must be lists of the same length."

    reasoning = plan.get("reasoning", "No reasoning provided.")
    result_summary = f"**🎭 Orchestration Plan:** {reasoning}\n\n"
    successful_steps = 0

    for i, (agent_name, msg) in enumerate(zip(agents, messages), 1):
        result_summary += f"**Step {i}: Delegate to {agent_name}**\n`{msg}`\n"
        response = delegate_to_agent(agent_name, msg, _caller_agent=_caller_agent)
        result_summary += f"Response: {response}\n\n---\n\n"
        if not response.startswith("❌"):
            successful_steps += 1

    result_summary += f"📊 **Summary:** {successful_steps}/{len(agents)} steps completed successfully."
    return result_summary

@agent_action
def refresh_agents(_caller_agent=None):
    """Refresh all sub-agent connections and health status."""
    manager = _get_manager(_caller_agent)
    if not manager:
        return "Error: Orchestration is not initialized."
    if not manager.get_all_agent_cards():
        return "❌ No agents to refresh."

    try:
        results = _run_coro(
            asyncio.wait_for(manager.refresh_all_agent_health(), timeout=20.0)
        )
        active = sum(1 for status in results.values() if status == "active")
        total = len(results)
        return f"✅ Refreshed {total} agents: {active} active, {total-active} inactive/error."
    except Exception as e:
        return f"❌ Refresh failed: {str(e)}"

@agent_action
def get_orchestration_status(_caller_agent=None):
    """Get a summary of the current orchestration status."""
    manager = _get_manager(_caller_agent)
    if not manager:
        return "Error: Orchestration is not initialized."
    cards = manager.get_all_agent_cards()
    if not cards:
        return "❌ No agents loaded."

    active = manager.get_agents_by_status("active")
    inactive = manager.get_agents_by_status("inactive")
    error = manager.get_agents_by_status("error")
    total = len(cards)

    status = f"📊 **Orchestration Status:**\n"
    status += f"**Total Agents:** {total}\n"
    status += f"**Active:** {len(active)} 🟢\n"
    status += f"**Inactive:** {len(inactive)} 🔴\n"
    status += f"**Error:** {len(error)} ❌\n"
    status += f"**Health:** {(len(active)/total*100):.0f}%"
    return status

@agent_action
def cleanup_orchestration(_caller_agent=None):
    """Clean up and terminate the orchestration session for the agent."""
    if not _caller_agent:
        return "Error: Calling agent is missing."

    manager = _get_manager(_caller_agent)
    if manager:
        try:
            _run_coro(manager.close())
        except Exception as e:
            print(f"Error closing orchestration manager: {e}")
        _caller_agent.orchestration_manager = None

    if hasattr(_caller_agent, 'orchestration_context_id'):
        _caller_agent.orchestration_context_id = None

    return "✅ Orchestration resources have been cleaned up."

def _get_conversation_history(agent) -> str:
    """Build a concise conversation history from the agent's messages."""
    if not hasattr(agent, 'messages') or not isinstance(agent.messages, list):
        return ""

    history_lines = []
    for msg in agent.messages[-10:]:
        role = msg.get("role", "unknown")
        content = str(msg.get("content", ""))
        if role == "system":
            continue
        elif role == "user":
            history_lines.append(f"User: {content}")
        elif role == "assistant":
            sub_agent = msg.get("metadata", {}).get("sub_agent")
            if sub_agent:
                history_lines.append(f"{sub_agent}: {content}")
            else:
                history_lines.append(f"Assistant: {content}")
    return "\n".join(history_lines)
