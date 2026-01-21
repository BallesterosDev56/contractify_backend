"""AI module - Business logic service with mock AI generation."""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.config import settings
from app.shared.exceptions import BadRequestException, NotFoundException

from .models import AsyncJob
from .repository import AICacheRepository, AsyncJobRepository
from .schemas import (
    AIGenerateMetadata,
    AIGenerateRequest,
    AIGenerateResponse,
    AIRegenerateRequest,
    AsyncJobResponse,
    AsyncJobStatus,
    JobStatus,
    ValidateInputRequest,
    ValidateInputResponse,
)

# Contract templates for mock generation
MOCK_TEMPLATES = {
    "ARRENDAMIENTO_VIVIENDA": """
<h1>CONTRATO DE ARRENDAMIENTO DE VIVIENDA URBANA</h1>

<p>Entre <strong>{arrendador_nombre}</strong>, identificado con cédula <strong>{arrendador_cedula}</strong>,
quien en adelante se denominará EL ARRENDADOR, y <strong>{arrendatario_nombre}</strong>,
identificado con cédula <strong>{arrendatario_cedula}</strong>, quien en adelante se denominará EL ARRENDATARIO,
se celebra el presente contrato de arrendamiento de vivienda urbana, regido por la Ley 820 de 2003.</p>

<h2>PRIMERA - OBJETO</h2>
<p>EL ARRENDADOR entrega en arrendamiento a EL ARRENDATARIO el inmueble ubicado en
<strong>{direccion}</strong>, en la ciudad de <strong>{ciudad}</strong>.</p>

<h2>SEGUNDA - CANON</h2>
<p>El canon mensual de arrendamiento es de <strong>${canon_mensual:,.0f} COP</strong>,
pagadero dentro de los primeros cinco (5) días de cada mes.</p>

<h2>TERCERA - DURACIÓN</h2>
<p>El presente contrato tiene una duración de <strong>{duracion_meses} meses</strong>,
contados a partir del <strong>{fecha_inicio}</strong>.</p>

<h2>CUARTA - OBLIGACIONES DEL ARRENDATARIO</h2>
<ol>
<li>Pagar el canon de arrendamiento en las fechas estipuladas.</li>
<li>Conservar el inmueble en buen estado.</li>
<li>No subarrendar ni ceder el contrato sin autorización escrita.</li>
<li>Pagar los servicios públicos durante la vigencia del contrato.</li>
</ol>

<h2>QUINTA - OBLIGACIONES DEL ARRENDADOR</h2>
<ol>
<li>Entregar el inmueble en condiciones de habitabilidad.</li>
<li>Mantener el inmueble en estado de servir para su uso.</li>
<li>Realizar las reparaciones locativas necesarias.</li>
</ol>

<p>Para constancia se firma en la ciudad de <strong>{ciudad}</strong>.</p>

<div class="signatures">
<div class="signature-block">
<p>_____________________________</p>
<p><strong>EL ARRENDADOR</strong></p>
<p>{arrendador_nombre}</p>
<p>C.C. {arrendador_cedula}</p>
</div>
<div class="signature-block">
<p>_____________________________</p>
<p><strong>EL ARRENDATARIO</strong></p>
<p>{arrendatario_nombre}</p>
<p>C.C. {arrendatario_cedula}</p>
</div>
</div>
""",
    "PRESTACION_SERVICIOS": """
<h1>CONTRATO DE PRESTACIÓN DE SERVICIOS PROFESIONALES</h1>

<p>Entre <strong>{contratante_nombre}</strong>, identificado con NIT/C.C. <strong>{contratante_nit}</strong>,
quien en adelante se denominará EL CONTRATANTE, y <strong>{contratista_nombre}</strong>,
identificado con cédula <strong>{contratista_cedula}</strong>, quien en adelante se denominará EL CONTRATISTA,
se celebra el presente contrato de prestación de servicios.</p>

<h2>PRIMERA - OBJETO</h2>
<p>{objeto}</p>

<h2>SEGUNDA - VALOR</h2>
<p>El valor total del contrato es de <strong>${valor:,.0f} COP</strong>.</p>

<h2>TERCERA - DURACIÓN</h2>
<p>El presente contrato tiene una duración de <strong>{duracion}</strong>,
a partir del <strong>{fecha_inicio}</strong>.</p>

<h2>CUARTA - INDEPENDENCIA</h2>
<p>EL CONTRATISTA actuará por su propia cuenta, con autonomía técnica y administrativa.</p>

<p>Para constancia se firma.</p>

<div class="signatures">
<div class="signature-block">
<p>_____________________________</p>
<p><strong>EL CONTRATANTE</strong></p>
<p>{contratante_nombre}</p>
</div>
<div class="signature-block">
<p>_____________________________</p>
<p><strong>EL CONTRATISTA</strong></p>
<p>{contratista_nombre}</p>
</div>
</div>
""",
    "NDA": """
<h1>ACUERDO DE CONFIDENCIALIDAD</h1>

<p>Entre <strong>{parte_reveladora}</strong> (Parte Reveladora) y <strong>{parte_receptora}</strong>
(Parte Receptora), se celebra el presente Acuerdo de Confidencialidad.</p>

<h2>1. INFORMACIÓN CONFIDENCIAL</h2>
<p>{objeto_confidencial}</p>

<h2>2. OBLIGACIONES</h2>
<p>La Parte Receptora se obliga a:</p>
<ul>
<li>Mantener en estricta confidencialidad la información recibida.</li>
<li>No divulgar la información a terceros.</li>
<li>Usar la información únicamente para el propósito acordado.</li>
</ul>

<h2>3. DURACIÓN</h2>
<p>Este acuerdo tendrá vigencia de <strong>{duracion}</strong>.</p>

<div class="signatures">
<div class="signature-block">
<p>_____________________________</p>
<p><strong>PARTE REVELADORA</strong></p>
<p>{parte_reveladora}</p>
</div>
<div class="signature-block">
<p>_____________________________</p>
<p><strong>PARTE RECEPTORA</strong></p>
<p>{parte_receptora}</p>
</div>
</div>
""",
}

# Default template for unknown contract types
DEFAULT_TEMPLATE = """
<h1>CONTRATO</h1>

<p>Se celebra el presente contrato con los siguientes términos y condiciones:</p>

<h2>CLÁUSULAS</h2>
<p>Las partes acuerdan los términos especificados en este documento.</p>

<div class="signatures">
<p>Para constancia se firma.</p>
</div>
"""


class AIService:
    """Service for AI-powered contract generation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_repo = AsyncJobRepository(db)
        self.cache_repo = AICacheRepository(db)

    def _generate_cache_key(self, contract_type: str, inputs: Dict[str, Any]) -> str:
        """Generate cache key from inputs."""
        data = f"{contract_type}:{sorted(inputs.items())}"
        return hashlib.md5(data.encode()).hexdigest()

    def _fill_template(self, template: str, inputs: Dict[str, Any]) -> str:
        """Fill template with input values."""
        content = template
        for key, value in inputs.items():
            # Handle numeric formatting
            if isinstance(value, (int, float)):
                content = content.replace(f"{{{key}:,.0f}}", f"{value:,.0f}")
            content = content.replace(f"{{{key}}}", str(value))
        return content

    def _generate_content(
        self,
        contract_type: str,
        inputs: Dict[str, Any],
    ) -> str:
        """Generate contract content (mock implementation)."""
        template = MOCK_TEMPLATES.get(contract_type, DEFAULT_TEMPLATE)
        return self._fill_template(template, inputs)

    async def validate_input(
        self,
        data: ValidateInputRequest,
    ) -> ValidateInputResponse:
        """Validate form inputs before generation."""
        errors: List[str] = []
        warnings: List[str] = []

        # Basic validation
        if not data.inputs:
            errors.append("No inputs provided")

        # Check for empty required fields (contract type specific)
        required_fields = {
            "ARRENDAMIENTO_VIVIENDA": ["arrendador_nombre", "arrendatario_nombre", "direccion", "canon_mensual"],
            "PRESTACION_SERVICIOS": ["contratante_nombre", "contratista_nombre", "objeto", "valor"],
            "NDA": ["parte_reveladora", "parte_receptora", "objeto_confidencial"],
        }

        type_required = required_fields.get(data.contractType, [])
        for field in type_required:
            if field not in data.inputs or not data.inputs[field]:
                errors.append(f"Campo requerido: {field}")

        # Warnings
        if "fecha_inicio" not in data.inputs:
            warnings.append("Se recomienda especificar fecha de inicio")

        return ValidateInputResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    async def generate_contract(
        self,
        current_user: CurrentUser,
        data: AIGenerateRequest,
    ) -> AIGenerateResponse:
        """
        Generate contract content using AI (mock implementation).

        In production, this would call OpenAI API with RAG context.
        """
        # Check cache first
        cache_key = self._generate_cache_key(data.contractType, data.inputs)
        cached = await self.cache_repo.get(cache_key)
        if cached:
            return AIGenerateResponse(
                content=cached.content,
                placeholders={},
                metadata_=AIGenerateMetadata(
                    model="cache",
                    promptVersion="v1",
                    confidenceScore=1.0,
                ),
            )

        # Generate content
        content = self._generate_content(data.contractType, data.inputs)

        # Cache the result
        await self.cache_repo.set(cache_key, content, {"contractType": data.contractType})

        return AIGenerateResponse(
            content=content,
            placeholders={},
            metadata_=AIGenerateMetadata(
                model="mock-gpt-4",
                promptVersion="v1.0",
                confidenceScore=0.95,
            ),
        )

    async def generate_contract_async(
        self,
        current_user: CurrentUser,
        data: AIGenerateRequest,
    ) -> AsyncJobResponse:
        """
        Start async contract generation.

        Returns job ID for polling.
        """
        # Create job
        job = await self.job_repo.create(
            job_type="AI_GENERATE",
            user_id=current_user.id,
            input_data={
                "contractId": data.contractId,
                "templateId": data.templateId,
                "contractType": data.contractType,
                "jurisdiction": data.jurisdiction,
                "inputs": data.inputs,
            },
        )

        # In production, this would trigger a background task
        # For now, we'll process synchronously and mark complete
        try:
            await self.job_repo.mark_processing(job.id)

            result = await self.generate_contract(current_user, data)

            await self.job_repo.mark_completed(
                job.id,
                {
                    "content": result.content,
                    "placeholders": result.placeholders,
                    "metadata_": result.metadata_.model_dump() if result.metadata_ else None,
                },
            )
        except Exception as e:
            await self.job_repo.mark_failed(job.id, str(e))

        return AsyncJobResponse(
            jobId=job.id,
            status=JobStatus.PENDING,
            pollUrl=f"/api/ai/jobs/{job.id}",
        )

    async def regenerate_contract(
        self,
        current_user: CurrentUser,
        data: AIRegenerateRequest,
    ) -> AIGenerateResponse:
        """
        Regenerate contract with feedback.

        In production, this would use the feedback to modify the prompt.
        """
        # For mock, just return a modified version
        content = f"""
<h1>CONTRATO (Versión Actualizada)</h1>

<p><em>Regenerado según feedback: {data.feedback}</em></p>

<p>Este documento ha sido actualizado según las instrucciones proporcionadas.</p>

<div class="signatures">
<p>Para constancia se firma.</p>
</div>
"""

        return AIGenerateResponse(
            content=content,
            placeholders={},
            metadata_=AIGenerateMetadata(
                model="mock-gpt-4",
                promptVersion="v1.0",
                confidenceScore=0.90,
            ),
        )

    async def get_job_status(self, job_id: str) -> AsyncJobStatus:
        """Get async job status."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundException(f"Job {job_id} not found")

        return AsyncJobStatus(
            jobId=job.id,
            status=JobStatus(job.status),
            progress=job.progress,
            result=job.result,
            error=job.error,
            createdAt=job.created_at,
            completedAt=job.completed_at,
        )
