import os, requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL = "https://openrouter.ai/api/v1/chat/completions"

def ask_nabd(history_list):
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return {"ok": False, "text": "مفتاح الخدمة غير مضبوط في الخادم."}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    msgs = [{"role": "system", "content": "اسمك نبض. أجب بوضوح واختصار ودقة باللغة العربية."}]
    for m in history_list[-8:]:
        r = "user" if m.get("role") == "u" else "assistant"
        t = (m.get("text") or "").strip()
        if t:
            msgs.append({"role": r, "content": t[:800]})
    try:
        r = requests.post(URL, headers=headers, json={"model": "openrouter/free", "messages": msgs, "temperature": 0.4, "max_tokens": 350}, timeout=12)
        if r.status_code != 200:
            return {"ok": False, "text": f"استجابة الخادم ({r.status_code})"}
        reply = (r.json().get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
        return {"ok": True, "text": reply} if reply else {"ok": False, "text": "لم يصل نص من النموذج."}
    except requests.Timeout:
        return {"ok": False, "text": "تأخر استجابة الشبكة بسبب ضعف الاتصال."}
    except Exception:
        return {"ok": False, "text": "انقطع الاتصال بالشبكة مؤقتاً."}

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "nabd_ui.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json or {}
    hist = data.get("history")
    if isinstance(hist, list) and hist:
        res = ask_nabd(hist)
        return jsonify({"ok": res["ok"], "reply": res["text"]})
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"ok": False, "reply": "الرسالة فارغة."})
    res = ask_nabd([{"role": "u", "text": msg}])
    return jsonify({"ok": res["ok"], "reply": res["text"]})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=False)
