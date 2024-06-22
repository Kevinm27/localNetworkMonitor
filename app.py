from flask import Flask, request, jsonify
import ping3
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

def log_ping_result(ip, status, rtt):
    conn = sqlite3.connect('ping_log.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS logs (ip TEXT, status TEXT, rtt REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    c.execute("INSERT INTO logs (ip, status, rtt) VALUES (?, ?, ?)", (ip, status, rtt))
    conn.commit()
    conn.close()

@app.route('/log', methods=['GET'])
def get_log():
    conn = sqlite3.connect('ping_log.db')
    c = conn.cursor()
    c.execute("Select * FROM logs")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

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
    

def scheduled_ping():
    devices = ['192.168.1.217', '192.168.1.214', '192.168.1.254'] # find ip i want to monitor

    for ip in devices:
        try:
            rtt = ping3.ping(ip)
            if rtt:
                log_ping_result(ip, 'online', rtt)
            else:
                log_ping_result(ip, 'offline', None)
        except Exception as e:
            log_ping_result(ip, 'error', None)

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_ping, 'interval', minutes=.1)
scheduler.start()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
