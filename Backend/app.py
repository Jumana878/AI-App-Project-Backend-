from flask import Flask, request, jsonify
from flask_cors import CORS
from scheduler_logic import generate_and_rank

app = Flask(__name__)
CORS(app)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json

    print("Received request:", data)  # Debug log

    courses = data.get('courses', [])
    preferences = data.get('preferences', {})

    if not courses:
        return jsonify({"error": "No courses selected"}), 400

    try:
        results = generate_and_rank(courses, preferences)

        if not results:
            return jsonify({"message": "No valid schedules found"}), 200

        return jsonify(results[:5])  # Top 5

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
