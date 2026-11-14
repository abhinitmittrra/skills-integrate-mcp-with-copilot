# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher login to register and unregister students
- Public view of activities and their participants

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Configure teacher login in the server environment before starting the app.
   Set `TEACHER_USERNAME`, `TEACHER_PASSWORD`, and `SESSION_SECRET`.
   `SESSION_SECRET` must be at least 32 characters; generate a random value
   and keep it out of source control. For local HTTP development only, set
   `SESSION_COOKIE_SECURE=false` so the session cookie can be used without
   HTTPS. Do not use that setting in production.

3. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities and their participants (public)                   |
| POST   | `/auth/login`                                                     | Log in with teacher username and password                            |
| GET    | `/auth/me`                                                        | Check the current login session                                       |
| POST   | `/auth/logout`                                                    | End the current login session                                         |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher login required)                           |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher login required)                      |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
