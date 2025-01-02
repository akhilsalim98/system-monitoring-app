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

db = SQLAlchemy()
db.init_app(app)

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
        try:
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().used / (1024 ** 3)
            partitions = psutil.disk_partitions()
            if partitions:
                device = partitions[0].device
                normalized_device = os.path.normpath(device).replace("\\", "/")
                print(f"Normalized Device: {normalized_device}")

                try:
                    if os.path.exists(normalized_device):
                        disk_usage = psutil.disk_usage(normalized_device).free / (1024 ** 3)
                    else:
                        disk_usage = 0 
                except Exception as e:
                    print(f"Error accessing disk usage for {normalized_device}: {e}")
                    disk_usage = 0
            else:
                disk_usage = 0 
            uptime = time.time() - psutil.boot_time()

            temperature = None
            if hasattr(psutil, 'sensors_temperatures') and 'coretemp' in psutil.sensors_temperatures():
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

            with app.app_context(): 
                db.session.add(new_metric)
                db.session.commit()

        except Exception as e:
            print(f"Error collecting metrics: {e}")
        
        time.sleep(30)

@app.route('/')
def dashboard():
    metrics = Metric.query.order_by(Metric.timestamp.desc()).limit(20).all()
    return render_template('dashboard.html', metrics=metrics)

@app.route('/metrics')
def get_metrics():
    try:
        metrics = Metric.query.order_by(Metric.timestamp.desc()).limit(20).all()
        metrics_list = []
        for metric in metrics:
            metrics_list.append({
                'timestamp': metric.timestamp,
                'cpu_usage': metric.cpu_usage,
                'ram_usage': metric.ram_usage,
                'disk_usage': metric.disk_usage,
                'uptime': metric.uptime,
                'temperature': metric.temperature
            })
        return jsonify(metrics_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 

    metric_thread = Thread(target=collect_metrics)
    metric_thread.daemon = True 
    metric_thread.start()

    app.run(host="0.0.0.0", port=5000, debug=True)
