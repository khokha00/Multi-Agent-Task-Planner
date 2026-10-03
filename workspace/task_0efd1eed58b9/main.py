from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Task model
class Task(BaseModel):
    id: int
    title: str
    done: bool

# In-memory task storage
tasks = [Task(id=1, title='Task 1', done=False), Task(id=2, title='Task 2', done=True)]

# GET /tasks
@app.get('/tasks', response_model=List[Task])
def get_tasks():
    return tasks

# GET /tasks/{task_id}
@app.get('/tasks/{task_id}', response_model=Task)
def get_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task

    return None

# POST /tasks
@app.post('/tasks', response_model=Task)
def create_task(task: Task):
    tasks.append(task)
    return task

# PUT /tasks/{task_id}
@app.put('/tasks/{task_id}', response_model=Task)
def update_task(task_id: int, task: Task):
    for i, existing_task in enumerate(tasks):
        if existing_task.id == task_id:
            tasks[i] = task
            return task

    return None

# DELETE /tasks/{task_id}
@app.delete('/tasks/{task_id}')
def delete_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)
            return {}

    return None