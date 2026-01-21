"""AI module - Database repository."""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AICache, AsyncJob


class AsyncJobRepository:
    """Repository for async job tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        job_type: str,
        user_id: str,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> AsyncJob:
        """Create a new async job."""
        job = AsyncJob(
            job_type=job_type,
            user_id=user_id,
            input_data=input_data or {},
            status="PENDING",
            progress=0,
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_by_id(self, job_id: str) -> Optional[AsyncJob]:
        """Get job by ID."""
        result = await self.db.execute(select(AsyncJob).where(AsyncJob.id == job_id))
        return result.scalar_one_or_none()

    async def update_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[AsyncJob]:
        """Update job status."""
        updates: Dict[str, Any] = {"status": status}
        if progress is not None:
            updates["progress"] = progress
        if result is not None:
            updates["result"] = result
        if error is not None:
            updates["error"] = error
        if status in ["COMPLETED", "FAILED"]:
            updates["completed_at"] = datetime.utcnow()

        await self.db.execute(
            update(AsyncJob).where(AsyncJob.id == job_id).values(**updates)
        )
        await self.db.flush()
        return await self.get_by_id(job_id)

    async def mark_processing(self, job_id: str) -> Optional[AsyncJob]:
        """Mark job as processing."""
        return await self.update_status(job_id, "PROCESSING", progress=10)

    async def mark_completed(
        self,
        job_id: str,
        result: Dict[str, Any],
    ) -> Optional[AsyncJob]:
        """Mark job as completed."""
        return await self.update_status(job_id, "COMPLETED", progress=100, result=result)

    async def mark_failed(self, job_id: str, error: str) -> Optional[AsyncJob]:
        """Mark job as failed."""
        return await self.update_status(job_id, "FAILED", error=error)


class AICacheRepository:
    """Repository for AI content cache."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, cache_key: str) -> Optional[AICache]:
        """Get cached content."""
        result = await self.db.execute(
            select(AICache).where(
                AICache.cache_key == cache_key,
            )
        )
        cache = result.scalar_one_or_none()

        # Check if expired
        if cache and cache.expires_at and cache.expires_at < datetime.utcnow():
            return None

        return cache

    async def set(
        self,
        cache_key: str,
        content: str,
        metadata_: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> AICache:
        """Set cached content."""
        cache = AICache(
            cache_key=cache_key,
            content=content,
            metadata_=metadata_ or {},
            expires_at=expires_at,
        )
        self.db.add(cache)
        await self.db.flush()
        return cache
