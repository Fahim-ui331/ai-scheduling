# data_models.py
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, UniqueConstraint, Table
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# many-to-many: course prerequisites (Course -> Course)
course_prereq = Table(
    "course_prereq",
    Base.metadata,
    Column("course_id", String(32), ForeignKey("courses.id"), primary_key=True),
    Column("prereq_id", String(32), ForeignKey("courses.id"), primary_key=True),
)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(120))
    cgpa = Column(Float, default=0.0)
    payment_cleared = Column(Boolean, default=False)
    evaluation_done = Column(Boolean, default=False)
    level = Column(Integer, default=1)
    department = Column(String(20))

    preferences = relationship("Preference", back_populates="student")
    assignments = relationship("Assignment", back_populates="student")

class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True)
    name = Column(String(120))
    max_load = Column(Integer, default=3)  # sections per term
    available = Column(Boolean, default=True)
    sections = relationship("Section", back_populates="faculty")

class Course(Base):
    __tablename__ = "courses"
    id = Column(String(32), primary_key=True)  # e.g., CS101
    title = Column(String(160))
    level = Column(Integer, default=1)
    credits = Column(Integer, default=3)

    sections = relationship("Section", back_populates="course")
    prerequisites = relationship(
        "Course",
        secondary=course_prereq,
        primaryjoin=id == course_prereq.c.course_id,
        secondaryjoin=id == course_prereq.c.prereq_id,
        backref="required_for"
    )

class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True)
    course_id = Column(String(32), ForeignKey("courses.id"))
    code = Column(String(8))          # A,B,C...
    day = Column(String(12))          # Monday, Tuesday...
    start_time = Column(String(5))    # 09:00
    end_time = Column(String(5))      # 10:30
    room = Column(String(40))
    capacity = Column(Integer, default=40)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)  # can be NULL / N/A

    course = relationship("Course", back_populates="sections")
    faculty = relationship("Faculty", back_populates="sections")
    assignments = relationship("Assignment", back_populates="section")

    __table_args__ = (UniqueConstraint('course_id', 'code', name='uq_course_section'),)

class Preference(Base):
    __tablename__ = "preferences"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(String(32), ForeignKey("courses.id"))
    preferred_sections = Column(String(50))  # e.g., "A,B,C"
    time_pref = Column(String(20))           # e.g., morning/avoid_08

    student = relationship("Student", back_populates="preferences")
    course = relationship("Course")

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    section_id = Column(Integer, ForeignKey("sections.id"))
    status = Column(String(20), default="assigned")  # assigned / not_assigned

    student = relationship("Student", back_populates="assignments")
    section = relationship("Section", back_populates="assignments")
