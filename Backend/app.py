from flask import Flask, request, jsonify
from flask_cors import CORS
from scheduler_logic import generate_and_rank # Importing your logic

app = Flask(__name__)
CORS(app) # Allows Lovable to communicate with this server

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    
    # Lovable sends: { "courses": ["CS101", "MATH101"], "preferences": {...} }
    courses = data.get('courses', [])
    preferences = data.get('preferences', {})
    
    if not courses:
        return jsonify({"error": "No courses selected"}), 400
        
    try:
        results = generate_and_rank(courses, preferences)
        # Send back the top 5 schedules
        return jsonify(results[:5])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the server on port 5000
    app.run(debug=True, port=5000)