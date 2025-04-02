# tools/dns_resolver_best.py

import socket
import dns.resolver
import dns.query
import dns.message
import dns.rdatatype
import requests
import urllib.parse
import subprocess
import struct
import pycurl
from io import BytesIO
import json
import argparse
import re
from dns.exception import DNSException
from dns.resolver import Resolver
try:
    import websocket
except ImportError:
    websocket = None
try:
    from scapy.all import traceroute
except ImportError:
    traceroute = None
try:
    import paramiko
except ImportError:
    paramiko = None

def resolve_domain(domain, test_all=False, quick=False, json_output=False, stop_at_first=False):
    print(f"[🧠 DNS] 🧪 Résolution de {domain}...")
    results = {}
    all_ips = []

    quick_methods = [
        "socket.gethostbyname", "fallback_8.8.8.8", "doh_google", "cloudflare_api",
        "dot_8.8.8.8", "dig_8.8.8.8", "icmp_ping", "http_leak"
    ]

    def should_run(method):
        return not quick or method in quick_methods

    def stop_if_found():
        return stop_at_first and len(all_ips) > 0

    # Méthode 1 : Résolution classique
    if should_run("socket.gethostbyname"):
        try:
            ip = socket.gethostbyname(domain)
            print(f"[🧠 DNS] ✅ socket.gethostbyname: {ip}")
            results["socket.gethostbyname"] = [ip]
            all_ips.extend([ip])
            if stop_if_found(): return all_ips
            if not test_all and not quick:
                return all_ips
        except Exception as e:
            print(f"[🧠 DNS] ❌ socket.gethostbyname: {e}")
            results["socket.gethostbyname"] = None

    # Méthode 2 : Résolution DNS avec fallbacks multiples
    if should_run("fallback_8.8.8.8"):
        for nameserver in ["8.8.8.8", "1.1.1.1", "9.9.9.9", "8.8.4.4", "94.140.14.14"]:
            try:
                resolver = Resolver(configure=False)
                resolver.nameservers = [nameserver]
                resolver.timeout = 5
                resolver.lifetime = 5
                answers = resolver.resolve(domain, "A")
                ips = [answer.address for answer in answers]
                print(f"[🧠 DNS] ✅ Fallback DNS {nameserver}: {ips}")
                results[f"fallback_{nameserver}"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            except DNSException as e:
                print(f"[🧠 DNS] ⚠️ Fallback DNS {nameserver}: {e}")
                results[f"fallback_{nameserver}"] = None
            if nameserver != "8.8.8.8" and quick:
                break  # Limiter à 8.8.8.8 pour --quick

    # Méthode 3 : DNS-over-HTTPS (Google)
    if should_run("doh_google"):
        try:
            url = f"https://dns.google/resolve?name={urllib.parse.quote(domain)}&type=A"
            headers = {"accept": "application/dns-json"}
            r = requests.get(url, timeout=5, headers=headers)
            r.raise_for_status()
            data = r.json()
            ips = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
            if ips:
                print(f"[🧠 DNS] ✅ DoH (dns.google): {ips}")
                results["doh_google"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ DoH (Google): Réponse vide")
                results["doh_google"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ DoH (Google): {e}")
            results["doh_google"] = None

    # Méthode 4 : DNS-over-HTTPS (Cloudflare API)
    if should_run("cloudflare_api"):
        try:
            url = f"https://1.1.1.1/dns-query?name={urllib.parse.quote(domain)}&type=A"
            headers = {"accept": "application/dns-json"}
            r = requests.get(url, timeout=5, headers=headers)
            r.raise_for_status()
            data = r.json()
            ips = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
            if ips:
                print(f"[🧠 DNS] ✅ Cloudflare API: {ips}")
                results["cloudflare_api"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ Cloudflare API: Réponse vide")
                results["cloudflare_api"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ Cloudflare API: {e}")
            results["cloudflare_api"] = None

    # Méthode 5 : DNS over TLS (DoT)
    if should_run("dot_8.8.8.8"):
        try:
            q = dns.message.make_query(domain, dns.rdatatype.A)
            response = dns.query.tls(q, "8.8.8.8", port=853, timeout=5)
            ips = [rdata.address for rdata in response.answer[0] if rdata.rdtype == dns.rdatatype.A]
            print(f"[🧠 DNS] ✅ DoT (8.8.8.8): {ips}")
            results["dot_8.8.8.8"] = ips
            all_ips.extend(ips)
            if stop_if_found(): return all_ips
            if not test_all and not quick:
                return all_ips
        except Exception as e:
            print(f"[🧠 DNS] ❌ DoT: {e}")
            results["dot_8.8.8.8"] = None

    # Méthode 6 : Commande dig
    if should_run("dig_8.8.8.8"):
        try:
            result = subprocess.run(
                ["dig", "+short", domain, "@8.8.8.8", "A"],
                capture_output=True,
                text=True,
                timeout=5
            )
            ips = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            if ips:
                print(f"[🧠 DNS] ✅ dig @8.8.8.8: {ips}")
                results["dig_8.8.8.8"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ dig: Réponse vide")
                results["dig_8.8.8.8"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ dig: {e}")
            results["dig_8.8.8.8"] = None

    # Méthode 7 : DoH avec pycurl
    if should_run("doh_pycurl"):
        try:
            buffer = BytesIO()
            c = pycurl.Curl()
            c.setopt(c.URL, f"https://dns.google/resolve?name={urllib.parse.quote(domain)}&type=A")
            c.setopt(c.WRITEDATA, buffer)
            c.setopt(c.HTTPHEADER, ["accept: application/dns-json"])
            c.setopt(c.TIMEOUT, 5)
            c.perform()
            c.close()
            data = json.loads(buffer.getvalue().decode("utf-8"))
            ips = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
            if ips:
                print(f"[🧠 DNS] ✅ DoH (pycurl): {ips}")
                results["doh_pycurl"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ DoH (pycurl): Réponse vide")
                results["doh_pycurl"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ DoH (pycurl): {e}")
            results["doh_pycurl"] = None

    # Méthode 8 : Commande nslookup
    if should_run("nslookup_8.8.8.8"):
        try:
            result = subprocess.run(
                ["nslookup", domain, "8.8.8.8"],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.splitlines()
            ips = [line.split()[-1] for line in lines if "Address:" in line and "." in line.split()[-1] and "8.8.8.8" not in line]
            if ips:
                print(f"[🧠 DNS] ✅ nslookup @8.8.8.8: {ips}")
                results["nslookup_8.8.8.8"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ nslookup: Réponse vide")
                results["nslookup_8.8.8.8"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ nslookup: {e}")
            results["nslookup_8.8.8.8"] = None

    # Méthode 9 : Requête DNS manuelle via UDP
    if should_run("manual_udp"):
        try:
            transaction_id = 0x1234
            flags = 0x0100
            questions = 1
            header = struct.pack(">HHHHHH", transaction_id, flags, questions, 0, 0, 0)
            qname = b"".join(bytes([len(part)]) + part.encode() for part in domain.split(".")) + b"\x00"
            qtype = 1
            qclass = 1
            question = qname + struct.pack(">HH", qtype, qclass)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.sendto(header + question, ("8.8.8.8", 53))
            data, _ = sock.recvfrom(1024)
            sock.close()

            ips = []
            offset = len(header + question)
            for _ in range(questions):
                while offset < len(data):
                    if data[offset] == 0xC0:
                        offset += 2
                    else:
                        offset += 1
                    if offset + 10 <= len(data):
                        rtype, rclass, ttl, rdlength = struct.unpack(">HHlH", data[offset:offset+10])
                        offset += 10
                        if rtype == 1 and rclass == 1:
                            ip = ".".join(map(str, data[offset:offset+4]))
                            ips.append(ip)
                        offset += rdlength
                    else:
                        break
            if ips:
                print(f"[🧠 DNS] ✅ Manual UDP: {ips}")
                results["manual_udp"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ Manual UDP: Réponse vide")
                results["manual_udp"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ Manual UDP: {e}")
            results["manual_udp"] = None

    # Méthode 10 : ICMP (Ping)
    if should_run("icmp_ping"):
        try:
            result = subprocess.run(
                ["ping", "-c", "1", domain],
                capture_output=True,
                text=True,
                timeout=5
            )
            first_line = result.stdout.splitlines()[0]
            ip = first_line.split("(")[1].split(")")[0] if "(" in first_line else None
            if ip and "." in ip:
                print(f"[🧠 DNS] ✅ ICMP Ping: {ip}")
                results["icmp_ping"] = [ip]
                all_ips.extend([ip])
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ ICMP Ping: Réponse vide")
                results["icmp_ping"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ ICMP Ping: {e}")
            results["icmp_ping"] = None

    # Méthode 11 : HTTP Headers Leak
    if should_run("http_leak"):
        try:
            r = requests.get(f"http://{domain}", timeout=5, allow_redirects=True)
            final_host = urllib.parse.urlparse(r.url).hostname
            ip = socket.gethostbyname(final_host)
            if ip:
                print(f"[🧠 DNS] ✅ HTTP Headers Leak: {ip}")
                results["http_leak"] = [ip]
                all_ips.extend([ip])
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ HTTP Headers Leak: Pas d'IP trouvée")
                results["http_leak"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ HTTP Headers Leak: {e}")
            results["http_leak"] = None

    # Méthode 12 : SMTP MX Lookup
    if should_run("smtp_mx"):
        try:
            resolver = Resolver(configure=False)
            resolver.nameservers = ["8.8.8.8"]
            resolver.timeout = 5
            resolver.lifetime = 5
            mx_answers = resolver.resolve(domain, "MX")
            ips = []
            for mx in mx_answers:
                mx_host = str(mx.exchange).rstrip(".")
                try:
                    a_answers = resolver.resolve(mx_host, "A")
                    mx_ips = [answer.address for answer in a_answers]
                    ips.extend(mx_ips)
                except DNSException:
                    continue
            if ips:
                print(f"[🧠 DNS] ✅ SMTP MX Lookup: {ips}")
                results["smtp_mx"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
                if not test_all and not quick:
                    return all_ips
            else:
                print("[🧠 DNS] ❌ SMTP MX Lookup: Pas d'IP trouvée")
                results["smtp_mx"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ SMTP MX Lookup: {e}")
            results["smtp_mx"] = None

    # Méthode 13 : Whois Lookup (via whois CLI)
    if should_run("whois_lookup"):
        try:
            result = subprocess.run(["whois", domain], capture_output=True, text=True, timeout=5)
            ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", result.stdout)
            valid_ips = [ip for ip in ips if not ip.startswith("0.") and not ip.startswith("127.")]
            if valid_ips:
                print(f"[🧠 DNS] ✅ Whois Lookup: {valid_ips}")
                results["whois_lookup"] = valid_ips
                all_ips.extend(valid_ips)
                if stop_if_found(): return all_ips
            else:
                print("[🧠 DNS] ❌ Whois Lookup: Pas d'IP trouvée")
                results["whois_lookup"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ Whois Lookup: {e}")
            results["whois_lookup"] = None

    # Méthode 14 : CNAME Flattening
    if should_run("cname_flattening"):
        try:
            resolver = Resolver(configure=False)
            resolver.nameservers = ["8.8.8.8"]
            resolver.timeout = 5
            resolver.lifetime = 5
            try:
                cname_answers = resolver.resolve(domain, "CNAME")
                ips = []
                for cname in cname_answers:
                    target = str(cname.target).rstrip(".")
                    a_answers = resolver.resolve(target, "A")
                    cname_ips = [answer.address for answer in a_answers]
                    ips.extend(cname_ips)
                    if stop_if_found(): return all_ips
                if ips:
                    print(f"[🧠 DNS] ✅ CNAME Flattening: {ips}")
                    results["cname_flattening"] = ips
                    all_ips.extend(ips)
                else:
                    print("[🧠 DNS] ❌ CNAME Flattening: Pas d'IP via CNAME")
                    results["cname_flattening"] = None
            except DNSException:
                print("[🧠 DNS] ❌ CNAME Flattening: Pas de CNAME")
                results["cname_flattening"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ CNAME Flattening: {e}")
            results["cname_flattening"] = None

    # Méthode 15 : Traceroute (via scapy si disponible, sinon ping -R)
    if should_run("traceroute"):
        if traceroute:
            try:
                ans, _ = traceroute(domain, maxttl=10, timeout=5, verbose=0)
                ip = ans.get_trace()[domain][-1][1] if ans else None
                if ip:
                    print(f"[🧠 DNS] ✅ Traceroute (scapy): {ip}")
                    results["traceroute"] = [ip]
                    all_ips.extend([ip])
                    if stop_if_found(): return all_ips
                else:
                    print("[🧠 DNS] ❌ Traceroute (scapy): Pas d'IP trouvée")
                    results["traceroute"] = None
            except Exception as e:
                print(f"[🧠 DNS] ❌ Traceroute (scapy): {e}")
                results["traceroute"] = None
        else:
            try:
                result = subprocess.run(
                    ["ping", "-R", "-c", "2", domain],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                lines = result.stdout.splitlines()
                ips = [re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line).group() for line in lines if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line)]
                if ips and ips[-1]:
                    print(f"[🧠 DNS] ✅ Traceroute (ping -R): {ips[-1]}")
                    results["traceroute"] = [ips[-1]]
                    all_ips.extend([ips[-1]])
                    if stop_if_found(): return all_ips
                else:
                    print("[🧠 DNS] ❌ Traceroute (ping -R): Pas d'IP trouvée")
                    results["traceroute"] = None
            except Exception as e:
                print(f"[🧠 DNS] ❌ Traceroute (ping -R): {e}")
                results["traceroute"] = None

    # Méthode 16 : HEAD CDN Request
    if should_run("head_cdn"):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((domain, 80))
            sock.send(f"HEAD / HTTP/1.1\r\nHost: {domain}\r\n\r\n".encode())
            response = sock.recv(1024).decode()
            sock.close()
            ip = socket.gethostbyname(domain)
            if ip:
                print(f"[🧠 DNS] ✅ HEAD CDN Request: {ip}")
                results["head_cdn"] = [ip]
                all_ips.extend([ip])
                if stop_if_found(): return all_ips
            else:
                print("[🧠 DNS] ❌ HEAD CDN Request: Pas d'IP trouvée")
                results["head_cdn"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ HEAD CDN Request: {e}")
            results["head_cdn"] = None

    # Méthode 17 : TXT Record Abuse
    if should_run("txt_abuse"):
        try:
            resolver = Resolver(configure=False)
            resolver.nameservers = ["8.8.8.8"]
            resolver.timeout = 5
            resolver.lifetime = 5
            txt_answers = resolver.resolve(domain, "TXT")
            ips = []
            for txt in txt_answers:
                txt_str = str(txt).strip('"')
                found_ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", txt_str)
                valid_ips = [ip for ip in found_ips if not ip.startswith("0.") and not ip.startswith("127.") and socket.inet_aton(ip)]
                ips.extend(valid_ips)
            if ips:
                print(f"[🧠 DNS] ✅ TXT Record Abuse: {ips}")
                results["txt_abuse"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
            else:
                print("[🧠 DNS] ❌ TXT Record Abuse: Pas d'IP trouvée dans TXT")
                results["txt_abuse"] = None
        except DNSException:
            print("[🧠 DNS] ❌ TXT Record Abuse: Pas de TXT")
            results["txt_abuse"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ TXT Record Abuse: {e}")
            results["txt_abuse"] = None

    # Méthode 18 : DNS ANY Record
    if should_run("any_record"):
        try:
            answers = resolver.resolve(domain, "ANY")
            ips = [a.address for a in answers if hasattr(a, "address")]
            if ips:
                print(f"[🧠 DNS] ✅ ANY Record: {ips}")
                results["any_record"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
            else:
                print("[🧠 DNS] ❌ ANY Record: Pas d'IP trouvée")
                results["any_record"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ ANY Record: {e}")
            results["any_record"] = None

    # Méthode 19 : IPv6 AAAA Lookup
    if should_run("ipv6_aaaa"):
        try:
            answers = resolver.resolve(domain, "AAAA")
            ips = [answer.address for answer in answers]
            if ips:
                print(f"[🧠 DNS] ✅ IPv6 (AAAA): {ips}")
                results["ipv6_aaaa"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
            else:
                print("[🧠 DNS] ❌ IPv6 (AAAA): Pas d'IPv6 trouvée")
                results["ipv6_aaaa"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ IPv6 (AAAA): {e}")
            results["ipv6_aaaa"] = None

    # Méthode 20 : PTR Lookup (reverse DNS)
    if should_run("ptr_lookup"):
        try:
            ip = all_ips[0] if all_ips else socket.gethostbyname(domain)
            ptr_domain = socket.gethostbyaddr(ip)[0]
            print(f"[🧠 DNS] ✅ PTR (reverse) lookup: {ptr_domain}")
            results["ptr_lookup"] = [ptr_domain]
        except Exception as e:
            print(f"[🧠 DNS] ❌ PTR lookup: {e}")
            results["ptr_lookup"] = None

    # Méthode 21 : DNSSEC (AD flag ou RRSIG check)
    if should_run("dnssec"):
        try:
            response = resolver.resolve(domain, "A", raise_on_no_answer=False)
            ad_flag = response.response.flags & 0x0020  # AD bit
            rrsig_present = any(rr.rdtype == dns.rdatatype.RRSIG for rr in response.response.answer)
            if ad_flag or rrsig_present:
                print(f"[🧠 DNS] ✅ DNSSEC: {'AD flag' if ad_flag else ''} {'+ RRSIG' if rrsig_present else ''}")
                results["dnssec"] = ["AD"] if ad_flag else []
                if rrsig_present:
                    results["dnssec"].append("RRSIG")
            else:
                print("[🧠 DNS] ❌ DNSSEC: Pas de signature détectée")
                results["dnssec"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ DNSSEC: {e}")
            results["dnssec"] = None

    # Méthode 22 : CDN Fingerprinting via HTTP Headers
    if should_run("cdn_fingerprint"):
        try:
            r = requests.head(f"http://{domain}", timeout=5, allow_redirects=True)
            cdn = []
            headers = r.headers
            if "cf-ray" in headers or "cf-cache-status" in headers:
                cdn.append("Cloudflare")
            if any("akamai" in v.lower() for v in headers.values()):
                cdn.append("Akamai")
            if any("fastly" in v.lower() for v in headers.values()):
                cdn.append("Fastly")
            if cdn:
                print(f"[🧠 DNS] ✅ CDN Fingerprint: {cdn}")
                results["cdn_fingerprint"] = cdn
            else:
                print("[🧠 DNS] ❌ CDN Fingerprint: Aucune signature trouvée")
                results["cdn_fingerprint"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ CDN Fingerprint: {e}")
            results["cdn_fingerprint"] = None

    # Méthode 23 : WebSocket IP Leak
    if should_run("websocket_leak") and websocket:
        try:
            ws_url = f"wss://{domain}"
            ws = websocket.create_connection(ws_url, timeout=5)
            ip = ws.sock.getpeername()[0]
            ws.close()
            if ip:
                print(f"[🧠 DNS] ✅ WebSocket Leak: {ip}")
                results["websocket_leak"] = [ip]
                all_ips.extend([ip])
                if stop_if_found(): return all_ips
            else:
                print("[🧠 DNS] ❌ WebSocket Leak: Pas d'IP récupérée")
                results["websocket_leak"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ WebSocket Leak: {e} - Trying fallback...")
            try:
                ws = websocket.create_connection("wss://echo.websocket.org", timeout=5)
                ip = ws.sock.getpeername()[0]
                ws.close()
                print(f"[🧠 DNS] ✅ WebSocket Leak (fallback): {ip}")
                results["websocket_leak"] = [ip]
                all_ips.extend([ip])
            except Exception as e2:
                print(f"[🧠 DNS] ❌ WebSocket Leak (fallback): {e2}")
                results["websocket_leak"] = None
    elif should_run("websocket_leak"):
        print("[🧠 DNS] ❌ WebSocket Leak: Module 'websocket' non installé")
        results["websocket_leak"] = None

    # Méthode 24 : HTTP/2 Alt-Svc header check
    if should_run("http2_alt_svc"):
        try:
            r = requests.get(f"https://{domain}", timeout=5)
            alt_svc = r.headers.get("Alt-Svc", "")
            if alt_svc:
                print(f"[🧠 DNS] ✅ HTTP2 Alt-Svc: {alt_svc}")
                results["http2_alt_svc"] = [alt_svc]
            else:
                print("[🧠 DNS] ❌ HTTP2 Alt-Svc: Non présent")
                results["http2_alt_svc"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ HTTP2 Alt-Svc: {e}")
            results["http2_alt_svc"] = None

    # Méthode 25 : SafeBrowsing-like Lookup
    if should_run("safebrowsing"):
        try:
            safe = True
            check = f"https://www.google.com/safebrowsing/diagnostic?site={domain}"
            r = requests.get(check, timeout=5)
            if "harmful" in r.text or "malware" in r.text:
                safe = False
            print(f"[🧠 DNS] ✅ SafeBrowsing Check: {'OK' if safe else 'Domaine suspect'}")
            results["safebrowsing"] = ["safe"] if safe else ["suspect"]
        except Exception as e:
            print(f"[🧠 DNS] ❌ SafeBrowsing Check: {e}")
            results["safebrowsing"] = None

    # Méthode 26 : DNS over SSH (optionnel, nécessite config SSH)
    if should_run("dns_over_ssh") and paramiko:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect("your_ssh_server", username="your_user", password="your_pass")  # À configurer
            stdin, stdout, stderr = ssh.exec_command(f"dig +short {domain} A")
            ips = [line.strip() for line in stdout.read().decode().splitlines() if line.strip()]
            ssh.close()
            if ips:
                print(f"[🧠 DNS] ✅ DNS over SSH: {ips}")
                results["dns_over_ssh"] = ips
                all_ips.extend(ips)
                if stop_if_found(): return all_ips
            else:
                print("[🧠 DNS] ❌ DNS over SSH: Réponse vide")
                results["dns_over_ssh"] = None
        except Exception as e:
            print(f"[🧠 DNS] ❌ DNS over SSH: {e}")
            results["dns_over_ssh"] = None
    elif should_run("dns_over_ssh"):
        print("[🧠 DNS] ❌ DNS over SSH: Module 'paramiko' non installé ou non configuré")
        results["dns_over_ssh"] = None

    # Résumé et export
    unique_ips = list(set(all_ips))
    if test_all or quick:
        print("\n[🧠 DNS] Résumé des méthodes :")
        for method, ips in results.items():
            if ips:
                print(f"  ✅ {method}: {ips}")
            else:
                print(f"  ❌ {method}: Échec")

    if json_output:
        with open(f"dns_results_{domain}.json", "w") as f:
            json.dump({"domain": domain, "results": results, "all_ips": unique_ips}, f, indent=4)
        print(f"[🧠 DNS] Résultats exportés vers dns_results_{domain}.json")

    return unique_ips if test_all or quick else all_ips

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Résoudre un domaine DNS avec plusieurs méthodes.")
    parser.add_argument("-domain", type=str, default="openai.com", help="Domaine à résoudre (ex: pypi.org)")
    parser.add_argument("-all", action="store_true", help="Tester toutes les méthodes et afficher les résultats")
    parser.add_argument("--json", action="store_true", help="Exporter les résultats en JSON")
    parser.add_argument("--quick", action="store_true", help="Exécuter uniquement les méthodes critiques et rapides")
    parser.add_argument("--first", action="store_true", help="Retourner dès qu'une IP est trouvée")
    args = parser.parse_args()

    result = resolve_domain(
        args.domain,
        test_all=args.all,
        quick=args.quick,
        json_output=args.json,
        stop_at_first=args.first
    )
    print(result)

