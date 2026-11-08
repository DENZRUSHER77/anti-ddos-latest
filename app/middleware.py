"""
Flask middleware anti-DDoS terbaru dengan Redis & crowdsec integration.
"""

from flask import Flask, request, jsonify
import time
import os
from functools import wraps

app = Flask(__name__)

# Redis connection
import redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)

# Load config
def get_config(key, default):
    return int(os.getenv(key, default))

RATE_LIMIT_REQUESTS = get_config('RATE_LIMIT_REQUESTS', 60)
RATE_LIMIT_WINDOW = get_config('RATE_LIMIT_WINDOW', 60)
LOGIN_RATE_LIMIT = get_config('LOGIN_RATE_LIMIT', 2)
LOGIN_WINDOW = get_config('LOGIN_WINDOW', 60)

# Utility functions
def rate_limit(key, limit, window):
    """Return True if request allowed, False if blocked"""
    current = redis_client.get(key)
    now = int(time.time())
    if current is None:
        redis_client.setex(key, window, str(1))
        return True
    else:
        requests = int(current)
        if requests < limit:
            redis_client.incr(key)
            return True
        else:
            return False

def get_client_ip():
    # Support for crowdsec / fail2ban
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        return xff.split(',')[0]
    return request.remote_addr

# Middleware decorator
def anti_ddos(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        client_ip = get_client_ip()

        # Rate limit untuk semua endpoint
        if not rate_limit(f"rate:{client_ip}", RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW):
            return jsonify({
                "error": "Rate limit exceeded",
                "retry_after": RATE_LIMIT_WINDOW
            }), 429

        # Special rate limit untuk login
        if request.path == '/login':
            login_key = f"login:{client_ip}"
            if not rate_limit(login_key, LOGIN_RATE_LIMIT, LOGIN_WINDOW):
                return jsonify({
                    "error": "Too many login attempts",
                    "retry_after": LOGIN_WINDOW
                }), 429

        # Basic user-agent check
        user_agent = request.headers.get('User-Agent', '').lower()
        suspicious_agents = ['curl', 'wget', 'python-requests', 'python-urllib', 'sqlmap', 'nikto', 'nmap', 'masscan']
        if any(sa in user_agent for sa in suspicious_agents):
            return jsonify({"error": "Suspicious User-Agent detected"}), 403

        return f(*args, **kwargs)
    return decorated

# Endpoint contoh
@app.route('/')
@anti_ddos
def home():
    return jsonify({"message": "Anti-DDoS Flask app"})

@app.route('/api/data')
@anti_ddos
def data():
    return jsonify({"data": list(range(1000))})

@app.route('/login', methods=['POST'])
@anti_ddos
def login():
    # Basic login (ganti dengan DB)
    data = request.get_json() or {}
    if data.get('username') == 'admin' and data.get('password') == 'admin':
        return jsonify({"message": "Login success"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
