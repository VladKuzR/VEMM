FROM python:3.9-slim

WORKDIR /app

COPY . .


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8502

ENTRYPOINT ["streamlit", "run", "1_Project_Dashboard.py", "--server.port=8502", "--server.address=0.0.0.0"]
