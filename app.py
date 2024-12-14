from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
import psutil
import time
import os

THRESHOLDS = {
    'cpu': 80,
    'ram': 8,
    'disk': 10,
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metrics.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    cpu_usage = db.Column(db.Float, nullable=False)
    ram_usage = db.Column(db.Float, nullable=False)
    disk_usage = db.Column(db.Float, nullable=False)
    uptime = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=True)

def collect_metrics():
    while True:
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().used / (1024 ** 3) 
        disk_usage = psutil.disk_usage('/').free / (1024 ** 3)
        uptime = time.time() - psutil.boot_time() 
        temperature = None

        if hasattr(psutil.sensors_temperatures(), 'coretemp'):
            core_temp = psutil.sensors_temperatures().get('coretemp', [])
            if core_temp:
                temperature = core_temp[0].current

        new_metric = Metric(
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            disk_usage=disk_usage,
            uptime=uptime / 3600,
            temperature=temperature
        )

        db.session.add(new_metric)
        db.session.commit()

        time.sleep(30)

@app.route('/')
def dashboard():
    metrics = Metric.query.order_by(Metric.timestamp.desc()).limit(20).all()
    return render_template('dashboard.html', metrics=metrics)

@app.route('/metrics')
def get_metrics():
    metrics = Metric.query.order_by(Metric.timestamp.desc()).limit(20).all()
    return jsonify([{
        'timestamp': metric.timestamp,
        'cpu_usage': metric.cpu_usage,
        'ram_usage': metric.ram_usage,
        'disk_usage': metric.disk_usage,
        'uptime': metric.uptime,
        'temperature': metric.temperature
    } for metric in metrics])

if __name__ == "__main__":
    if not os.path.exists('metrics.db'):
        db.create_all()
    
    metric_thread = Thread(target=collect_metrics)
    metric_thread.daemon = True
    metric_thread.start()
    
    app.run(host='0.0.0.0', port=5000)
