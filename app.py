from flask import Flask

app = Flask(__name__)

@app.get("/")
def hello():
    return "Hello, Harness! ✅\n"

if __name__ == "__main__":
    # Em container, normalmente você roda via gunicorn; isso é pra debug local
    app.run(host="0.0.0.0", port=8080)
