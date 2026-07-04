FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
