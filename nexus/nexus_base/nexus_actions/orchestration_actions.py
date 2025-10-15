import asyncio
import json
import uuid
import concurrent.futures
from typing import Dict

from nexus.nexus_base.action_manager import agent_action
from nexus.nexus_base.agent_card_manager import AgentCardManager

def _sanitize_input(text: str) -> str:
    """Sanitizes text to prevent injection and formatting issues."""
    if not isinstance(text, str):
        return str(text)
    return text.replace("\n", " ").replace("\r", "").strip()[:2000]

def _run_coro(coro):
    """Safely execute async code in a sync context, handling nested event loops."""
    try:
        # If a loop is already running, use a thread pool to avoid RuntimeError
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No running loop, so it's safe to use asyncio.run
        return asyncio.run(coro)

@agent_action
def initialize_orchestration(agent_urls: str, _caller_agent=None):
    """
    Initialize orchestration for the calling agent by loading sub-agent cards from URLs.
    This creates an orchestration manager on the agent.
    """
    if not _caller_agent:
        return "Error: Calling agent is missing. This action must be called by an agent."
    if not agent_urls:
        return "Error: agent_urls parameter is missing or empty."

    urls = [url.strip() for url in agent_urls.split(",") if url.strip().startswith(('http://', 'https://'))]
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
        # If initialization fails, clean up the manager
        _caller_agent.orchestration_manager = None
        return f"❌ Error during initialization: {str(e)}"

@agent_action
def list_available_agents(_caller_agent=None):
    """List all available sub-agents managed by the calling agent."""
    if not _caller_agent or not hasattr(_caller_agent, 'orchestration_manager') or not _caller_agent.orchestration_manager:
        return "Error: Orchestration is not initialized. Call initialize_orchestration first."

    manager = _caller_agent.orchestration_manager
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
    if not _caller_agent or not hasattr(_caller_agent, 'orchestration_manager') or not _caller_agent.orchestration_manager:
        return "Error: Orchestration is not initialized."
    if not agent_name or not message:
        return "Error: agent_name and message parameters are required."

    agent_name = _sanitize_input(agent_name)
    message = _sanitize_input(message)
    manager = _caller_agent.orchestration_manager

    if not manager.check_agent_status(agent_name):
        available = ', '.join(manager.get_all_agent_names()) or "none"
        return f"❌ Agent '{agent_name}' not available. Available agents: {available}"

    # Manage context_id directly on the agent
    if not hasattr(_caller_agent, 'orchestration_context_id') or not _caller_agent.orchestration_context_id:
        _caller_agent.orchestration_context_id = str(uuid.uuid4())
    context_id = _caller_agent.orchestration_context_id

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
            # Append to host agent's history for context
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
        return f"❌ Communication error with {agent_name}: {str(e)}"

@agent_action
def execute_delegation_plan(plan_json: str, _caller_agent=None):
    """Execute a multi-step delegation plan sequentially."""
    if not _caller_agent or not hasattr(_caller_agent, 'orchestration_manager') or not _caller_agent.orchestration_manager:
        return "Error: Orchestration is not initialized."
    if not plan_json:
        return "Error: plan_json parameter is missing."

    # Safely extract JSON from markdown code blocks
    plan_json = plan_json.strip()
    if "```json" in plan_json:
        start_index = plan_json.find("```json") + 7
        end_index = plan_json.find("```", start_index)
        if end_index != -1:
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
        result_summary += f"**Step {i}: Delegate to {agent_name}**\n"
        response = delegate_to_agent(agent_name, msg, _caller_agent=_caller_agent)
        result_summary += f"Response: {response}\n\n---\n\n"
        if not response.startswith("❌"):
            successful_steps += 1

    result_summary += f"📊 **Summary:** {successful_steps}/{len(agents)} steps completed successfully."
    return result_summary

@agent_action
def cleanup_orchestration(_caller_agent=None):
    """Clean up and terminate the orchestration session for the agent."""
    if not _caller_agent:
        return "Error: Calling agent is missing."

    # Clean up the manager on the agent instance
    if hasattr(_caller_agent, 'orchestration_manager') and _caller_agent.orchestration_manager:
        manager = _caller_agent.orchestration_manager
        try:
            _run_coro(manager.close())
        except Exception as e:
            # Log error but continue cleanup
            print(f"Error closing orchestration manager: {e}")
        _caller_agent.orchestration_manager = None

    # Clean up context ID
    if hasattr(_caller_agent, 'orchestration_context_id'):
        _caller_agent.orchestration_context_id = None

    return "✅ Orchestration resources have been cleaned up."

# --- Helper functions that don't depend on global state ---

def _get_conversation_history(agent) -> str:
    """Build a concise conversation history from the agent's messages."""
    if not hasattr(agent, 'messages') or not agent.messages:
        return ""

    history_lines = []
    # Take the last 10 messages to keep the context relevant and performant
    for msg in agent.messages[-10:]:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "system":
            continue  # System messages are usually for setup, not context
        elif role == "user":
            history_lines.append(f"User: {content}")
        elif role == "assistant":
            # Check if it was a sub-agent's response
            sub_agent_name = msg.get("metadata", {}).get("sub_agent")
            if sub_agent_name:
                history_lines.append(f"{sub_agent_name}: {content}")
            else:
                history_lines.append(f"Assistant: {content}")

    return "\n".join(history_lines)
