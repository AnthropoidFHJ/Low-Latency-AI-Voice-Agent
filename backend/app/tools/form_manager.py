import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
logger = logging.getLogger(__name__)
class FormStatus(Enum):
    DRAFT = "draft"
    OPEN = "open"
    VALIDATING = "validating"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    ERROR = "error"
@dataclass
class FormField:
    name: str
    value: Optional[str] = None
    field_type: str = "text"
    required: bool = False
    validation_pattern: Optional[str] = None
    error_message: Optional[str] = None
    is_valid: bool = True
@dataclass
class Form:
    form_id: str
    form_type: str
    title: str
    fields: Dict[str, FormField] = field(default_factory=dict)
    status: FormStatus = FormStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
class FormManager:
    def __init__(self):
        self.current_form: Optional[Form] = None
        self.form_templates = self._initialize_form_templates()
        self.stats = {
            "forms_created": 0,
            "fields_filled": 0,
            "forms_submitted": 0,
            "validation_errors": 0,
            "avg_completion_time_ms": 0,
        }
    def _initialize_form_templates(self) -> Dict[str, Dict[str, FormField]]:
        return {
            "contact": {
                "name": FormField("name", field_type="text", required=True),
                "email": FormField("email", field_type="email", required=True,
                                 validation_pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
                "phone": FormField("phone", field_type="tel", required=False,
                                 validation_pattern=r'^\+?[\d\s\-\(\)]{10,}$'),
                "message": FormField("message", field_type="textarea", required=True),
            },
            "registration": {
                "first_name": FormField("first_name", field_type="text", required=True),
                "last_name": FormField("last_name", field_type="text", required=True),
                "email": FormField("email", field_type="email", required=True,
                                 validation_pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
                "age": FormField("age", field_type="number", required=True,
                               validation_pattern=r'^\d{1,3}$'),
                "company": FormField("company", field_type="text", required=False),
            },
            "feedback": {
                "name": FormField("name", field_type="text", required=False),
                "email": FormField("email", field_type="email", required=False,
                                 validation_pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
                "rating": FormField("rating", field_type="number", required=True,
                                  validation_pattern=r'^[1-5]$'),
                "feedback": FormField("feedback", field_type="textarea", required=True),
                "recommend": FormField("recommend", field_type="boolean", required=False),
            },
            "survey": {
                "participant_id": FormField("participant_id", field_type="text", required=True),
                "age_range": FormField("age_range", field_type="select", required=True),
                "experience_level": FormField("experience_level", field_type="select", required=True),
                "satisfaction": FormField("satisfaction", field_type="number", required=True,
                                        validation_pattern=r'^[1-10]$'),
                "comments": FormField("comments", field_type="textarea", required=False),
            }
        }
    async def open_form(self, form_type: str, title: str = "") -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        try:
            if form_type not in self.form_templates:
                available_types = list(self.form_templates.keys())
                return {
                    "success": False,
                    "error": f"Unknown form type '{form_type}'. Available types: {available_types}",
                    "available_types": available_types
                }
            form_id = f"{form_type}_{int(datetime.utcnow().timestamp()*1000)}"
            display_title = title or f"{form_type.title()} Form"
            template_fields = self.form_templates[form_type]
            form_fields = {
                name: FormField(
                    name=field.name,
                    field_type=field.field_type,
                    required=field.required,
                    validation_pattern=field.validation_pattern
                )
                for name, field in template_fields.items()
            }
            self.current_form = Form(
                form_id=form_id,
                form_type=form_type,
                title=display_title,
                fields=form_fields,
                status=FormStatus.OPEN
            )
            self.stats["forms_created"] += 1
            response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.info(f"Form opened: {form_id} ({response_time_ms:.2f}ms)")
            return {
                "success": True,
                "form_id": form_id,
                "form_type": form_type,
                "title": display_title,
                "fields": [
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "required": field.required,
                        "filled": field.value is not None
                    }
                    for field in form_fields.values()
                ],
                "response_time_ms": round(response_time_ms, 2),
                "message": f"I've opened a {form_type} form for you. You can now fill the fields by saying things like 'My name is John Smith' or 'Set email to john@example.com'."
            }
        except Exception as e:
            logger.error(f"Error opening form: {e}")
            return {
                "success": False,
                "error": f"Failed to open form: {str(e)}"
            }
    async def fill_field(self, field_name: str, value: str) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        try:
            if not self.current_form:
                return {
                    "success": False,
                    "error": "No form is currently open. Please open a form first."
                }
            normalized_field_name = self._normalize_field_name(field_name)
            if normalized_field_name not in self.current_form.fields:
                available_fields = list(self.current_form.fields.keys())
                return {
                    "success": False,
                    "error": f"Field '{field_name}' not found. Available fields: {available_fields}",
                    "available_fields": available_fields
                }
            field = self.current_form.fields[normalized_field_name]
            processed_value = self._process_field_value(field, value)
            validation_result = self._validate_field_value(field, processed_value)
            if not validation_result["is_valid"]:
                self.stats["validation_errors"] += 1
                return {
                    "success": False,
                    "error": validation_result["error_message"],
                    "field_name": field_name,
                    "field_type": field.field_type
                }
            field.value = processed_value
            field.is_valid = True
            field.error_message = None
            self.current_form.updated_at = datetime.utcnow()
            self.stats["fields_filled"] += 1
            response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.debug(f"Field filled: {normalized_field_name} = {processed_value} ({response_time_ms:.2f}ms)")
            return {
                "success": True,
                "field_name": normalized_field_name,
                "value": processed_value,
                "field_type": field.field_type,
                "response_time_ms": round(response_time_ms, 2),
                "message": f"I've set {field_name} to '{processed_value}'. {self._get_next_field_suggestion()}"
            }
        except Exception as e:
            logger.error(f"Error filling field: {e}")
            return {
                "success": False,
                "error": f"Failed to fill field: {str(e)}"
            }
    async def validate_form(self) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        try:
            if not self.current_form:
                return {
                    "success": False,
                    "error": "No form is currently open."
                }
            validation_errors = []
            missing_required_fields = []
            filled_fields = 0
            total_fields = len(self.current_form.fields)
            for field_name, field in self.current_form.fields.items():
                if field.required and (field.value is None or field.value.strip() == ""):
                    missing_required_fields.append(field_name)
                elif field.value is not None:
                    filled_fields += 1
                    validation_result = self._validate_field_value(field, field.value)
                    if not validation_result["is_valid"]:
                        validation_errors.append({
                            "field": field_name,
                            "error": validation_result["error_message"]
                        })
            completion_percentage = (filled_fields / total_fields) * 100
            is_complete = len(missing_required_fields) == 0 and len(validation_errors) == 0
            if is_complete:
                self.current_form.status = FormStatus.COMPLETED
            elif validation_errors:
                self.current_form.status = FormStatus.ERROR
            else:
                self.current_form.status = FormStatus.VALIDATING
            response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            result = {
                "success": True,
                "is_valid": is_complete,
                "completion_percentage": round(completion_percentage, 1),
                "filled_fields": filled_fields,
                "total_fields": total_fields,
                "missing_required_fields": missing_required_fields,
                "validation_errors": validation_errors,
                "response_time_ms": round(response_time_ms, 2)
            }
            if is_complete:
                result["message"] = "Form is complete and valid! You can now submit it."
            elif missing_required_fields:
                result["message"] = f"Please fill the required fields: {', '.join(missing_required_fields)}"
            elif validation_errors:
                result["message"] = f"Please fix validation errors in: {', '.join([e['field'] for e in validation_errors])}"
            else:
                result["message"] = f"Form is {completion_percentage:.0f}% complete."
            return result
        except Exception as e:
            logger.error(f"Error validating form: {e}")
            return {
                "success": False,
                "error": f"Failed to validate form: {str(e)}"
            }
    async def submit_form(self, confirm: bool = True) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        try:
            if not self.current_form:
                return {
                    "success": False,
                    "error": "No form is currently open."
                }
            if not confirm:
                return {
                    "success": False,
                    "error": "Form submission cancelled by user."
                }
            validation_result = await self.validate_form()
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "error": "Form validation failed. Please fix errors before submitting.",
                    "validation_details": validation_result
                }
            form_data = {
                "form_id": self.current_form.form_id,
                "form_type": self.current_form.form_type,
                "title": self.current_form.title,
                "fields": {
                    name: {
                        "value": field.value,
                        "type": field.field_type
                    }
                    for name, field in self.current_form.fields.items()
                    if field.value is not None
                },
                "submitted_at": datetime.utcnow().isoformat(),
                "completion_time_ms": (datetime.utcnow() - self.current_form.created_at).total_seconds() * 1000
            }
            await asyncio.sleep(0.1)
            self.current_form.status = FormStatus.SUBMITTED
            self.stats["forms_submitted"] += 1
            completion_time = (datetime.utcnow() - self.current_form.created_at).total_seconds() * 1000
            self.stats["avg_completion_time_ms"] = (
                (self.stats["avg_completion_time_ms"] + completion_time) / 2
                if self.stats["avg_completion_time_ms"] > 0
                else completion_time
            )
            response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.info(f"Form submitted: {self.current_form.form_id} ({response_time_ms:.2f}ms)")
            submitted_form_id = self.current_form.form_id
            self.current_form = None
            return {
                "success": True,
                "form_id": submitted_form_id,
                "form_data": form_data,
                "response_time_ms": round(response_time_ms, 2),
                "message": "Form submitted successfully! Thank you for providing the information."
            }
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return {
                "success": False,
                "error": f"Failed to submit form: {str(e)}"
            }
    def _normalize_field_name(self, field_name: str) -> str:
        field_name_lower = field_name.lower().strip()
        mappings = {
            "full name": "name",
            "your name": "name",
            "first": "first_name",
            "last": "last_name",
            "surname": "last_name",
            "family name": "last_name",
            "e-mail": "email",
            "email address": "email",
            "phone number": "phone",
            "telephone": "phone",
            "mobile": "phone",
            "age range": "age_range",
            "how old": "age",
            "company name": "company",
            "organization": "company",
            "comments": "message",
            "feedback": "message",
            "rating": "rating",
            "score": "rating",
            "recommend": "recommend",
            "recommendation": "recommend",
        }
        return mappings.get(field_name_lower, field_name_lower.replace(" ", "_"))
    def _process_field_value(self, field: FormField, value: str) -> str:
        value = value.strip()
        if field.field_type == "email":
            return value.lower()
        elif field.field_type == "boolean":
            return str(value.lower() in ["yes", "true", "1", "positive", "definitely", "sure", "absolutely"]).lower()
        elif field.field_type == "number":
            import re
            numbers = re.findall(r'\d+', value)
            return numbers[0] if numbers else value
        elif field.field_type == "tel":
            import re
            return re.sub(r'[^\d\+\-\(\)\s]', '', value)
        else:
            return value
    def _validate_field_value(self, field: FormField, value: str) -> Dict[str, Any]:
        if field.validation_pattern:
            import re
            if not re.match(field.validation_pattern, value):
                return {
                    "is_valid": False,
                    "error_message": f"Invalid format for {field.name}. Please check your input."
                }
        return {"is_valid": True}
    def _get_next_field_suggestion(self) -> str:
        if not self.current_form:
            return ""
        for field_name, field in self.current_form.fields.items():
            if field.required and (field.value is None or field.value.strip() == ""):
                return f"Next, please provide your {field_name.replace('_', ' ')}."
        for field_name, field in self.current_form.fields.items():
            if field.value is None or field.value.strip() == "":
                return f"You can also add your {field_name.replace('_', ' ')} if you'd like."
        return "All fields are filled! You can validate or submit the form now."
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "current_form_id": self.current_form.form_id if self.current_form else None,
            "current_form_status": self.current_form.status.value if self.current_form else None,
        }
class FormTool:
    def __init__(self, form_manager: FormManager):
        self.form_manager = form_manager
    async def execute(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if function_name == "open_form":
            return await self.form_manager.open_form(**arguments)
        elif function_name == "fill_form_field":
            return await self.form_manager.fill_field(**arguments)
        elif function_name == "validate_form":
            return await self.form_manager.validate_form()
        elif function_name == "submit_form":
            return await self.form_manager.submit_form(**arguments)
        else:
            return {"success": False, "error": f"Unknown function: {function_name}"}