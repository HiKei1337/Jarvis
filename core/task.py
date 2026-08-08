"""
JARVIS Task Context

Encapsulates task state for tracking execution progress.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid


# Task statuses
STATUS_PENDING = "pending"
STATUS_PLANNING = "planning"
STATUS_EXECUTING = "executing"
STATUS_VERIFYING = "verifying"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"


@dataclass
class TaskContext:
    """Context object for tracking a single task."""
    
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_request: str = ""
    current_step: int = 0
    total_steps: int = 0
    status: str = STATUS_PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    last_error: Optional[str] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    results: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self):
        """Mark task as started."""
        self.started_at = datetime.now()
        if self.status == STATUS_PENDING:
            self.status = STATUS_PLANNING
    
    def begin_execution(self, steps: List[Dict[str, Any]]):
        """Begin execution phase."""
        self.steps = steps
        self.total_steps = len(steps)
        self.status = STATUS_EXECUTING
        self.current_step = 0
    
    def step_complete(self, result: str, success: bool = True):
        """Mark a step as complete."""
        self.current_step += 1
        self.results.append(result)
        if not success and self.last_error is None:
            self.last_error = result
    
    def verify(self):
        """Enter verification phase."""
        self.status = STATUS_VERIFYING
    
    def complete(self):
        """Mark task as completed successfully."""
        self.finished_at = datetime.now()
        self.status = STATUS_COMPLETED
    
    def fail(self, error: str):
        """Mark task as failed."""
        self.finished_at = datetime.now()
        self.status = STATUS_FAILED
        self.last_error = error
    
    def cancel(self):
        """Mark task as cancelled."""
        self.finished_at = datetime.now()
        self.status = STATUS_CANCELLED
    
    @property
    def is_active(self) -> bool:
        """Check if task is still active."""
        return self.status in (STATUS_PENDING, STATUS_PLANNING, STATUS_EXECUTING, STATUS_VERIFYING)
    
    @property
    def is_finished(self) -> bool:
        """Check if task is finished."""
        return self.status in (STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED)
    
    @property
    def progress(self) -> float:
        """Get execution progress (0.0 to 1.0)."""
        if self.total_steps == 0:
            return 0.0
        return min(1.0, self.current_step / self.total_steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "user_request": self.user_request,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "last_error": self.last_error,
            "results": self.results,
            "progress": self.progress,
        }
