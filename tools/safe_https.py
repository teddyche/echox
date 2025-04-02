i# tools/safe_https.py

import ssl
import http.client
import json
from http.client import HTTPSConnection
from urllib.parse import urlparse


def post_json_via_ip(ip, host_header, path, payload, headers=None, port=443):
    """
    Envoie une requête POST JSON via une IP avec un SSLContext spécifiant le SNI (server_hostname).
    """
    context = ssl.create_default_context()
    conn = http.client.HTTPSConnection(ip, port=port, context=context)
    
    full_headers = {
        "Host": host_header,
        "Content-Type": "application/json",
        "User-Agent": "echo-x/1.0"
    }
    if headers:
        full_headers.update(headers)

    try:
        conn.request("POST", path, body=json.dumps(payload), headers=full_headers)
        response = conn.getresponse()
        data = response.read().decode()
        conn.close()
        return json.loads(data), response.status
    except Exception as e:
        return {"error": str(e)}, 0


def get_json_via_ip(ip, host_header, path, headers=None, port=443):
    """
    Envoie une requête GET via une IP avec un SSLContext spécifiant le SNI (server_hostname).
    """
    context = ssl.create_default_context()
    conn = http.client.HTTPSConnection(ip, port=port, context=context)

    full_headers = {
        "Host": host_header,
        "User-Agent": "echo-x/1.0",
        "Accept": "application/json"
    }
    if headers:
        full_headers.update(headers)

    try:
        conn.request("GET", path, headers=full_headers)
        response = conn.getresponse()
        data = response.read().decode()
        conn.close()
        return json.loads(data), response.status
    except Exception as e:
        return {"error": str(e)}, 0

