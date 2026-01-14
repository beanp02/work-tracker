FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create persistence directory
RUN mkdir -p /app/data

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]