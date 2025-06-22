from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from fastapi.responses import JSONResponse
from fastapi import status, FastAPI, Depends

from src.auth import verify_api_key, verify_db_key

app = FastAPI(
    title="Roechling FastAPI",
    version="1.1.0",
    description="A simple API to interact with the Roechling database.",
    docs_url="/docs",
)

# app.docs_url = None
# app.redoc_url = None
# app.openapi_url = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Generic HTTPException handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "An unexpected error occurred",
            "method": request.method,
            "url": request.url.path,
        },
    )


# Routers
from src.v1.guest_book.router import router as guest_book_router
from src.v1.companies.router import router as companies_router
from src.v1.database.router import router as database_router
from src.v1.forms.router import router as forms_router
from src.auth.router import router as auth_router

# Auth router
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
# Database router
app.include_router(database_router, prefix="/v1/database", tags=["Database"], dependencies=[Depends(verify_db_key)])
# Guest Book router
app.include_router(guest_book_router, prefix="/v1/guest-book", tags=["Guest Book"], dependencies=[Depends(verify_api_key)])
# Forms router
app.include_router(forms_router, prefix="/v1/forms", tags=["Forms"], dependencies=[Depends(verify_api_key)])
# Companies router
app.include_router(companies_router, prefix="/v1/companies", tags=["Companies"], dependencies=[Depends(verify_api_key)])
