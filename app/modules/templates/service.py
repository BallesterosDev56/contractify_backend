"""Templates module - Business logic service with static data."""

from typing import Any, Dict, List, Optional

from app.shared.exceptions import NotFoundException

from .schemas import ContractFormSchema, ContractTemplate, ContractType, FormField

# Static template data - In production, this would come from database or external storage
TEMPLATES: List[ContractTemplate] = [
    ContractTemplate(
        id="tpl_arrendamiento_v1",
        name="Contrato de Arrendamiento de Vivienda",
        description="Contrato estándar para arrendamiento de vivienda urbana en Colombia",
        category="inmobiliario",
        jurisdiction="CO",
        variables=["arrendador_nombre", "arrendatario_nombre", "direccion", "canon_mensual", "duracion_meses"],
    ),
    ContractTemplate(
        id="tpl_prestacion_servicios_v1",
        name="Contrato de Prestación de Servicios",
        description="Contrato para prestación de servicios profesionales independientes",
        category="laboral",
        jurisdiction="CO",
        variables=["contratante_nombre", "contratista_nombre", "objeto", "valor", "duracion"],
    ),
    ContractTemplate(
        id="tpl_compraventa_v1",
        name="Contrato de Compraventa",
        description="Contrato de compraventa de bienes muebles o inmuebles",
        category="comercial",
        jurisdiction="CO",
        variables=["vendedor_nombre", "comprador_nombre", "bien", "precio", "forma_pago"],
    ),
    ContractTemplate(
        id="tpl_confidencialidad_v1",
        name="Acuerdo de Confidencialidad (NDA)",
        description="Acuerdo de no divulgación de información confidencial",
        category="comercial",
        jurisdiction="CO",
        variables=["parte_reveladora", "parte_receptora", "objeto_confidencial", "duracion"],
    ),
    ContractTemplate(
        id="tpl_trabajo_v1",
        name="Contrato de Trabajo",
        description="Contrato laboral a término fijo o indefinido",
        category="laboral",
        jurisdiction="CO",
        variables=["empleador_nombre", "empleado_nombre", "cargo", "salario", "tipo_contrato"],
    ),
]

CONTRACT_TYPES: List[ContractType] = [
    ContractType(
        id="ARRENDAMIENTO_VIVIENDA",
        name="Arrendamiento de Vivienda",
        description="Contratos para alquiler de inmuebles residenciales",
        category="inmobiliario",
        icon="home",
    ),
    ContractType(
        id="PRESTACION_SERVICIOS",
        name="Prestación de Servicios",
        description="Contratos para servicios profesionales independientes",
        category="laboral",
        icon="briefcase",
    ),
    ContractType(
        id="COMPRAVENTA",
        name="Compraventa",
        description="Contratos para compra y venta de bienes",
        category="comercial",
        icon="shopping-cart",
    ),
    ContractType(
        id="NDA",
        name="Confidencialidad (NDA)",
        description="Acuerdos de no divulgación",
        category="comercial",
        icon="lock",
    ),
    ContractType(
        id="TRABAJO",
        name="Contrato de Trabajo",
        description="Contratos laborales formales",
        category="laboral",
        icon="users",
    ),
]

# Form schemas per contract type
TYPE_SCHEMAS: Dict[str, ContractFormSchema] = {
    "ARRENDAMIENTO_VIVIENDA": ContractFormSchema(
        type="object",
        properties={
            "arrendador_nombre": {"type": "string", "title": "Nombre del Arrendador"},
            "arrendador_cedula": {"type": "string", "title": "Cédula del Arrendador"},
            "arrendatario_nombre": {"type": "string", "title": "Nombre del Arrendatario"},
            "arrendatario_cedula": {"type": "string", "title": "Cédula del Arrendatario"},
            "direccion": {"type": "string", "title": "Dirección del Inmueble"},
            "ciudad": {"type": "string", "title": "Ciudad"},
            "canon_mensual": {"type": "number", "title": "Canon Mensual (COP)"},
            "duracion_meses": {"type": "integer", "title": "Duración (meses)"},
            "fecha_inicio": {"type": "string", "format": "date", "title": "Fecha de Inicio"},
        },
        required=["arrendador_nombre", "arrendatario_nombre", "direccion", "canon_mensual", "duracion_meses"],
        fields=[
            FormField(name="arrendador_nombre", label="Nombre del Arrendador", type="text", required=True),
            FormField(name="arrendador_cedula", label="Cédula del Arrendador", type="text", required=True),
            FormField(name="arrendatario_nombre", label="Nombre del Arrendatario", type="text", required=True),
            FormField(name="arrendatario_cedula", label="Cédula del Arrendatario", type="text", required=True),
            FormField(name="direccion", label="Dirección del Inmueble", type="textarea", required=True),
            FormField(name="ciudad", label="Ciudad", type="text", required=True),
            FormField(name="canon_mensual", label="Canon Mensual (COP)", type="number", required=True),
            FormField(name="duracion_meses", label="Duración (meses)", type="number", required=True),
            FormField(name="fecha_inicio", label="Fecha de Inicio", type="date", required=True),
        ],
    ),
    "PRESTACION_SERVICIOS": ContractFormSchema(
        type="object",
        properties={
            "contratante_nombre": {"type": "string", "title": "Nombre del Contratante"},
            "contratante_nit": {"type": "string", "title": "NIT/Cédula del Contratante"},
            "contratista_nombre": {"type": "string", "title": "Nombre del Contratista"},
            "contratista_cedula": {"type": "string", "title": "Cédula del Contratista"},
            "objeto": {"type": "string", "title": "Objeto del Contrato"},
            "valor": {"type": "number", "title": "Valor del Contrato (COP)"},
            "duracion": {"type": "string", "title": "Duración"},
            "fecha_inicio": {"type": "string", "format": "date", "title": "Fecha de Inicio"},
        },
        required=["contratante_nombre", "contratista_nombre", "objeto", "valor"],
        fields=[
            FormField(name="contratante_nombre", label="Nombre del Contratante", type="text", required=True),
            FormField(name="contratante_nit", label="NIT/Cédula del Contratante", type="text", required=True),
            FormField(name="contratista_nombre", label="Nombre del Contratista", type="text", required=True),
            FormField(name="contratista_cedula", label="Cédula del Contratista", type="text", required=True),
            FormField(name="objeto", label="Objeto del Contrato", type="textarea", required=True),
            FormField(name="valor", label="Valor del Contrato (COP)", type="number", required=True),
            FormField(name="duracion", label="Duración", type="text", required=True),
            FormField(name="fecha_inicio", label="Fecha de Inicio", type="date", required=True),
        ],
    ),
    "COMPRAVENTA": ContractFormSchema(
        type="object",
        properties={
            "vendedor_nombre": {"type": "string", "title": "Nombre del Vendedor"},
            "vendedor_cedula": {"type": "string", "title": "Cédula del Vendedor"},
            "comprador_nombre": {"type": "string", "title": "Nombre del Comprador"},
            "comprador_cedula": {"type": "string", "title": "Cédula del Comprador"},
            "bien": {"type": "string", "title": "Descripción del Bien"},
            "precio": {"type": "number", "title": "Precio (COP)"},
            "forma_pago": {"type": "string", "title": "Forma de Pago"},
        },
        required=["vendedor_nombre", "comprador_nombre", "bien", "precio"],
        fields=[
            FormField(name="vendedor_nombre", label="Nombre del Vendedor", type="text", required=True),
            FormField(name="vendedor_cedula", label="Cédula del Vendedor", type="text", required=True),
            FormField(name="comprador_nombre", label="Nombre del Comprador", type="text", required=True),
            FormField(name="comprador_cedula", label="Cédula del Comprador", type="text", required=True),
            FormField(name="bien", label="Descripción del Bien", type="textarea", required=True),
            FormField(name="precio", label="Precio (COP)", type="number", required=True),
            FormField(name="forma_pago", label="Forma de Pago", type="text", required=True),
        ],
    ),
    "NDA": ContractFormSchema(
        type="object",
        properties={
            "parte_reveladora": {"type": "string", "title": "Parte Reveladora"},
            "parte_receptora": {"type": "string", "title": "Parte Receptora"},
            "objeto_confidencial": {"type": "string", "title": "Información Confidencial"},
            "duracion": {"type": "string", "title": "Duración de la Confidencialidad"},
        },
        required=["parte_reveladora", "parte_receptora", "objeto_confidencial"],
        fields=[
            FormField(name="parte_reveladora", label="Parte Reveladora", type="text", required=True),
            FormField(name="parte_receptora", label="Parte Receptora", type="text", required=True),
            FormField(name="objeto_confidencial", label="Información Confidencial", type="textarea", required=True),
            FormField(name="duracion", label="Duración de la Confidencialidad", type="text", required=True),
        ],
    ),
    "TRABAJO": ContractFormSchema(
        type="object",
        properties={
            "empleador_nombre": {"type": "string", "title": "Nombre del Empleador"},
            "empleador_nit": {"type": "string", "title": "NIT del Empleador"},
            "empleado_nombre": {"type": "string", "title": "Nombre del Empleado"},
            "empleado_cedula": {"type": "string", "title": "Cédula del Empleado"},
            "cargo": {"type": "string", "title": "Cargo"},
            "salario": {"type": "number", "title": "Salario Mensual (COP)"},
            "tipo_contrato": {"type": "string", "enum": ["INDEFINIDO", "FIJO", "OBRA_LABOR"], "title": "Tipo de Contrato"},
            "fecha_inicio": {"type": "string", "format": "date", "title": "Fecha de Inicio"},
        },
        required=["empleador_nombre", "empleado_nombre", "cargo", "salario", "tipo_contrato"],
        fields=[
            FormField(name="empleador_nombre", label="Nombre del Empleador", type="text", required=True),
            FormField(name="empleador_nit", label="NIT del Empleador", type="text", required=True),
            FormField(name="empleado_nombre", label="Nombre del Empleado", type="text", required=True),
            FormField(name="empleado_cedula", label="Cédula del Empleado", type="text", required=True),
            FormField(name="cargo", label="Cargo", type="text", required=True),
            FormField(name="salario", label="Salario Mensual (COP)", type="number", required=True),
            FormField(
                name="tipo_contrato",
                label="Tipo de Contrato",
                type="select",
                required=True,
                options=[
                    {"value": "INDEFINIDO", "label": "Indefinido"},
                    {"value": "FIJO", "label": "Término Fijo"},
                    {"value": "OBRA_LABOR", "label": "Obra o Labor"},
                ],
            ),
            FormField(name="fecha_inicio", label="Fecha de Inicio", type="date", required=True),
        ],
    ),
}


class TemplateService:
    """Service for template operations."""

    def get_templates(
        self,
        category: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> List[ContractTemplate]:
        """Get available templates with optional filters."""
        templates = TEMPLATES.copy()

        if category:
            templates = [t for t in templates if t.category == category]
        if jurisdiction:
            templates = [t for t in templates if t.jurisdiction == jurisdiction]

        return templates

    def get_template(self, template_id: str) -> ContractTemplate:
        """Get template by ID."""
        for template in TEMPLATES:
            if template.id == template_id:
                return template
        raise NotFoundException(f"Template {template_id} not found")

    def get_types(self) -> List[ContractType]:
        """Get available contract types."""
        return CONTRACT_TYPES.copy()

    def get_type_schema(self, type_id: str) -> ContractFormSchema:
        """Get form schema for contract type."""
        schema = TYPE_SCHEMAS.get(type_id)
        if not schema:
            raise NotFoundException(f"Schema for type {type_id} not found")
        return schema
