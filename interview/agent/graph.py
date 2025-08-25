"""Interview StateGraph definition."""

import logging
import os
from typing import Literal
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage, AIMessage

from langchain.chat_models import init_chat_model
from langgraph.graph import END, StateGraph
# from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from .state import State
from .prompts import (
    START_PROMPT, 
    EVALUATE_ANSWER_PROMPT, 
    FOLLOW_UP_PROMPT, 
    NEXT_QUESTION_PROMPT,
    CLOSING_PROMPT,
    VOICE_ANALYSIS_PROMPT,
    SYSTEM_PROMPT,
    TECHNICAL_INSTRUCTIONS,
    BEHAVIORAL_INSTRUCTIONS,
    MIXED_INSTRUCTIONS
)

# Ensure .env is loaded even in ASGI import path
load_dotenv()

logger = logging.getLogger(__name__) 

# Initialize the language model to be used for memory extraction
MODEL_NAME = os.environ.get("LLM_MODEL", "groq/llama3-8b-8192")
if "/" in MODEL_NAME:
    provider, model = MODEL_NAME.split("/", 1)
    extra = {}
    if provider == "groq":
        extra["api_key"] = os.environ.get("GROQ_API_KEY")
    llm = init_chat_model(model=model, model_provider=provider, **extra)
else:
    provider = os.environ.get("LLM_PROVIDER", "openai")
    llm = init_chat_model(model=MODEL_NAME, model_provider=provider)

def calculate_max_questions(duration: int) -> int:
    """Calculate number of questions based on interview duration."""
    if duration <= 15:
        return 5
    elif duration <= 30:
        return 8
    elif duration <= 45:
        return 12
    else:
        return 15

async def start_interview(state: State) -> dict:
    """Start the interview with a greeting."""
    max_questions = calculate_max_questions(state.interview_duration)

    interview_type_value = state.interview_type.value if hasattr(state.interview_type, "value") else str(state.interview_type)

    greetings = START_PROMPT.format(
        interview_type=interview_type_value,
        job_title=state.job_title,
        company=state.company,
        experience_level=state.experience_level.value if hasattr(state.experience_level, "value") else str(state.experience_level),
        interview_duration=state.interview_duration,
    )

    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    interview_id = state.interview_id

    await channel_layer.group_send(
        f"interview_{interview_id}", {"type": "interview.message", "message": greetings}
    )

    return {
        "messages": [{"role": "assistant", "content": greetings}],
        "interview_started": True,
        "current_state": "awaiting_response",
        "max_questions": max_questions,
        "job_title": state.job_title,
        "company": state.company,
        "job_description": state.job_description,
        "interview_type": state.interview_type,
        "experience_level": state.experience_level,
        "interview_duration": state.interview_duration,
        "voice_analysis_enabled": state.voice_analysis_enabled,
        "interview_id": interview_id,
    }

async def ask_question(state: State) -> dict:
    """Ask a question to the user."""
    prompt = NEXT_QUESTION_PROMPT.format(
        job_title=state.job_title,
        company=state.company,
        job_description=state.job_description,
        interview_type=state.interview_type.value if hasattr(state.interview_type, "value") else str(state.interview_type),
        experience_level=state.experience_level.value if hasattr(state.experience_level, "value") else str(state.experience_level),
        conversation_history="\n".join([msg.content for msg in state.messages if hasattr(msg, 'content')])
    )

    response = await llm.ainvoke([{"role": "system", "content": prompt}])
    question = response.content

    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    interview_id = state.interview_id

    await channel_layer.group_send(
        f"interview_{interview_id}", {"type": "interview.message", "message": question}
    )

    return {
        "messages": [{"role": "assistant", "content": question}],
        "current_question": question,
        "question_count": state.question_count + 1,
        "current_state": "awaiting_response",
    }

async def analyze_voice_response(state: State) -> dict:
    """Analyze the voice response of the user."""
    if not state.voice_analysis_enabled or not state.user_response:
        return {"voice_feedback": None}
    
    prompt = VOICE_ANALYSIS_PROMPT.format(user_response = state.user_response)
    response = await llm.ainvoke([{"role": "system", "content": prompt}])

    return {"voice_feedback":response.content}

async def evaluate_answer(state: State) -> dict:
    """Evaluate the answer of the user."""
    voice_analysis = await analyze_voice_response(state)
    prompt = EVALUATE_ANSWER_PROMPT.format(
        job_description=state.job_description,
        job_title=state.job_title,
        interview_type=state.interview_type.value if hasattr(state.interview_type, "value") else str(state.interview_type),
        current_question=state.current_question,
        user_response=state.user_response,
    )

    response = await llm.ainvoke([{"role": "system", "content": prompt}])
    evaluation = response.content

    feedback = ""
    follow_up_needed = False
    follow_up_question = ""

    lines = evaluation.split("\n")
    for line in lines:
        if line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:","").strip()
        elif line.startswith("FOLLOW_UP_NEEDED:"):
            follow_up_needed = "yes" in line.lower()
        elif line.startswith("FOLLOW_UP_QUESTION:"):
            follow_up_question = line.replace("FOLLOW_UP_QUESTION:","").strip()

    #Add voice feedback if possible
    if voice_analysis.get("voice_feedback"):
        feedback += f"\n\nVoice Feedback: {voice_analysis['voice_feedback']}"

    #prepare response
    response_content = f"Feedback: {feedback}"

    # Broadcast feedback immediately to the client over WS
    try:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        interview_id = state.interview_id
        # Fire-and-forget broadcast; ignore if channel layer not available
        await channel_layer.group_send(
            f"interview_{interview_id}",
            {"type": "interview.message", "message": response_content},
        )
    except Exception:
        pass

    result: dict = {
        
        "messages": [
            {"role": "user", "content": state.user_response},
            {"role": "assistant", "content": response_content}
            ],
        "follow_up_needed": follow_up_needed,
        "current_state": "ask_question",
        "voice_feedback": voice_analysis.get("voice_feedback"),
    }

    if follow_up_needed and follow_up_question:
        result.update({
            "current_question": follow_up_question,
            "current_state": "awaiting_response",
        })
    return result

async def follow_up(state: State) -> dict:
    """Ask a follow-up question when needed to keep a human-like flow."""
    question = state.current_question or "Could you elaborate a bit more on your previous answer?"

    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    interview_id = state.interview_id

    await channel_layer.group_send(
        f"interview_{interview_id}", {"type": "interview.message", "message": question}
    )

    return {
        "messages": [{"role": "assistant", "content": question}],
        "current_state": "awaiting_response",
    }

async def end_interview(state: State) -> dict:
    """End the interview with a closing message."""
    prompt = CLOSING_PROMPT.format(
        job_title=state.job_title,
        company = state.company,
        interview_type = state.interview_type.value if hasattr(state.interview_type, "value") else str(state.interview_type),
    )
    response = await llm.ainvoke([{"role": "system", "content": prompt}])
    closing = response.content
    return {
        "messages": [{"role": "assistant", "content": closing}],
        "current_state": "end",
    }


def route_after_start(state:State) -> Literal["ask_question", "end"]:
    if state.interview_started:
        return "ask_question"
    return "end"


def route_after_evaluation(state:State) -> Literal["follow_up", "ask_question", "end"]:
    if getattr(state, "follow_up_needed", False):
        return "follow_up"
    if state.question_count >= state.max_questions:
        return "end"
    return "ask_question"

# Create the interview graph builder
builder = StateGraph(State)

# Define Nodes
builder.add_node("start_interview", start_interview)
builder.add_node("ask_question", ask_question)
builder.add_node("evaluate_answer", evaluate_answer)
builder.add_node("follow_up", follow_up)
builder.add_node("end_interview", end_interview)

# Define Edges
builder.set_entry_point("start_interview")

builder.add_conditional_edges(
    "start_interview",
    route_after_start,
    ["ask_question", "end_interview"]
)

# After evaluation, branch to follow_up, ask, or end
builder.add_conditional_edges(
    "evaluate_answer",
    route_after_evaluation,
    ["follow_up", "ask_question", "end_interview"],
)

builder.add_edge("end_interview", END)

# Factory to compile app with checkpointer

def create_app(db_path: str):
    # checkpointer = SqliteSaver.from_conn_string(db_path)
    checkpointer = MemorySaver()
    app = builder.compile(checkpointer=checkpointer)
    app.name = "MockInterviewAgent"
    return app

__all__ = ["create_app"]