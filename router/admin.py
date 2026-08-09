from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from database import SessionLocal
from models import todos
from fastapi.responses import JSONResponse
from router.auth import get_current_user

router = APIRouter()

# =========================
# Database Dependency
# =========================
def get_db():
    # Open a database session for each request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# =========================
# User Dependency
# =========================
user_dependency = Annotated[dict, Depends(get_current_user)]

# =========================
# Admin Read All Todos
# =========================
@router.get("/admin/todo")
def read_all_todos(user: user_dependency, db: db_dependency):
    # Only admin users can use this endpoint
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=401, detail='Failed Authentication')
    # return db.query(todos).filter(todos.owner_id == user.get('id')).all()
    
    return db.query(todos).all()


@router.delete("/admin/delete/{todo_id}")
def delete_todos_by_admin(
    user: user_dependency,
    db: db_dependency,
    todo_id: int
):
    # Only admin users can delete a todo by its id
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=404, detail='User Not found. Try again.')

    todo = (
        db.query(todos)
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



