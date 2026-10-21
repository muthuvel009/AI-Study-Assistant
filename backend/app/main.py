from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.routers import auth, documents, chats, progress, quizzes, recommendations

app = FastAPI(
    title="AI Study Assistant API",
    description="Backend API for AI Study Assistant platform",
    version="5.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chats.router)
app.include_router(quizzes.router)
app.include_router(progress.router)
app.include_router(recommendations.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint confirming API status."""
    return {
        "status": "healthy",
        "service": "AI Study Assistant Backend",
        "phase": 5,
    }


# Standardized error handling without exposing internal stack traces
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Format 422 validation errors cleanly
    errors = exc.errors()
    clean_messages = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        clean_messages.append(f"{loc}: {msg}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error in request data.",
            "errors": clean_messages,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Catch unexpected 500 exceptions cleanly without exposing internal tracebacks
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )
