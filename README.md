# System Monitoring & Alerting Application

## **Setup Instructions**

### **1. Run Locally**
1. Install dependencies:
    ```bash
    pip install -r requirements.txt

3. Run the application:
    ```bash
    python app.py
    ```

4. Open your browser and visit:

    http://127.0.0.1:5000

---

### **2. Run with Docker**
1. Build the Docker image:
    ```bash
    docker build -t system-monitoring-app:latest .
    ```

2. Run the container:
    ```bash
    docker run -d -p 5000:5000 --name system-monitoring-app system-monitoring-app:latest

    ```

3. Visit the dashboard at:
    http://127.0.0.1:5000

