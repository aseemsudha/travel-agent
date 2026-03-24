from fastapi import APIRouter, HTTPException
from core.vector_db import get_memory_collection
from app_config import MEMORY_USER_CAN_DELETE

router = APIRouter()

@router.delete("/memory")
async def delete_user_memory(session_id: str = None):
    """
    Delete all memories for a session_id.
    If no session_id provided, deletes all memories (use carefully!)
    """

     # ---- Check if user memory deletion is allowed ----
    if not MEMORY_USER_CAN_DELETE:
        raise HTTPException(status_code=403, detail="Memory deletion disabled")

    collection = get_memory_collection()

    try:
        if session_id:
            results = collection.get(
                where={"session_id": session_id},
                include=["metadatas"]
            )
        else:
            results = collection.get(include=["metadatas"])

        ids_to_delete = results.get("ids", [])

        if not ids_to_delete:
            return {"message": "No memories to delete"}

        collection.delete(ids=ids_to_delete)
        return {"message": f"Deleted {len(ids_to_delete)} memories."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))