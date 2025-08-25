import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .agent import create_app

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
        
        # Build updated state with user message
        messages = state.values.get("messages", [])
        messages.append({"role": "user", "content": user_response})
        
        updated_state = {
            **state.values,
            "messages": messages,
            "user_response": user_response,
            "current_state": "evaluate_answer",
        }
        
        # Run graph step
        result = await _app.ainvoke(updated_state, config=config)
        
        # Send response
        msg = ""
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            msg = getattr(last, "content", last.get("content", "")) if isinstance(last, dict) else getattr(last, "content", str(last))

        await self.send(text_data=json.dumps({"message": msg}))

    async def interview_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))