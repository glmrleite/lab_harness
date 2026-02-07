# lab_harness

## Run local
python -m venv .venv
# Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
python app.py

## Run with Docker
docker build -t lab_harness:local .
docker run -p 8080:8080 lab_harness:local
