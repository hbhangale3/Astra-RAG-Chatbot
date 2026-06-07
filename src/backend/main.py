import logging
from fastapi import FastAPI
from src.backend.api.chat import router as chat_router
from src.backend.api.document_router import router as document_router
from src.backend.config.backend_settings import BackendSettings
from src.backend.api.quiz_router import router as quiz_router
from src.backend.services.metrics_service import (
    get_metrics_response,
    prometheus_metrics_middleware,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()
app.middleware("http")(prometheus_metrics_middleware)
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(quiz_router)

settings = BackendSettings()

@app.get("/metrics")
def metrics():
    """
    Exposes Prometheus metrics for scraping.
    """
    return get_metrics_response()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )