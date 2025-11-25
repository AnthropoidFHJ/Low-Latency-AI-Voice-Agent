import os
import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator, Dict, Any
from fastapi import WebSocket
from dotenv import load_dotenv
from database import db

load_dotenv()

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.frames.frames import Frame, AudioRawFrame, TextFrame, EndFrame
from pipecat.services.google.gemini_live import GeminiLiveLLMService
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv('GEMINI_API_KEY')

class FormTool:
    def __init__(self):
        self.form_data = {}
        self.form_active = False
        self.fields = ['name', 'phone', 'jobTitle']
        self.session_id = str(uuid.uuid4())
        
    def open_form(self) -> Dict[str, Any]:
        self.form_active = True
        self.form_data = {field: "" for field in self.fields}
        self.session_id = str(uuid.uuid4())
        
        # Save initial form session to database
        db.save_form_session(self.session_id, self.form_data, "in_progress")
        
        return {
            "action": "form_opened",
            "message": "Form opened! I'll collect your name, phone number, and job title.",
            "fields": self.fields,
            "data": self.form_data,
            "session_id": self.session_id
        }
    
    def update_field(self, field: str, value: str) -> Dict[str, Any]:
        if not self.form_active:
            return {"action": "error", "message": "No form is currently open."}
        
        if field in self.fields:
            self.form_data[field] = value
            
            # Update form session in database
            db.save_form_session(self.session_id, self.form_data, "in_progress")
            
            return {
                "action": "field_updated",
                "field": field,
                "value": value,
                "message": f"Updated {field} to {value}",
                "data": self.form_data,
                "session_id": self.session_id
            }
        else:
            return {"action": "error", "message": f"Unknown field: {field}"}
    
    def submit_form(self) -> Dict[str, Any]:
        if not self.form_active:
            return {"action": "error", "message": "No form is currently open."}
        
        required_fields = ['name', 'phone', 'jobTitle']
        missing_fields = [field for field in required_fields if not self.form_data.get(field)]
        
        if missing_fields:
            return {
                "action": "validation_error",
                "message": f"Please provide: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }
        
        try:
            # Save user data to database
            user_id = db.save_user_data(
                name=self.form_data['name'],
                phone=self.form_data['phone'],
                job_title=self.form_data['jobTitle'],
                session_data={
                    "session_id": self.session_id,
                    "form_data": self.form_data,
                    "submitted_at": str(asyncio.get_event_loop().time())
                }
            )
            
            # Complete form session in database
            db.complete_form_session(self.session_id, user_id)
            
            result = self.form_data.copy()
            result["user_id"] = user_id
            result["session_id"] = self.session_id
            
            self.form_active = False
            self.form_data = {}
            
            return {
                "action": "form_submitted",
                "message": "Form submitted successfully! Thank you for providing your information.",
                "submitted_data": result,
                "user_id": user_id,
                "session_id": self.session_id,
                "database_saved": True
            }
            
        except Exception as e:
            logger.error(f"Database error during form submission: {e}")
            return {
                "action": "error",
                "message": "Form data collected but database error occurred. Please try again.",
                "error_details": str(e)
            }

class VoiceAgentProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.form_tool = FormTool()
        self._websocket = None
    
    def set_websocket(self, ws: WebSocket):
        self._websocket = ws
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            text = frame.text.lower()
            tool_response = None
            if "fill a form" in text or "open form" in text:
                tool_response = self.form_tool.open_form()
            elif "submit" in text and "form" in text:
                tool_response = self.form_tool.submit_form()
            elif "my name is" in text:
                name = text.split("my name is")[-1].strip()
                tool_response = self.form_tool.update_field("name", name)
            elif "my phone" in text or "my number" in text:
                phone = text.split("my phone is")[-1].strip() if "my phone is" in text else text.split("my number is")[-1].strip()
                tool_response = self.form_tool.update_field("phone", phone)
            elif "job title" in text or "work as" in text or "i am a" in text:
                if "job title is" in text:
                    job = text.split("job title is")[-1].strip()
                elif "work as" in text:
                    job = text.split("work as")[-1].strip()
                elif "i am a" in text:
                    job = text.split("i am a")[-1].strip()
                else:
                    job = ""
                if job:
                    tool_response = self.form_tool.update_field("jobTitle", job)
            
            if tool_response and self._websocket:
                try:
                    await self._websocket.send_json({
                        "type": "tool_response",
                        **tool_response
                    })
                except Exception as e:
                    logger.error(f"Error sending tool response: {e}")
        
        await self.push_frame(frame, direction)

class RealTimeVoicePipeline:
    
    def __init__(self):
        self.api_key = API_KEY
        self.pipeline = None
        self.runner = None
        self.processor = VoiceAgentProcessor()
        
    async def create_pipeline(self, websocket: WebSocket) -> Pipeline:
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        self.processor.set_websocket(websocket)

        llm = GeminiLiveLLMService(
            api_key=self.api_key,
            voice_id="Puck",
            model="gemini-2.0-flash-exp",
            tools=[
                {
                    "name": "open_form",
                    "description": "Opens a new form for the user to fill out",
                    "parameters": {"type": "object", "properties": {}}
                },
                {
                    "name": "update_form_field",
                    "description": "Updates a field in the currently open form",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string", "description": "The field name to update"},
                            "value": {"type": "string", "description": "The value to set"}
                        },
                        "required": ["field", "value"]
                    }
                },
                {
                    "name": "submit_form",
                    "description": "Submits the currently open form",
                    "parameters": {"type": "object", "properties": {}}
                }
            ]
        )

        pipeline = Pipeline([
            llm,  
            self.processor,
        ])
        
        return pipeline
    
    async def run_pipeline(self, websocket: WebSocket):
        try:
            logger.info("Starting Voice Agent...")
            pipeline = await self.create_pipeline(websocket)
            task = PipelineTask(pipeline)
            self.runner = PipelineRunner()
            await websocket.send_json({
                "type": "pipeline_ready",
                "message": "Voice pipeline ready! You can start speaking.",
                "latency_target": "< 500ms",
                "features": ["voice_chat", "form_filling", "interruption_handling"]
            })

            await self.runner.run(task)
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            await websocket.send_json({
                "type": "pipeline_error",
                "message": f"Pipeline error: {str(e)}"
            })

def create_pipeline():
    class VoiceAgentPipeline:
        def __init__(self):
            self.api_key = API_KEY
            
        async def run(self, websocket: WebSocket):
            try:
                logger.info("🎤 Voice Agent Pipeline started")
                await self._handle_text_chat(websocket)
                
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                await websocket.close()
        
        async def _handle_text_chat(self, websocket: WebSocket):
            form_tool = FormTool()
            form_tool.open_form()
            
            while True:
                try:
                    message = await websocket.receive_json()
                    msg_type = message.get('type', '')
                    
                    if msg_type == 'connect':
                        welcome_message = "Hello! I'll collect your name, phone number, and job title. Can you please provide your information?"
                        await websocket.send_json({
                            "type": "welcome", 
                            "message": welcome_message,
                            "api_key_loaded": bool(self.api_key),
                            "features": ["voice_recognition", "form_filling", "natural_language"],
                            "commands": [
                                "Tell me your name",
                                "Provide your phone number", 
                                "Share your job title",
                                "Say 'submit' when ready"
                            ]
                        })
                    
                    elif msg_type == 'audio_data':
                        logger.info(f"Received audio data: {len(message.get('data', []))} bytes")
                        
                    elif msg_type == 'chat' or msg_type == 'audio_text':
                        user_message = message.get('message', '')
                        
                        if user_message:
                            ai_response, form_updates = self._process_user_input(user_message, form_tool)
                            await websocket.send_json({
                                "type": "chat_response",
                                "user_message": user_message,
                                "ai_response": ai_response,
                                "timestamp": message.get('timestamp')
                            })

                            for update in form_updates:
                                await websocket.send_json({
                                    "type": "form_update",
                                    **update
                                })
                    
                    elif msg_type == 'form_command':
                        command = message.get('command', '').lower()
                        
                        if command == 'open':
                            response = form_tool.open_form()
                        elif command == 'submit':
                            response = form_tool.submit_form()
                        else:
                            response = {"action": "error", "message": "Unknown form command"}
                        
                        await websocket.send_json({
                            "type": "form_response",
                            **response
                        })
                    
                    elif msg_type == 'form_update':
                        field = message.get('field', '')
                        value = message.get('value', '')
                        response = form_tool.update_field(field, value)
                        
                        await websocket.send_json({
                            "type": "form_response",
                            **response
                        })
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Text chat error: {e}")
                    break
        
        def _process_user_input(self, user_message: str, form_tool: FormTool):
            import re
            
            message = user_message.lower()
            form_updates = []
            ai_response = ""
            
            # Check if all fields are already filled
            all_filled = all(form_tool.form_data.get(field) for field in form_tool.fields)
            
            # Handle submission requests first
            if "submit" in message or "yes" in message or "sure" in message or "confirm" in message:
                if all_filled:
                    result = form_tool.submit_form()
                    ai_response = "Form submitted successfully! Thank you for providing your information."
                    form_updates.append({"action": "form_submitted", "data": result})
                    return ai_response, form_updates
                else:
                    missing = [field for field in form_tool.fields if not form_tool.form_data.get(field)]
                    ai_response = f"Please provide the following information first: {', '.join(missing)}"
                    return ai_response, form_updates
            
            # Process name only if not already captured
            if not form_tool.form_data.get("name"):
                name_patterns = [
                    r"(?:my name is|i am|i'm|call me)\s+([a-zA-Z\s]+?)(?:\.|$|,|\sand)",
                    r"name.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
                    r"^([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)(?:\s|$|\.)",
                    r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\b(?=\s*(?:here|$|\.|,|!|\?))",
                    r"^(?:it's\s+|this\s+is\s+)?([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)$"
                ]
                
                # Special case for very short messages that are likely just names
                words = user_message.strip().split()
                if len(words) <= 3 and not any(word.lower() in ['hello', 'hi', 'hey', 'yes', 'no', 'okay', 'sure', 'phone', 'number', 'job', 'title', 'submit'] for word in words):
                    potential_name = ' '.join(word.capitalize() for word in words if word.isalpha() and len(word) > 1)
                    if potential_name and len(potential_name) > 2:
                        form_tool.update_field("name", potential_name)
                        form_updates.append({"action": "field_updated", "field": "name", "value": potential_name})
                        ai_response = f"Nice to meet you, {potential_name}! Please provide your 11-digit phone number."
                        return ai_response, form_updates
                
                # Regular pattern matching for names
                for pattern in name_patterns:
                    match = re.search(pattern, user_message, re.IGNORECASE)
                    if match:
                        name = match.group(1).strip()
                        name = ' '.join(word.capitalize() for word in name.split() if word.isalpha())
                        if len(name) > 1 and not any(word.lower() in ['hello', 'hi', 'hey', 'phone', 'number', 'job', 'title'] for word in name.split()): 
                            form_tool.update_field("name", name)
                            form_updates.append({"action": "field_updated", "field": "name", "value": name})
                            ai_response = f"Nice to meet you, {name}! Please provide your 11-digit phone number."
                            return ai_response, form_updates
            
            # Process phone only if not already captured and name exists
            elif not form_tool.form_data.get("phone"):
                phone_patterns = [
                    r'(?:phone|number|call)\s*(?:is|:)?\s*([0-9\s\-\(\)\.\+]{11,})',
                    r'([0-9]{11})',  
                    r'([0-9]{1}[-.\\s]?[0-9]{3}[-.\\s]?[0-9]{3}[-.\\s]?[0-9]{4})',  
                    r'(\+?1[-.\\s]?[0-9]{3}[-.\\s]?[0-9]{3}[-.\\s]?[0-9]{4})'
                ]
                
                for pattern in phone_patterns:
                    match = re.search(pattern, user_message, re.IGNORECASE)
                    if match:
                        phone_raw = match.group(1)
                        phone = re.sub(r'[^0-9]', '', phone_raw)
                        if len(phone) == 11:
                            formatted_phone = f"{phone[:5]}-{phone[5:]}"
                            form_tool.update_field("phone", formatted_phone)
                            form_updates.append({"action": "field_updated", "field": "phone", "value": formatted_phone})
                            ai_response = "Great! Now, what's your job title?"
                            return ai_response, form_updates
            
            # Process job title only if not already captured and name + phone exist
            elif not form_tool.form_data.get("jobTitle"):
                job_patterns = [
                    r"(?:job title is|work as|i am a|my job is|position is)\s+([a-zA-Z\s]+?)(?:\.|$|,|\sand)",
                    r"(?:engineer|developer|manager|analyst|designer|consultant|specialist|coordinator|director|lead)\b([a-zA-Z\s]*)",
                    r"([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(?:engineer|developer|manager|analyst)",
                    r"(AI|ML|Data|Software|Web|Mobile|Full[\s-]?Stack|DevOps|Cloud)\s+[A-Za-z]+"
                ]
                
                for pattern in job_patterns:
                    match = re.search(pattern, user_message, re.IGNORECASE)
                    if match:
                        job_title = match.group(0 if "engineer" in pattern or "AI|ML" in pattern else 1).strip()
                        if len(job_title) > 1:  
                            job_title = ' '.join(word.capitalize() for word in job_title.split())
                            form_tool.update_field("jobTitle", job_title)
                            form_updates.append({"action": "field_updated", "field": "jobTitle", "value": job_title})
                            ai_response = "Perfect! I've collected all your information. Would you like to submit the form?"
                            return ai_response, form_updates
            
            # Default responses only if no field was updated
            if not ai_response:
                if "hello" in message or "hi" in message:
                    if not form_tool.form_data.get("name"):
                        ai_response = "Hello! Could you please tell me your name?"
                    elif not form_tool.form_data.get("phone"):
                        ai_response = "Please provide your phone number."
                    elif not form_tool.form_data.get("jobTitle"):
                        ai_response = "What's your job title?"
                    else:
                        ai_response = "I have all your information. Would you like to submit the form?"
                elif not form_tool.form_data.get("name"):
                    ai_response = "Could you please tell me your name?"
                elif not form_tool.form_data.get("phone"):
                    ai_response = "Please provide your phone number."
                elif not form_tool.form_data.get("jobTitle"):
                    ai_response = "What's your job title?"
                else:
                    ai_response = "I have all your information. Would you like to submit the form?"
            
            return ai_response, form_updates
    
    return VoiceAgentPipeline()