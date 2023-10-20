FROM python:3.12.0b1-slim
WORKDIR /functional

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD sleep 10 && python prepare_env.py && python -m pytest . --html=report/pytest_report.html
