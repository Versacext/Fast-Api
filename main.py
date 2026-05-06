from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
import sqlite3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('state_tracker.db')
    cursor = conn.cursor()
    # Таблица для записей состояния
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
                      (id INTEGER PRIMARY KEY, timestamp TEXT, zone_level INTEGER, day_number INTEGER)''')
    # Таблица для даты старта
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Дата начала вашего пути (можно обнулять при срыве)
START_DATE = datetime(2026, 5, 1) 

class StateEntry(BaseModel):
    level: int

def get_status_message(day: int, level: int):
    # Логика: если день кратен 7 (критические точки) и уровень выше 6
    if day % 7 == 0 and level >= 7:
        return "ВНИМАНИЕ: Критическая нагрузка в опасный период. Срочно смени деятельность!"
    if level >= 8:
        return "DANGEROUS ZONE: Мозг в ловушке. Немедленно отойди от компьютера!"
    return "Состояние под контролем."

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    conn = sqlite3.connect('state_tracker.db')
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, zone_level, day_number FROM logs ORDER BY timestamp ASC")
    data = cursor.fetchall()
    conn.close()
    
    labels = [d[0] for d in data]
    values = [d[1] for d in data]
    days = [d[2] for d in data]

    # Получаем последнее состояние для проверки
    latest_level = values[-1] if values else 1
    latest_day = days[-1] if days else 1
    current_message = get_status_message(latest_day, latest_level)

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "labels": labels, 
        "values": values, 
        "days": days,
        "message": current_message  # Передаем статус в HTML
    })

@app.post("/log")
async def add_entry(entry: StateEntry):
    current_time = datetime.now()
    day_number = (current_time - START_DATE).days + 1
    
    conn = sqlite3.connect('state_tracker.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (timestamp, zone_level, day_number) VALUES (?, ?, ?)",
                   (current_time.strftime("%H:%M"), entry.level, day_number))
    conn.commit()
    conn.close()
    return {"status": "success", "day": day_number}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
