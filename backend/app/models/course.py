import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    modules = relationship("Module", back_populates="course", order_by="Module.order")
    enrollments = relationship("Enrollment", back_populates="course")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, default=0)

    course = relationship("Course", back_populates="modules")
    exercises = relationship("Exercise", back_populates="module", order_by="Exercise.order")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    name = Column(String, nullable=False)
    repo_prefix = Column(String)
    classroom_url = Column(String)
    classroom_teacher_url = Column(String)
    order = Column(Integer, default=0)
    required = Column(Boolean, default=True, nullable=False)

    module = relationship("Module", back_populates="exercises")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user = relationship("User")
    course = relationship("Course", back_populates="enrollments")


class ProgressStatus(enum.StrEnum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    github_repo = Column(String)
    status = Column(Enum(ProgressStatus), default=ProgressStatus.not_started, nullable=False)
    completed_at = Column(DateTime)

    user = relationship("User")
    exercise = relationship("Exercise")
