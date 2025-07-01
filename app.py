from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)

# --- MongoDB Connection ---
# IMPORTANT: You need to replace the placeholder with your actual MongoDB Atlas connection string.
# For security, it's best to set this as an environment variable.
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://server:grpc8BZKoeTqUVcP@cluster0.mi2bcfi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.tasks_db
tasks_collection = db.tasks
gamification_collection = db.gamification

def init_gamification():
    """Ensure the score document exists in the gamification collection."""
    if gamification_collection.count_documents({"key": "score"}) == 0:
        gamification_collection.insert_one({"key": "score", "value": 0})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = []
    # Find all tasks and sort by timestamp in descending order
    for task in tasks_collection.find().sort("timestamp", -1):
        task["id"] = str(task["_id"])
        del task["_id"]
        tasks.append(task)
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({"status": "error", "message": "Invalid input"}), 400

    task_content = data.get('task', 'unnamed')
    timestamp = datetime.now(timezone.utc).isoformat()

    task_to_insert = {
        "task": task_content,
        "timestamp": timestamp
    }
    result = tasks_collection.insert_one(task_to_insert)
    new_id = result.inserted_id

    # Gamification: Add 10 points if the task is from the ESP32
    if task_content == "Task done from ESP32":
        gamification_collection.update_one(
            {"key": "score"},
            {"$inc": {"value": 10}},
            upsert=True  # Create the score document if it doesn't exist
        )

    new_task_response = {
        "id": str(new_id),
        "task": task_content,
        "timestamp": timestamp
    }
    return jsonify({"status": "ok", "task": new_task_response}), 201

@app.route('/api/score', methods=['GET'])
def get_score():
    score_doc = gamification_collection.find_one({"key": "score"})
    score = score_doc['value'] if score_doc else 0
    return jsonify({"score": score})

@app.route('/api/tasks/<string:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        # Convert the string ID to a MongoDB ObjectId
        obj_id = ObjectId(task_id)
    except Exception:
        return jsonify({"status": "error", "message": "Invalid task ID format"}), 400
    
    result = tasks_collection.delete_one({'_id': obj_id})

    if result.deleted_count == 0:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    
    return jsonify({"status": "ok", "message": f"Task {task_id} deleted"}), 200

if __name__ == '__main__':
    init_gamification()
    app.run(host='0.0.0.0', port=40924, debug=True)
