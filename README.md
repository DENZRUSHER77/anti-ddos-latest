# Anti-DDoS Stack Latest 🛡️

Stack lengkap anti-DDoS modern dengan lapisan pertahanan multiple:

## 🏗️ Arsitektur

```
Internet
    ↓
[Cloudflare/Edge CDN] (Optional - Layer 3/4)
    ↓
[Nginx + Rate Limit + WAF] → [Fail2Ban] → [CrowdSec]
    ↓
[Flask App + Redis Rate Limit] → [Redis]
    ↓
[Prometheus + Grafana] (Monitoring & Alerting)
```

## 🎯 5 Lapisan Pertahanan

| Layer | Tools | Fungsi |
|-------|-------|--------|
| **1. Edge** | Cloudflare / AWS Shield | Filter volumetric DDoS, bot management |
| **2. Reverse Proxy** | Nginx + Rate Limit + WAF | Rate limit per IP, blokir pattern serangan |
| **3. Host IDS** | Fail2Ban | Ban IP otomatis dari log Nginx |
| **4. Threat Intel** | CrowdSec | Crowd-sourced threat intelligence, auto-block |
| **5. App-Level** | Flask Middleware + Redis | Rate limit per user/IP, deteksi anomali |
| **6. Monitoring** | Prometheus + Grafana | Alert real-time, dashboard visualisasi |

## 🚀 Quick Start

```bash
cd anti-ddos-latest
chmod +x scripts/setup.sh
./scripts/setup.sh
```

Atau manual:

```bash
docker-compose pull
docker-compose build app
docker-compose up -d
```

## 📊 Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| Nginx | http://localhost | - |
| Flask App | http://localhost/api/data | - |
| Health Check | http://localhost/health | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin / admin |

## ⚙️ Konfigurasi Utama

### Rate Limit (nginx/rate-limit.conf)
```nginx
limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;  # 10 req/s per IP
limit_req zone=one burst=20 nodelay;
```

### Login Rate Limit (lebih ketat)
```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=2r/s;  # 2 req/s
limit_req zone=login burst=5 nodelay;
```

### WAF Rules (nginx/waf.conf)
- Blokir User-Agent bot/scanner
- Blokir SQLi, path traversal
- Blokir query string mencurigakan
- Blokir HTTP method berbahaya

### App Middleware (app/middleware.py)
```python
RATE_LIMIT_REQUESTS = 60   # per menit
RATE_LIMIT_WINDOW = 60     # detik
LOGIN_RATE_LIMIT = 2       # percobaan login per menit
```

### CrowdSec Collections (crowdsec/acquis.yaml)
- linux, nginx, http-crawl-non_statics
- http-bad-user-agent, http-probing
- http-backdoors-attempts, http-sensitive-files
- http-vuln-wordpress, http-vuln-generic
- http-php-csrf-protection-circumvention

### Fail2Ban Jails (fail2ban/jail.local)
- nginx-http-auth (3 retry)
- nginx-limit-req (10 retry/60s)
- nginx-botsearch (2 retry)
- nginx-scan (5 retry)
- nginx-404 (10 retry/60s)
- custom-bad-ua (1 retry/60s)

## 📈 Alerts (alerts/alerts.yml)

| Alert | Threshold | Severity |
|-------|-----------|----------|
| NginxRateLimitExceeded | >0 rate 429/403 | warning |
| HighTrafficSpike | >5000 req/5m | critical |
| HighErrorRate | >5% 5xx | warning |
| RedisMemoryHigh | >200MB | warning |
| BruteForceLogin | >10 req/s /login | critical |
| CrowdSecDecision | >0 decisions | critical |
| Fail2BanBanned | >0 banned | warning |

## 🛠️ Commands

```bash
# Status
docker-compose ps

# Logs
docker-compose logs -f nginx
docker-compose logs -f crowdsec
docker-compose logs -f fail2ban

# Block IP manual
./scripts/block-ip.sh 192.168.1.100 "Brute force attempt"

# Unban IP
fail2ban-client set custom-bad-ua unbanip 192.168.1.100
cscli decisions delete --ip 192.168.1.100
iptables -D INPUT -s 192.168.1.100 -j DROP

# Check crowdsec decisions
cscli decisions list

# Check fail2ban status
fail2ban-client status
fail2ban-client status custom-bad-ua

# Restart
docker-compose restart

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache app
docker-compose up -d
```

## 📝 Runbook

Lihat `runbook.md` untuk incident response procedures.

## 🔧 Customization

### Rate Limit
Edit `nginx/rate-limit.conf` dan `app/middleware.py`

### WAF Patterns
Edit `nginx/waf.conf` - tambah/hapus regex

### Alert Thresholds
Edit `alerts/alerts.yml`

### CrowdSec Collections
Edit `docker-compose.yml` environment `COLLECTIONS`

### Grafana Dashboard
Import dashboard ID 12559 (Nginx) atau buat custom

## 📦 Production Checklist

- [ ] Ganti Grafana password di `docker-compose.yml`
- [ ] Setup SSL/TLS (Certbot) di Nginx
- [ ] Integrasikan Cloudflare/Edge CDN
- [ ] Set Redis persistent storage
- [ ] Setup Prometheus remote write / alerting channels (Slack, Discord, Email)
- [ ] Tuning rate limit berdasarkan traffic normal
- [ ] Setup CrowdSec bouncer untuk nginx/iptables
- [ ] Harden Docker (read-only, no-new-privileges)
- [ ] Backup konfigurasi

## 🔗 Referensi

- [CrowdSec Docs](https://docs.crowdsec.net/)
- [Fail2Ban Wiki](https://github.com/fail2ban/fail2ban/wiki)
- [Nginx Rate Limiting](https://docs.nginx.com/nginx/admin-guide/security-controls/controlling-access-proxied-http/)
- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/)