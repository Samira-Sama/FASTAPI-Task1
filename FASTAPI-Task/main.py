from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
from typing import List
from pydantic import BaseModel 
from celery import Celery
from celery_config import CELERY_BROKER_URL

app = FastAPI()

celery = Celery(
    'tasks',
    broker=CELERY_BROKER_URL,
)

# Secret key to sign the JWT tokens
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Dependency to get the current user based on the JWT token
async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Custom logic to fetch user data from a database or another source
    # For simplicity, returning a hardcoded user here
    return {"username": username, "roles": ["admin"]}

# Middleware for custom authorization based on user roles
async def authorize_user(current_user: dict = Depends(get_current_user), required_roles: list = None):
    if required_roles is None:
        return current_user

    user_roles = current_user.get("roles", [])
    for role in required_roles:
        if role in user_roles:
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have access to this resource",
    )

# Model for the task
class TaskCreate(BaseModel):
    task_name: str

tasks_db = []

# POST endpoint to create a task
@app.post("/create-task", response_model=dict)
async def create_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    current_time = datetime.utcnow()
    task_data = {"username": current_user["username"], "task_name": task.task_name, "timestamp": current_time}
    tasks_db.append(task_data)
    return task_data

# GET endpoint to get the list of tasks for a logged-in user
@app.get("/tasks", response_model=List[dict], dependencies=[Depends(authorize_user)])
async def get_tasks(current_user: dict = Depends(get_current_user)):
    user_tasks = [task for task in tasks_db if task["username"] == current_user["username"]]
    return user_tasks



@celery.task(name='tasks.print_message')
def print_message(message):
    print(message)
    return f"Message '{message}' printed successfully."


@celery.task(name='tasks.schedule_print_message')
def schedule_print_message(task_name, scheduled_time):
    print(f"Scheduled task: '{task_name}' will be printed at {scheduled_time}")
    print_message.apply_async(args=[f"Scheduled Task: {task_name}"], eta=scheduled_time)


@app.post("/schedule-task", response_model=dict)
async def schedule_task(task: TaskCreate, scheduled_time: datetime, current_user: dict = Depends(get_current_user)):
    current_time = datetime.utcnow()

    # Enqueue the Celery periodic task for scheduled execution
    schedule_print_message.apply_async(args=[task.task_name, scheduled_time], countdown=10)

    task_data = {"username": current_user["username"], "task_name": task.task_name, "timestamp": current_time, "scheduled_time": scheduled_time}
    tasks_db.append(task_data)
    return task_data