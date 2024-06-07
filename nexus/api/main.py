from typing import List

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from nexus.nexus_base.nexus import ChatSystem

app = FastAPI()


def chat():
    chat = ChatSystem()
    return chat


# Pydantic models for structured data
class Message(BaseModel):
    role: str
    content: str


class AgentCallRequest(BaseModel):
    agent_name: str
    agent_profile: str
    agent_actions: List[str]
    messages: List[Message]

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "OpenAIAgent",
                "agent_profile": "Olly",
                "agent_actions": ["recommend"],
                "messages": [{"content": "Spell CLOCK", "role": "user"}],
            }
        }


@app.get("/get_threads", response_model=List[dict])
async def get_threads(chat: ChatSystem = Depends(chat)):
    threads = [thread.to_dict() for thread in chat.get_all_threads()]
    return threads


@app.get("/read_messages/{thread_id}", response_model=List[Message])
async def get_messages(thread_id: int, chat: ChatSystem = Depends(chat)):
    messages = [message.to_dict() for message in chat.read_messages(thread_id)]
    return messages


@app.get("/get_agent_names", response_model=List[dict])
async def get_agents(chat: ChatSystem = Depends(chat)):
    agents = [{"name": agent} for agent in chat.get_agent_names()]
    return agents


@app.get("/get_profile_names", response_model=List[dict])
async def get_profiles(chat: ChatSystem = Depends(chat)):
    profiles = [{"name": profile} for profile in chat.get_profile_names()]
    return profiles


@app.get("/get_action_names", response_model=List[dict])
async def get_actions(chat: ChatSystem = Depends(chat)):
    actions = [{"name": action} for action in chat.get_action_names()]
    return actions


@app.post("/call_agent", response_model=dict)
async def call_agent(request: AgentCallRequest, chat: ChatSystem = Depends(chat)):
    agent_name = request.agent_name
    agent_profile = request.agent_profile
    agent_actions = request.agent_actions
    messages = request.messages
    agent = chat.get_agent(agent_name)
    agent.profile = chat.get_profile(agent_profile)
    agent.chat_history = messages[:-1]  # get all messages except the last one
    # agent.actions = agent_actions

    generator = agent.get_response_stream(messages[-1].content, 0)

    responses = []
    for item in generator():
        responses.append(item)
    response = "".join(responses)

    return {"response": response}
