from flask import Flask, request, jsonify
from datetime import datetime
import uuid

app = Flask(__name__)

# In-memory store for demo
abuse_reports = {}

@app.route('/report_abuse', methods=['POST'])
def report_abuse():
    data = request.json
    report_id = str(uuid.uuid4())
    report = {
        'reportId': report_id,
        'reviewId': data.get('reviewId'),
        'userId': data.get('userId'),
        'reportReason': data.get('reportReason', ''),
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'NEW',
        'triagePriority': 'LOW'
    }
    abuse_reports[report_id] = report
    return jsonify({'message': 'Report submitted', 'reportId': report_id}), 201

if __name__ == '__main__':
    app.run(debug=True)
