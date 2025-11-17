from flask import Flask, render_template, request, jsonify
import json
import ast
import operator as op
import requests
import re
import time
import os

app = Flask(__name__)

# ⛔ DELETE your old key — replace with a new one here
OPENROUTER_API_KEY =os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"

ops = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow
}

waiting_for_answer = {}

# -----------------------
# Safe math evaluation
# -----------------------
def safe_math(expr: str):
    expr = expr.replace("^", "")
    try:
        node = ast.parse(expr, mode='eval').body
    except:
        return None

    def _eval(n):
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            return ops[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        return None

    try:
        return _eval(node)
    except:
        return None

# -----------------------
# Weather API
# -----------------------
def get_weather(city: str):
    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        ).json()

        if "results" not in geo:
            return "City not found."

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        city_name = geo["results"][0]["name"]

        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        ).json()

        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]

        return f"Weather in {city_name}: {temp}°C, Wind {wind} km/h"
    except:
        return "Weather error."

# -----------------------
# Knowledge base
# -----------------------
def load_know():
    try:
        with open("knowledge_base.json", "r") as f:
            return json.load(f)
    except:
        return {"questions": []}



# Extract city name
def extract_city(text):
    match = re.search(r"weather(?: in)? ([\w\s]+)", text.lower())
    return match.group(1).strip() if match else None

# -----------------------
# OpenRouter API call
# -----------------------
def ask_openrouter(prompt):
    for attempt in range(3):
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:5000", 
                "X-Title": "My Flask Chatbot",
                "Content-Type": "application/json"
            }

            data = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ]
            }

            response = requests.post(OPENROUTER_URL, headers=headers, json=data)
            res = response.json()

            if "choices" in res:
                return res["choices"][0]["message"]["content"]

            print("OpenRouter error response:", res)
            time.sleep(1)

        except Exception as e:
            print("Exception:", e)
            time.sleep(1)

    return "OpenRouter API failed after 3 attempts."

# -----------------------
# Routes
# -----------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json["message"].strip()
    kb = load_know()

    # Learning mode (optional)
    if "session" in waiting_for_answer:
        question = waiting_for_answer.pop("session")
        kb["questions"].append({"questions": question, "answer": user_msg})
        (kb)
        return jsonify({"response": "Thanks! Learned something new."})

    # Weather intent
    if "weather" in user_msg.lower():
        city = extract_city(user_msg) or "Delhi"
        return jsonify({"response": get_weather(city)})

    # Math
    math_result = safe_math(user_msg)
    if math_result is not None:
        return jsonify({"response": str(math_result)})

    # Check stored knowledge (manual entries)
    for q in kb["questions"]:
        if user_msg.lower() == q["questions"].lower():
            return jsonify({"response": q["answer"]})

    # Ask OpenRouter AI (no saving)
    answer = ask_openrouter(user_msg)

    return jsonify({"response": answer})

# -----------------------
# Run server
# -----------------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
