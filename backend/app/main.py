import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.config import settings
from backend.app.database.session import Base, engine
from backend.app.seed import seed_db

# Import Routers
from backend.app.api.auth import router as auth_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.tenders import router as tenders_router
from backend.app.api.sources import router as sources_router
from backend.app.api.keywords import router as keywords_router
from backend.app.api.settings import router as settings_router
from backend.app.api.prompts import router as prompts_router
from backend.app.api.health import router as health_router
from backend.app.api.analytics import router as analytics_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database & Seed
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    seed_db()

# Mount API V1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(tenders_router, prefix=settings.API_V1_STR)
app.include_router(sources_router, prefix=settings.API_V1_STR)
app.include_router(keywords_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(prompts_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)

# Mount Static Client Scripts & Assets
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../static"))
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount Stitch Design UI pages
stitch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../stitch_tenderiq_ai_platform"))
if os.path.exists(stitch_dir):
    app.mount("/stitch", StaticFiles(directory=stitch_dir), name="stitch")

@app.get("/")
def read_root():
    # Return main entry view
    dashboard_path = os.path.join(stitch_dir, "dashboard_tenderiq_ai", "code.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return {"message": "TenderIQ AI Backend Running", "docs": "/docs"}

@app.get("/login")
def login_page():
    path = os.path.join(stitch_dir, "login_tenderiq_ai", "code.html")
    return FileResponse(path)

@app.get("/opportunities")
def opportunities_page():
    path = os.path.join(stitch_dir, "opportunities_tenderiq_ai", "code.html")
    return FileResponse(path)

@app.get("/opportunity-details")
def opportunity_details_page():
    path = os.path.join(stitch_dir, "opportunity_details_tenderiq_ai", "code.html")
    return FileResponse(path)

@app.get("/sources")
def sources_page():
    path = os.path.join(stitch_dir, "source_manager_tenderiq_ai", "code.html")
    return FileResponse(path)

@app.get("/keywords")
def keywords_page():
    path = os.path.join(stitch_dir, "keyword_manager_tenderiq_ai", "code.html")
    return FileResponse(path)

@app.get("/ai-analysis")
def ai_analysis_page():
    path = os.path.join(stitch_dir, "ai_analysis_tenderiq_ai", "code.html")
    return FileResponse(path)

@app.get("/reports")
def reports_page():
    path = os.path.join(stitch_dir, "keyword_manager_tenderiq_ai", "code.html")
    return FileResponse(path)

