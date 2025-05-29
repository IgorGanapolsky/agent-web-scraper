"""Audit logging utilities."""

import logging
from typing import Any, Optional

# Create a separate logger for audit logs
audit_logger = logging.getLogger("audit")


def log_audit_event(
    event_type: str,
    user: Optional[str] = None,
    resource: Optional[str] = None,
    action: Optional[str] = None,
    status: str = "success",
    details: Optional[dict[str, Any]] = None,
):
    """Log an audit event.

    Args:
        event_type: Type of the event (e.g., 'user_login', 'data_export')
        user: User who performed the action
        resource: Resource that was accessed or modified
        action: Action that was performed
        status: Status of the action ('success', 'failure')
        details: Additional details about the event
    """
    extra = {
        "audit": {
            "event_type": event_type,
            "user": user,
            "resource": resource,
            "action": action,
            "status": status,
            **({} if details is None else {"details": details}),
        }
    }

    # Use INFO level for successful events, WARNING for failures
    log_level = logging.INFO if status == "success" else logging.WARNING
    audit_logger.log(
        log_level,
        "Audit: %s - %s - %s",
        event_type,
        action or "",
        status,
        extra={"data": extra},
    )
