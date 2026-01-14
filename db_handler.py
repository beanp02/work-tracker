import sqlite3
import pandas as pd
import hashlib
import os

DB_FOLDER = "data"
DB_PATH = os.path.join(DB_FOLDER, "work_data.db")

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

def generate_hash(row):
    """Generates a unique hash to prevent duplicate imports."""
    date_str = str(row.get('date', ''))
    # Ensure consistency by stripping whitespace
    start_str = str(row.get('start_time', '')).strip().lower()
    finish_str = str(row.get('finish_time', '')).strip().lower()
    loc_str = str(row.get('location', '')).strip()
    raw_string = f"{date_str}{start_str}{finish_str}{loc_str}"
    return hashlib.md5(raw_string.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS work_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP,
            location TEXT,
            start_time TEXT,
            finish_time TEXT,
            break_duration TEXT,
            base_hours REAL,
            ot_hours REAL,
            unique_hash TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def insert_data(df):
    if df.empty:
        return 0

    conn = sqlite3.connect(DB_PATH)
    
    # Generate hashes if not present
    if 'unique_hash' not in df.columns:
        df['unique_hash'] = df.apply(generate_hash, axis=1)
    
    # [cite_start]Check existing hashes [cite: 1]
    try:
        existing_hashes = pd.read_sql("SELECT unique_hash FROM work_logs", conn)['unique_hash'].tolist()
    except:
        existing_hashes = []
    
    # Filter duplicates
    new_data = df[~df['unique_hash'].isin(existing_hashes)]
    
    if not new_data.empty:
        new_data.to_sql('work_logs', conn, if_exists='append', index=False)
    
    conn.close()
    return len(new_data)

def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM work_logs", conn)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()

def check_dates_exist(start_date, end_date):
    """
    Returns a list of dates within the range that already exist in the DB.
    Used for Feature 1.1: Conflict Detection.
    """
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT date FROM work_logs WHERE date BETWEEN ? AND ?"
    try:
        df = pd.read_sql(query, conn, params=(start_date, end_date))
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            return df['date'].dt.date.tolist()
        return []
    except Exception:
        return []
    finally:
        conn.close()

# --- CRUD FUNCTIONS ---

def update_record(id, field, value):
    """Updates a single field for a record."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = f"UPDATE work_logs SET {field} = ? WHERE id = ?"
    c.execute(query, (value, id))
    conn.commit()
    conn.close()

def bulk_update_range(start_date, end_date, field, value):
    """
    Updates a specific field for all records within a date range.
    Used for Feature 2.2: Bulk Edit Mode.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = f"UPDATE work_logs SET {field} = ? WHERE date BETWEEN ? AND ?"
    c.execute(query, (value, start_date, end_date))
    rows = c.rowcount
    conn.commit()
    conn.close()
    return rows

def delete_record(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM work_logs WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def clear_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM work_logs")
    conn.commit()
    conn.close()