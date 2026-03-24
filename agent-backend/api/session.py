# api/session.py
import uuid
from fastapi import APIRouter

router = APIRouter()

@router.get("/get-session-id")
def get_session():
    """
    Generate a unique session ID each time the frontend requests one.
    Frontend stores it in localStorage for persistence.
    """
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}