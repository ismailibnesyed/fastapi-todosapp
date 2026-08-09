from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from fastapi.responses import JSONResponse

import models
from models import todos, Users
from router.auth import get_current_user
from database import engine, SessionLocal
from router import admin
from router import auth


# Create the FastAPI app object
app = FastAPI()


# Make sure database tables are created
models.Base.metadata.create_all(bind=engine)


# Add routers from auth and admin modules
app.include_router(auth.router)
app.include_router(admin.router)


# =========================
# Pydantic Models
# =========================

# This model is used when creating a new todo item
class TodoCreate(BaseModel):
    id: int
    title: str
    description: str = Field(max_length=100)
    priority: int = Field(gt=0, le=5)
    completed: bool


# This model is used when updating an existing todo item
class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=100)
    priority: Optional[int] = Field(default=None, gt=0, lt=5)
    completed: Optional[bool] = None


# =========================
# Database Dependency
# =========================

def get_db():
    # Open a new database session for each request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# =========================
# User Dependency
# =========================

# Get current user from token before handling request
user_dependency = Annotated[dict, Depends(get_current_user)]


# =========================
# GET ALL TODOS
# =========================

@app.get("/")
def read_todos(user: user_dependency, db: db_dependency):
    # Return all todos for the logged-in user
    if user is None:
        raise HTTPException(status_code=404, detail='User Not found. Try again.')
    return db.query(todos).filter(todos.owner_id == user.get('id')).all()


# =========================
# GET SPECIFIC TODO
# =========================

@app.get("/todo/{todo_id}")
def read_specific_todo(user: user_dependency, db: db_dependency, todo_id: int):
    # Return a single todo by its id for the logged-in user
    if user is None:
        raise HTTPException(status_code=404, detail='User Not found. Try again.')

    specific_todo = (
        db.query(todos)
        .filter(todos.owner_id == user.get('id'))
        .filter(todos.id == todo_id)
        .first()
    )

    if specific_todo is None:
        raise HTTPException(
            status_code=404,
            detail="Todo not found. Please try again."
        )

    return specific_todo


# =========================
# CREATE TODO
# =========================

@app.post("/create/")
def create_todo(user: user_dependency, db: db_dependency, new_todo: TodoCreate):
    # Add a new todo item for the current user
    if user is None:
        raise HTTPException(status_code=404, detail='Todos  already added. Create new todos.')
    
    todo_model = todos(**new_todo.model_dump(), owner_id=user.get('id'))
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)

    return JSONResponse(status_code=201, content={"message": "Todo created successfully.", "todo_id": todo_model.id})


# =========================
# UPDATE TODOS
# =========================

@app.put("/edit/{todo_id}")
def update_todo(
    user: user_dependency,
    db: db_dependency,
    todo_id: int,
    update_todo: TodoUpdate
):
    # Update an existing todo owned by the current user
    if user is None:
        raise HTTPException(status_code=404, detail='Faild Authentication.')

    todo = (
        db.query(todos)
        .filter(todos.owner_id == user.get('id'))
        .filter(todos.id == todo_id)
        .first()
    )

    if todo is None:
        raise HTTPException(
            status_code=404,
            detail="Todo not found."
        )

    update_data = update_todo.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(todo, key, value)

    db.commit()
    db.refresh(todo)

    return JSONResponse(
        status_code=200,
        content={
            "message": "Todo updated successfully."
        }
    )


# =========================
# DELETE TODO
# =========================

@app.delete("/delete/{todo_id}")
def delete_todo(
    user: user_dependency,
    db: db_dependency,
    todo_id: int
):
    # Remove a todo owned by the current user
    if user is None:
        raise HTTPException(status_code=404, detail='User Not found. Try again.')

    todo = (
        db.query(todos)
        .filter(todos.owner_id == user.get('id'))
        .filter(todos.id == todo_id)
        .first()
    )

    if todo is None:
        raise HTTPException(
            status_code=404,
            detail="Todo not found."
        )

    db.delete(todo)
    db.commit()

    return JSONResponse(
        status_code=200,
        content={
            "message": "Todo deleted successfully."
        }
    )


# =========================
# View Profile
# =========================

@app.get("/user")
def view_profile(
    user: user_dependency, db: db_dependency
):
    # Return the current user's information
    if user is None:
        raise HTTPException(status_code=404, detail='Failed Authentication. User Not found. Try again.')
    # Change this line in view_profile
    return db.query(Users).filter(Users.id == user.get('id')).first()


