FROM python:3.10-slim

WORKDIR /app

COPY . .


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8503

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0"]
