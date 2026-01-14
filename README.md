# 🇦🇺 Australian Work & Tax Tracker V2.0
### **Maximize your tax return with data-driven WFH logging.**

The **Australian Work & Tax Tracker** is a production-ready tool designed for Australian employees and contractors to simplify the tracking of work hours. By automating the calculation of tax-deductible hours and comparing ATO claim methods, this app ensures you maximize your return with audit-ready data.

---

## 🚀 Core Features

### 1. Smart Data Ingestion & Normalization
* **Intelligent Import Engine:** Seamlessly handles Excel/CSV exports with a built-in "translation layer" that maps custom headers (e.g., 'Start Time' -> 'start_time').
* **MD5 Deduplication:** Uses unique cryptographic hashing (Unique Hash logic) to prevent duplicate entries, even if you upload the same Excel sheet multiple times.
* **Time Normalization:** Built-in regex logic allows for flexible time entry (e.g., "9am", "1700", or "5:30pm") and automatically converts it to a standard database format.

### 2. ATO-Compliant Tax Logic
* **Financial Year Awareness:** Automatically calculates and filters data based on the Australian Fiscal Year (July 1 – June 30) for precise reporting.
* **Dual-Method Comparison:** * **Fixed Rate Method:** Calculates claims based on the current ATO rate (e.g., $0.67/hr).
    * **Actual Cost Method:** Allows manual input of utilities and work-use percentages to see which method yields a higher return.
* **Deductible Hour Breakdown:** Tracks Base WFH hours, "After Hours" support, and Overtime separately for granular tax claims.

### 3. Advanced Analytics & Dashboards
* **Real-Time Header:** V2.0 includes a dynamic live date and time display in the sidebar for better logging context.
* **Work Trends:** Visualizes Office vs. WFH patterns using professional Plotly Line and Bar charts.
* **Gap Analysis:** An "Audit Mode" that identifies missing log entries within a date range to ensure no claimable day is forgotten.

### 4. Data Management Tools
* **Schedule Generator:** Quickly bulk-generate a 7-day work week (e.g., Mon-Wed Office, Thu-Fri WFH) with built-in conflict detection for existing records.
* **Bulk Editor:** Change locations, base hours, or OT for an entire month or custom date range in one click.
* **Secure Persistence:** Powered by SQLite with Docker volumes to ensure your data survives container restarts.
* **Safety Controls:** Includes a secure delete function requiring manual confirmation to wipe the database.

---

## 🛠 Tech Stack
- Frontend: Streamlit
- Backend: Python 3.9 & SQLite
- Visuals: Plotly Express
- Deployment: Docker & Docker Compose

---

## 📦 Deployment & Server Management

### 1. Prerequisites
Ensure your Ubuntu VM has Docker and Docker Compose installed. Run these commands:

# Update package list and install Docker/Compose
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker

### 2. Installation, Verification & Management
Navigate to your project directory and use the following commands to manage the application:

# --- INSTALLATION ---
# Build and start the container in the background
docker-compose up -d --build

# --- VERIFICATION ---
# Check if the container is running
docker ps

# View real-time logs (useful for debugging imports)
docker logs -f tax_tracker_v1

# --- STOPPING THE SERVICE ---
# Shut down the application while keeping your data volume safe
docker-compose down

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
