# 🇦🇺 Australian Work & Tax Tracker
### **Maximize your tax return with data-driven WFH logging.**

The **Australian Work & Tax Tracker** is a production-ready Streamlit application designed for employees and contractors under the Australian tax system. It simplifies the tedious process of tracking WFH hours, office days, and overtime to ensure you claim every cent possible under ATO guidelines.

---

## 🚀 Core Features

### 1. Smart Data Ingestion
* **Messy Import Engine:** Handles Excel/CSV exports from various work-logging apps with intelligent column mapping.
* **MD5 Deduplication:** Advanced hashing (based on date, time, and location) ensures that importing the same file twice won't duplicate your records.
* **Time Normalization:** Intelligent input parsing converts varied inputs (e.g., "9am", "1730", or "5pm") into standard database formats automatically to maintain data integrity.

### 2. ATO-Compliant Tax Logic
* **FY Cycle Awareness:** Automatically groups and filters data into Australian Financial Year cycles (July 1 – June 30).
* **Dual-Method Comparison:** * **Fixed Rate Method:** Automatically calculates claims based on the current ATO rate (e.g., **$0.67/hr**).
    * **Actual Cost Method:** Input utilities (Electricity, Internet) and usage percentages to compare which method yields a higher return.
* **Deductible Hour Breakdown:** Specifically tracks Base WFH hours, After Hours, and Overtime.

### 3. Advanced Analytics & Dashboards
* **Multi-Month Filtering:** Drill down into specific months or quarters (e.g., July–Sept) for precise reporting.
* **Year-over-Year Comparison:** Toggle an overlay to compare current WFH patterns against previous years to identify shifts in work habits.
* **Gap Analysis:** An "Audit Mode" that scans your database for missing log entries within a date range, ensuring no claimable day is forgotten.

### 4. Enterprise-Grade Data Management
* **Bulk Edit Mode:** Change the location status (e.g., "Annual Leave") for an entire date range in one click.
* **Schedule Generator:** Tool to bulk-generate "expected" weekly logs (e.g., Mon-Wed Office, Thu-Fri WFH) with built-in conflict detection for existing records.
* **Persistent Storage:** Built on SQLite with Docker Volume

## Tech Stack
- Python 3.9, Streamlit, SQLite, Docker.

## 📦 Deployment & Server Management

### 1. Prerequisites
Ensure your Ubuntu VM has Docker and Docker Compose installed:
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker

### 2. Installation
docker-compose up -d --build

### 3. Verification
# Check container status
docker ps

# View real-time logs (useful for debugging imports)
docker logs -f tax_tracker_v1

### 4. Stopping the service
docker-compose down

