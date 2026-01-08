from fastapi import APIRouter

router = APIRouter(tags=['Monitoring'])

@router.get("/health")
def health_check():
    return {"status": "ok"}
