"""
Role-based access control.

This is a demo RBAC layer for the hackathon.
The frontend sends the role in the X-User-Role request header.
In production you would verify a signed JWT here instead.

Roles:
  faculty  — full read/write access
  student  — read-only; no upload/delete/modify
"""
from fastapi import Header, HTTPException

FACULTY = "faculty"
STUDENT = "student"
VALID_ROLES = {FACULTY, STUDENT}

FORBIDDEN_MSG = (
    "You do not have permission to modify course content. "
    "Only faculty can upload or manage course materials."
)


def require_faculty(x_user_role: str = Header(default="faculty")) -> str:
    """
    FastAPI dependency — raises 403 if the caller is not faculty.

    Usage:
        @router.post("/upload")
        async def upload(..., role: str = Depends(require_faculty)):
            ...
    """
    role = x_user_role.lower().strip()
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown role '{role}'. Must be 'faculty' or 'student'.",
        )
    if role != FACULTY:
        raise HTTPException(status_code=403, detail=FORBIDDEN_MSG)
    return role


def get_role(x_user_role: str = Header(default="faculty")) -> str:
    """
    FastAPI dependency — returns the role string without enforcing it.
    Used on read endpoints where both roles are allowed.
    """
    role = x_user_role.lower().strip()
    return role if role in VALID_ROLES else FACULTY
