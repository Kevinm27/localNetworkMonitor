from flask import Flask, request, jsonify, render_template
import ping3
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

app = Flask(__name__)

def log_ping_result(ip, status, rtt):
    conn = sqlite3.connect('ping_log.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS logs (ip TEXT, status TEXT, rtt REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    c.execute("INSERT INTO logs (ip, status, rtt) VALUES (?, ?, ?)", (ip, status, rtt))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping', methods=['POST'])
def ping():
    ip = request.json['ip']
    try:
        rtt = ping3.ping(ip)
        if rtt:
            log_ping_result(ip, 'online', rtt)
            return jsonify({'ip': ip, 'status': 'online', 'rtt': rtt})
        else:
            log_ping_result(ip, 'offline', None)
            return jsonify({'ip': ip, 'status': 'offline', 'rtt': None})
    except Exception as e:
        log_ping_result(ip, 'error', None)
        return jsonify({'ip': ip, 'status': 'error', 'message': str(e)})

@app.route('/log', methods=['GET'])
def get_log():
    conn = sqlite3.connect('ping_log.db')
    c = conn.cursor()
    c.execute("SELECT * FROM logs")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

def scheduled_ping():
    devices = ['8.8.8.8', '8.8.4.4']
    for ip in devices:
        try:
            rtt = ping3.ping(ip)
            if rtt:
                log_ping_result(ip, 'online', rtt)
            else:
                log_ping_result(ip, 'offline', None)
        except Exception as e:
            log_ping_result(ip, 'error', None)
            print(f"Error pinging {ip}: {e}")

executors = {
    'default': ThreadPoolExecutor(10),
    'processpool': ProcessPoolExecutor(3)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 1
}

scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
scheduler.add_job(scheduled_ping, 'interval', minutes=5, misfire_grace_time=300)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
