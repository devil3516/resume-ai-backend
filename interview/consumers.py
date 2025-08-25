import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

# Import the app factory
from .agent import create_app

# Single app instance for WS flows
_app = create_app("interview_memory.db")

class InterviewConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.interview_id = self.scope["url_route"]["kwargs"]["interview_id"]
        self.room_group_name = f"interview_{self.interview_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_response = data.get("message", "").strip()
        if not user_response:
            return

        config = {"configurable": {"thread_id": self.interview_id}}
        # Get current state
        state = await _app.aget_state(config)
        # Prepare updated state to evaluate the user's answer
        updated_state = {
            **state.values,
            "user_response": user_response,
            "current_state": "evaluate_answer",
        }
        # Run one step of the graph
        result = await _app.ainvoke(updated_state, config=config)

        # Extract assistant message
        msg = ""
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            msg = getattr(last, "content", last.get("content", "")) if isinstance(last, dict) else getattr(last, "content", str(last))

        # Emit back to the client
        await self.send(text_data=json.dumps({"message": msg}))

    async def interview_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    async def interview_agent(self, event):
        user_response = event["user_response"]
        interview_id = self.interview_id

        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        # Update the state with the user response
        await channel_layer.group_send(
            f"interview_{interview_id}",
            {
                "type": "interview.update_state",
                "user_response": user_response,
            },
        )
        
        # Send a message back to the group to trigger the next step in the graph
        await channel_layer.group_send(
            f"interview_{interview_id}",
            {
                "type": "interview.process_next",
            },
        )

    async def interview_update_state(self, event):
        self.user_response = event["user_response"]

    async def interview_process_next(self, event):
        # TODO: Trigger the next step in the graph
        print("Triggering next step in the graph")
        pass