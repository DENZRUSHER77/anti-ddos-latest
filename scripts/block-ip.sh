#!/bin/bash
# Script untuk block IP manual (via fail2ban / crowdsec / iptables)
# Usage: ./block-ip.sh <IP> [reason]

set -e

IP="$1"
REASON="${2:-Manual block}"

if [ -z "$IP" ]; then
    echo "Usage: $0 <IP> [reason]"
    exit 1
fi

echo "🔒 Blocking IP: $IP (Reason: $REASON)"

# Block via iptables
iptables -I INPUT -s "$IP" -j DROP 2>/dev/null || true
ip6tables -I INPUT -s "$IP" -j DROP 2>/dev/null || true

# Add to fail2ban
fail2ban-client set custom-bad-ua banip "$IP" 2>/dev/null || true
fail2ban-client set nginx-limit-req banip "$IP" 2>/dev/null || true

# Add to crowdsec (if running)
cscli decisions add --ip "$IP" --reason "$REASON" --duration 24h 2>/dev/null || true

echo "✅ IP $IP diblokir"
echo "📝 Cek: iptables -L INPUT -n | grep $IP"