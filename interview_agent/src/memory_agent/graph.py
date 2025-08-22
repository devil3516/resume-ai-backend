"""Graphs that extract memories on a schedule."""

import asyncio
import logging
from datetime import datetime
from typing import cast, Literal, Optional,Dict

from langchain.chat_models import init_chat_model
from langgraph.graph import END, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.base import BaseStore

from memory_agent import tools, utils
from memory_agent.context import Context
from memory_agent.state import State
from memory_agent.prompts import (
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

logger = logging.getLogger(__name__)

# Initialize the language model to be used for memory extraction
llm = init_chat_model()

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

# async def call_model(state: State, runtime: Runtime[Context]) -> dict:
#     """Extract the user's state from the conversation and update the memory."""
#     user_id = runtime.context.user_id
#     model = runtime.context.model
#     system_prompt = runtime.context.system_prompt

#     # Retrieve the most recent memories for context
#     memories = await cast(BaseStore, runtime.store).asearch(
#         ("memories", user_id),
#         query=str([m.content for m in state.messages[-3:]]),
#         limit=10,
#     )

#     # Format memories for inclusion in the prompt
#     formatted = "\n".join(
#         f"[{mem.key}]: {mem.value} (similarity: {mem.score})" for mem in memories
#     )
#     if formatted:
#         formatted = f"""
# <memories>
# {formatted}
# </memories>"""

#     # Prepare the system prompt with user memories and current time
#     # This helps the model understand the context and temporal relevance
#     sys = system_prompt.format(user_info=formatted, time=datetime.now().isoformat())

#     # Invoke the language model with the prepared prompt and tools
#     # "bind_tools" gives the LLM the JSON schema for all tools in the list so it knows how
#     # to use them.
#     msg = await llm.bind_tools([tools.upsert_memory]).ainvoke(
#         [{"role": "system", "content": sys}, *state.messages],
#         context=utils.split_model_and_provider(model),
#     )
#     return {"messages": [msg]}


# async def store_memory(state: State, runtime: Runtime[Context]):
#     # Extract tool calls from the last message
#     tool_calls = getattr(state.messages[-1], "tool_calls", [])

#     # Concurrently execute all upsert_memory calls
#     saved_memories = await asyncio.gather(
#         *(
#             tools.upsert_memory(
#                 **tc["args"],
#                 user_id=runtime.context.user_id,
#                 store=cast(BaseStore, runtime.store),
#             )
#             for tc in tool_calls
#         )
#     )

#     # Format the results of memory storage operations
#     # This provides confirmation to the model that the actions it took were completed
#     results = [
#         {
#             "role": "tool",
#             "content": mem,
#             "tool_call_id": tc["id"],
#         }
#         for tc, mem in zip(tool_calls, saved_memories)
#     ]
#     return {"messages": results}


# def route_message(state: State):
#     """Determine the next step based on the presence of tool calls."""
#     msg = state.messages[-1]
#     if getattr(msg, "tool_calls", None):
#         # If there are tool calls, we need to store memories
#         return "store_memory"
#     # Otherwise, finish; user can send the next message
#     return END


# # Create the graph + all nodes
# builder = StateGraph(State, context_schema=Context)

# # Define the flow of the memory extraction process
# builder.add_node(call_model)
# builder.add_edge("__start__", "call_model")
# builder.add_node(store_memory)
# builder.add_conditional_edges("call_model", route_message, ["store_memory", END])
# # Right now, we're returning control to the user after storing a memory
# # Depending on the model, you may want to route back to the model
# # to let it first store memories, then generate a response
# builder.add_edge("store_memory", "call_model")
# graph = builder.compile()
# graph.name = "MemoryAgent"


# __all__ = ["graph"]


async def start_interview(state: State, runtime: Runtime[Context]) -> dict:
    """Start the interview with a greeting."""
    context = runtime.context

    max_questions = calculate_max_questions(context.interview_duration)
    # Get type-specific instructions
    type_instructions_map = {
        "technical": TECHNICAL_INSTRUCTIONS,
        "behavioral": BEHAVIORAL_INSTRUCTIONS,
        "mixed": MIXED_INSTRUCTIONS
    }
    
    type_instructions = type_instructions_map.get(context.interview_type.value, MIXED_INSTRUCTIONS)

    greetings = START_PROMPT.format(
        interview_type=context.interview_type.value,
        job_title=context.job_title,
        company=context.company,
        experience_level=context.experience_level.value,
        interview_duration=context.interview_duration
    )

    return {
        "messages": [{"role": "assistant", "content": greetings}],
        "interview_started": True,
        "current_state": "awaiting_response",
        "max_questions": max_questions,
        "job_title": context.job_title,
        "company": context.company,
        "job_description": context.job_description,
        "interview_type": context.interview_type,
        "experience_level": context.experience_level,
        "interview_duration": context.interview_duration,
        "voice_analysis_enabled": context.voice_analysis_enabled
    }

async def ask_question(state: State, runtime: Runtime[Context]) -> dict:
    """Ask a question to the user."""
    context = runtime.context

    # Get type-specific instructions
    type_instructions = {
        "technical": "Focus on technical skills and knowledge.",
        "behavioral": "Focus on behavioral and situational questions.",
        "mixed": "Balance between technical and behavioral questions."
    }

    prompt = NEXT_QUESTION_PROMPT.format(
        job_title=state.job_title,
        company=state.company,
        job_description=state.job_description,
        interview_type=state.interview_type.value,
        experience_level=state.experience_level.value,
        conversation_history="\n".join([msg.content for msg in state.messages if hasattr(msg, 'content')])
    )

    #Generate question using llm
    response = await llm.ainvoke([{"role": "system", "content": prompt}])
    question = response.content

    return {
        "messages": [{"role": "assistant", "content": question}],
        "current_question": question,
        "question_count": state.question_count + 1,
        "current_state": "awaiting_response"
    }

async def analyze_voice_response(state:State, runtime:Runtime[Context]) -> dict:
    """Analyze the voice response of the user."""
    if not state.voice_analysis_enabled or not state.user_response:
        return {"voice_feedback": None}
    
    prompt = VOICE_ANALYSIS_PROMPT.format(user_response = state.user_response)
    response = await llm.ainvoke([{"role": "system", "content": prompt}])

    return {"voice_feedback":response.content}

async def evaluate_answer(state:State, runtime:Runtime[Context]) -> dict:
    """Evaluate the answer of the user."""
    context = runtime.context

    #Analyze voice if enabeled
    voice_analysis = await analyze_voice_response(state, runtime)
    prompt = EVALUATE_ANSWER_PROMPT.format(
        job_description = state.job_description,
        job_title = state.job_title,
        interview_type = state.interview_type.value,
        current_question = state.current_question,
        user_response = state.user_response,
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

    if follow_up_needed and follow_up_question:
        response_content += f"\n\nFOLLOW_UP_QUESTION: {follow_up_question}"
        return{
            "messages": [{"role": "assistant", "content": response_content}],
            "follow_up_needed": True,
            "current_question": follow_up_question,
            "current_state": "awaiting_response",
            "voice_feedback": voice_analysis.get("voice_feedback")
        }
    else:
        return {
            "messages": [{"role": "assistant", "content": response_content}],
            "follow_up_needed": False,
            "current_state": "ask_question",
            "voice_feedback": voice_analysis.get("voice_feedback")
        }
    
async def end_interview(state:State, runtime:Runtime[Context]) -> dict:
    """End the interview with a closing message."""
    context = runtime.context

    prompt = CLOSING_PROMPT.format(
        job_title=state.job_title,
        company = state.company,
        interview_type = state.interview_type.value
    )
    #Generate closing remarks using llm
    response = await llm.ainvoke([{"role": "system", "content": prompt}])
    closing = response.content
    return {
        "messages": [{"role": "assistant", "content": closing}],
        "current_state": "end"
    }

def route_after_start(state:State) -> Literal["ask_question", "end"]:
    """Route after interview start."""
    if state.interview_started:
        return "ask_question"
    return "end"

def route_after_evaluation(state:State) -> Literal["ask_question","follow_up" "end"]:
    """Route after answer evaluation."""
    if state.follow_up_needed:
        return "follow_up"
    elif state.question_count >= state.max_questions:
        return "end"
    else:
        return "ask_question"
    

def route_after_follow_up(state:State) -> Literal["ask_question", "end"]:
    """Route after follow-up question."""
    if state.question_count >= state.max_questions:
        return "end"
    return "ask_question"

#Create the interview graph
builder = StateGraph(State, context_schema=Context)

#Define Nodes
builder.add_node("start_interview", start_interview)
builder.add_node("ask_question", ask_question)
builder.add_node("evaluate_answer", evaluate_answer)
builder.add_node("end_interview", end_interview)

#Define Edges
builder.set_entry_point("start_interview")

builder.add_conditional_edges(
    "start_interview",
    route_after_start,
    [ask_question, end_interview]
)

builder.add_conditional_edges(
    "follow_up",
    route_after_follow_up,
    ["ask_question", "end_interview"]
)

builder.add_edge("end_interview", END)

#Compile the graph
interview_graph = builder.compile()

interview_graph.name = "MockInterviewAgent"

__all__ = ["interview_graph"]




            
        

    