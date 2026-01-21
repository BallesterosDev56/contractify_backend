"""Templates module - API routes matching OpenAPI spec."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Depends

from .schemas import ContractFormSchema, ContractTemplate, ContractType
from .service import TemplateService

router = APIRouter(tags=["Templates"])


def get_service() -> TemplateService:
    """Get template service instance."""
    return TemplateService()


@router.get("/contracts/templates", response_model=List[ContractTemplate])
async def list_templates(
    category: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    service: TemplateService = Depends(get_service),
) -> List[ContractTemplate]:
    """
    List available contract templates.

    GET /contracts/templates
    """
    return service.get_templates(category=category, jurisdiction=jurisdiction)


@router.get("/contracts/templates/{templateId}", response_model=ContractTemplate)
async def get_template(
    templateId: str,
    service: TemplateService = Depends(get_service),
) -> ContractTemplate:
    """
    Get template details.

    GET /contracts/templates/{templateId}
    """
    return service.get_template(templateId)


@router.get("/contracts/types", response_model=List[ContractType])
async def list_contract_types(
    service: TemplateService = Depends(get_service),
) -> List[ContractType]:
    """
    Get available contract types (for UI selection).

    GET /contracts/types
    """
    return service.get_types()


@router.get("/contracts/types/{type}/schema")
async def get_type_schema(
    type: str,
    service: TemplateService = Depends(get_service),
) -> Dict[str, Any]:
    """
    Get form schema for contract type.

    GET /contracts/types/{type}/schema
    """
    schema = service.get_type_schema(type)
    return schema.model_dump()
