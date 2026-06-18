"""Upload proxy — receives the file from the frontend and stores it via the
storage adapter (B2 in staging/prod, filesystem in dev).

Avoids CORS issues with direct browser→B2 presigned PUTs. The frontend always
uploads to our API; our API uploads to B2 server-side (no CORS involved).
"""

from fastapi import APIRouter, Request, Response, status
from app.integrations.factory import get_storage_adapter

router = APIRouter(prefix="/upload", tags=["upload"])


@router.put("/{key:path}")
async def proxy_upload(key: str, request: Request) -> Response:
    body = await request.body()
    content_type = request.headers.get("content-type", "application/octet-stream")
    storage = get_storage_adapter()
    await storage.put_bytes(key, body, content_type=content_type)
    return Response(status_code=status.HTTP_200_OK)
