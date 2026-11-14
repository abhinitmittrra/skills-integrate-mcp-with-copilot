"""
High School Management System API

A simple FastAPI application that lets the public view extracurricular activities
and lets teachers manage student registrations.
"""

import hmac
import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware import Middleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

session_secret = os.getenv("SESSION_SECRET")
app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
    middleware=[
        Middleware(
            SessionMiddleware,
            secret_key=session_secret or secrets.token_urlsafe(32),
            https_only=os.getenv("SESSION_COOKIE_SECURE", "true").lower() != "false",
            same_site="lax",
        )
    ],
)


class TeacherLogin(BaseModel):
    username: str
    password: str


def get_teacher_credentials() -> tuple[str, str] | None:
    username = os.getenv("TEACHER_USERNAME")
    password = os.getenv("TEACHER_PASSWORD")
    secret = os.getenv("SESSION_SECRET")
    if not username or not password or not secret or len(secret) < 32:
        return None
    return username, password


def require_teacher(request: Request) -> str:
    credentials = get_teacher_credentials()
    if credentials is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Teacher login is not configured. Set TEACHER_USERNAME, "
                "TEACHER_PASSWORD, and a SESSION_SECRET of at least 32 characters."
            ),
        )

    username, _ = credentials
    if request.session.get("teacher") != username:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(credentials: TeacherLogin, request: Request):
    configured_credentials = get_teacher_credentials()
    if configured_credentials is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Teacher login is not configured. Set TEACHER_USERNAME, "
                "TEACHER_PASSWORD, and a SESSION_SECRET of at least 32 characters."
            ),
        )

    username, password = configured_credentials
    username_matches = hmac.compare_digest(
        credentials.username.encode("utf-8"), username.encode("utf-8")
    )
    password_matches = hmac.compare_digest(
        credentials.password.encode("utf-8"), password.encode("utf-8")
    )
    if not (username_matches and password_matches):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    request.session.clear()
    request.session["teacher"] = username
    return {"authenticated": True, "username": username}


@app.get("/auth/me")
def current_teacher(request: Request):
    credentials = get_teacher_credentials()
    username = credentials[0] if credentials else None
    session_username = request.session.get("teacher")
    if username and session_username == username:
        return {"authenticated": True, "username": username}
    return {"authenticated": False}


@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"authenticated": False}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str, email: str, _: str = Depends(require_teacher)
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str, email: str, _: str = Depends(require_teacher)
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
