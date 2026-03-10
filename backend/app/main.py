from fastapi import FastAPI

from app.database import Base, engine
from app.models.course import Course, Enrollment, Exercise, Module, Progress  # noqa: F401
from app.routers import auth, courses, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DevSchool API")
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
