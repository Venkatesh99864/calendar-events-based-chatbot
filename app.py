from flask import Flask, request, jsonify, render_template
from chatbot import handle_request

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
  return render_template("index.html")


@app.post("/chat")
def chat():
  data = request.get_json(force=True) or {}
  result = handle_request(data)
  return jsonify(result)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8000, debug=True)
