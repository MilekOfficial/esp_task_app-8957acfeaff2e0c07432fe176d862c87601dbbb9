from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
import sqlite3

app = Flask(__name__)
DATABASE = 'tasks.db'

def get_db_conn():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS gamification (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
    ''')
    conn.execute('INSERT OR IGNORE INTO gamification (key, value) VALUES (?, ?)', ('score', 0))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_conn()
    tasks = conn.execute('SELECT id, task, timestamp FROM tasks ORDER BY timestamp DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    task_content = data.get('task', 'unnamed')
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task, timestamp) VALUES (?, ?)', (task_content, timestamp))
    new_id = cursor.lastrowid

    # Gamification: Add points if the task is from the ESP32
    if task_content == "Task done from ESP32":
        cursor.execute('UPDATE gamification SET value = value + ? WHERE key = ?', (10, 'score'))

    conn.commit()
    conn.close()

    new_task = {
        "id": new_id,
        "task": task_content,
        "timestamp": timestamp
    }
    return jsonify({"status": "ok", "task": new_task}), 201

@app.route('/api/score', methods=['GET'])
def get_score():
    conn = get_db_conn()
    score_row = conn.execute('SELECT value FROM gamification WHERE key = ?', ('score',)).fetchone()
    conn.close()
    score = score_row['value'] if score_row else 0
    return jsonify({"score": score})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()

    if rows_deleted == 0:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    
    return jsonify({"status": "ok", "message": f"Task {task_id} deleted"}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=40924, debug=True)
