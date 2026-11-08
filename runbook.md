# Anti-DDoS Incident Response Runbook

## 🚨 Incident Classification

| Level | Criteria | Response Time | Escalation |
|-------|----------|---------------|------------|
| **P1 - Critical** | Volumetric DDoS >10Gbps, service down | <5 min | On-call + Team Lead |
| **P2 - High** | Application layer DDoS, high error rate, brute force | <15 min | On-call |
| **P3 - Medium** | Suspicious traffic spike, failed login attempts | <1 hour | Next business day |
| **P4 - Low** | Single IP blocked, minor anomalies | <4 hours | Next business day |

---

## 🔍 Detection

### Auto-Detection (Prometheus Alerts)
```bash
# Cek alert yang firing
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# Atau via Grafana UI
http://localhost:3000/alerting
```

### Manual Detection Commands
```bash
# Cek rate limit hits
docker-compose logs nginx | grep "limiting requests"

# Cek 403/429 responses
docker-compose logs nginx | grep -E " 403 | 429 "

# Cek crowdsec decisions
docker-compose exec crowdsec cscli decisions list

# Cek fail2ban banned
docker-compose exec fail2ban fail2ban-client status custom-bad-ua

# Cek active connections
docker-compose exec nginx ss -tunap | grep :80

# Top IPs by request count
docker-compose logs nginx | awk '{print $1}' | sort | uniq -c | sort -rn | head -20
```

---

## ⚡ Response Procedures

### P1 - Volumetric DDoS (Network Layer)

**Immediate Actions (<5 min):**
1. **Enable Cloudflare "Under Attack Mode"** atau AWS Shield Advanced
2. **Activate WAF rate limiting** di edge
3. **Block geographic regions** jika attack dari negara tertentu
4. **Scale up bandwidth** (contact ISP/CDN)

```bash
# Quick block suspicious subnet
./scripts/block-ip.sh 203.0.113.0/24 "Volumetric DDoS subnet"

# Or via iptables directly
iptables -I INPUT -s 203.0.113.0/24 -j DROP
```

**Communication:**
- Notify team via Slack/Discord #incidents
- Update status page
- Contact CDN/ISP support

### P2 - Application Layer DDoS (HTTP Flood)

**Immediate Actions (<15 min):**
1. **Analyze attack pattern** - path, user-agent, query params
2. **Tighten Nginx rate limits**:
```bash
# Edit nginx/rate-limit.conf
limit_req_zone $binary_remote_addr zone=one:10m rate=5r/s;  # Reduce from 10
limit_req zone=one burst=10 nodelay;  # Reduce burst
docker-compose restart nginx
```
3. **Add specific WAF rule** untuk pattern attack:
```nginx
# nginx/waf.conf - add specific pattern
if ($request_uri ~* "/api/v1/expensive-endpoint") {
    limit_req zone=one burst=5 nodelay;
}
```
4. **Enable CrowdSec custom collection** untuk pattern
5. **Block top attacking IPs**:
```bash
# Get top 50 IPs
docker-compose logs nginx | awk '{print $1}' | sort | uniq -c | sort -rn | head -50 > /tmp/top_ips.txt

# Block them
while read count ip; do
    ./scripts/block-ip.sh "$ip" "HTTP flood - $count req"
done < /tmp/top_ips.txt
```

### P3 - Brute Force / Credential Stuffing

**Actions (<1 hour):**
1. **Verify alerts** - BruteForceLogin firing
2. **Check targeted accounts**:
```bash
docker-compose logs app | grep -i "login" | grep -i "fail"
```
3. **Tighten login rate limit**:
```bash
# app/middleware.py
LOGIN_RATE_LIMIT = 1  # Reduce from 2
LOGIN_WINDOW = 300    # Increase window to 5 min
docker-compose restart app
```
4. **Enable CAPTCHA** pada login endpoint
5. **Block attacking IPs** via fail2ban/crowdsec
6. **Force password reset** untuk compromised accounts

### P4 - Suspicious Anomaly

**Actions (<4 hours):**
1. **Investigate source** - single IP? botnet? misconfigured client?
2. **Review logs** untuk pattern
3. **Adjust thresholds** jika false positive
4. **Document** untuk tuning

---

## 🔄 Recovery

### Verify Service Restored
```bash
# Health check
curl -s http://localhost/health
curl -s http://localhost/api/data | head -5

# Check error rate
curl -s "http://localhost:9090/api/v1/query?query=rate(nginx_http_requests_total{status=~\"5..\"}[5m])"

# Check rate limit
curl -s "http://localhost:9090/api/v1/query?query=rate(nginx_http_requests_total{status=~\"429|403\"}[5m])"
```

### Remove Temporary Blocks
```bash
# Review blocks
cscli decisions list
fail2ban-client status

# Remove specific IP if false positive
cscli decisions delete --ip 192.168.1.100
fail2ban-client set custom-bad-ua unbanip 192.168.1.100
iptables -D INPUT -s 192.168.1.100 -j DROP
```

### Restore Rate Limits
```bash
# Revert nginx/rate-limit.conf to normal values
# Restart nginx
docker-compose restart nginx
```

---

## 📋 Post-Incident

### Within 24 Hours
- [ ] Root Cause Analysis (RCA) draft
- [ ] Timeline of events
- [ ] Impact assessment (downtime, users affected)
- [ ] Block list review (false positives?)

### Within 48 Hours
- [ ] Final RCA document
- [ ] Action items untuk prevention
- [ ] Update runbook jika gap ditemukan
- [ ] Update WAF rules / rate limits
- [ ] Update CrowdSec collections
- [ ] Team retrospective

### Prevention Improvements
- [ ] Add new WAF rules untuk attack pattern
- [ ] Tune rate limits berdasarkan normal traffic
- [ ] Add new Prometheus alerts
- [ ] Update Grafana dashboard
- [ ] Test failover / scaling
- [ ] Update documentation

---

## 📞 Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| On-call Engineer | @oncall-slack | P1/P2 |
| Team Lead | @teamlead-slack | P1 |
| Infrastructure | @infra-slack | P1/P2 |
| Security | @security-slack | P1 |
| CDN/Cloudflare | Support ticket | P1 |
| ISP | Emergency line | P1 |

---

## 🛠️ Quick Reference Cards

### Block IP (All Layers)
```bash
./scripts/block-ip.sh <IP> "Reason"
# Does: iptables + fail2ban + crowdsec
```

### Check All Banned IPs
```bash
echo "=== IPTABLES ===" && iptables -L INPUT -n | grep DROP
echo "=== FAIL2BAN ===" && docker-compose exec fail2ban fail2ban-client status
echo "=== CROWDSEC ===" && docker-compose exec crowdsec cscli decisions list
```

### Emergency Rate Limit (Nginx)
```bash
# Ultra strict
sed -i 's/rate=10r/s/rate=2r/s/' nginx/rate-limit.conf
sed -i 's/burst=20/burst=5/' nginx/rate-limit.conf
docker-compose restart nginx
```

### View Live Traffic
```bash
# Nginx access log
docker-compose logs -f nginx | grep -E "POST|GET"

# App logs
docker-compose logs -f app

# Redis keys
docker-compose exec redis redis-cli KEYS "rate:*"
```

---

## 📝 Incident Log Template

```markdown
## Incident: [ID] - [Date]

**Classification:** P1/P2/P3/P4
**Status:** Investigating / Mitigating / Recovering / Resolved
**Start Time:** 
**End Time:** 
**Duration:** 

### Summary
[1-2 sentences]

### Impact
- Users affected:
- Services degraded:
- Revenue impact:

### Timeline
- HH:MM - Detection (alert/user report)
- HH:MM - Response started
- HH:MM - Mitigation applied
- HH:MM - Service restored
- HH:MM - Post-incident review

### Root Cause
[Technical details]

### Actions Taken
- [Action 1]
- [Action 2]

### Prevention
- [Improvement 1]
- [Improvement 2]

### Links
- Grafana dashboard:
- Prometheus alerts:
- Logs:
- RCA document:
```

---

**Last Updated:** $(date)
**Version:** 1.0
**Owner:** Platform Team