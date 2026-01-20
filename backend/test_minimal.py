from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({'message': 'Hello World'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🚀 Starting minimal Flask test server...")
    print("📍 Will run on http://127.0.0.1:5000")
    print("🔍 Debug mode: ON")
    print("⏳ Waiting for connections...")
    try:
        # Use default Flask port 5000
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🛑 Server stopped")
