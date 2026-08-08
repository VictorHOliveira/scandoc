import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ScanJob:
    id: str
    uid: str
    status: str = "processing"
    progress: dict = field(default_factory=lambda: {"percent": 0, "stage": "Enviando"})
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class JobStore:
    def __init__(self, ttl_seconds: int = 900, max_jobs: int = 50) -> None:
        self._jobs: dict[str, ScanJob] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
        self._max = max_jobs

    def create(self, uid: str) -> ScanJob:
        with self._lock:
            self._cleanup()
            job = ScanJob(id=uuid.uuid4().hex[:12], uid=uid)
            self._jobs[job.id] = job
            return job

    def get(self, job_id: str, uid: str) -> Optional[ScanJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None and job.uid != uid:
                return None
            return job

    def update(self, job_id: str, **kwargs: Any) -> Optional[ScanJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            for key, value in kwargs.items():
                setattr(job, key, value)
            job.updated_at = time.time()
            return job

    def _cleanup(self) -> None:
        now = time.time()
        expired = [jid for jid, j in self._jobs.items() if now - j.updated_at > self._ttl]
        for jid in expired:
            del self._jobs[jid]
        if len(self._jobs) > self._max:
            oldest = sorted(self._jobs, key=lambda jid: self._jobs[jid].created_at)
            for jid in oldest[: len(self._jobs) - self._max]:
                del self._jobs[jid]


jobs = JobStore()
