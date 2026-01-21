"""Templates module - Pydantic schemas matching OpenAPI spec."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ContractTemplate(BaseModel):
    """Contract template - matches OpenAPI ContractTemplate."""

    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    jurisdiction: Optional[str] = None
    docxTemplateUrl: Optional[str] = None
    previewImageUrl: Optional[str] = None
    variables: List[str] = []


class ContractType(BaseModel):
    """Contract type - matches OpenAPI ContractType."""

    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None


class FormFieldOption(BaseModel):
    """Form field option."""

    value: str
    label: str


class FormField(BaseModel):
    """Form field definition."""

    name: str
    label: str
    type: str  # text, email, number, date, select, textarea, checkbox
    placeholder: Optional[str] = None
    options: Optional[List[FormFieldOption]] = None
    required: bool = False
    validation: Optional[Dict[str, Any]] = None


class ContractFormSchema(BaseModel):
    """Contract form schema - JSON Schema for form."""

    type: str = "object"
    properties: Dict[str, Any] = {}
    required: List[str] = []
    # Additional fields for UI rendering
    fields: Optional[List[FormField]] = None
