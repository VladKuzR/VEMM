FROM python:3.9-slim

WORKDIR /app

COPY . .


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "1_Project_Dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
