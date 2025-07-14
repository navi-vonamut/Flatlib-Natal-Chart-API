FROM python:3.11-slim

RUN apt update && apt install -y gcc build-essential libffi-dev zlib1g-dev

RUN pip install --upgrade pip

RUN pip install flatlib==0.2.3 pyswisseph==2.8.0.post1 flask

WORKDIR /app

COPY main.py .

CMD ["python", "main.py"]