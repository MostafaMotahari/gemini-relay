FROM docker.arvancloud.ir/python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip config --user set global.index https://mirror-pypi.runflare.com/simple
RUN pip config --user set global.index-url https://mirror-pypi.runflare.com/simple
RUN pip config --user set global.trusted-host mirror-pypi.runflare.com
run pip config --user set global.timeout 60
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]