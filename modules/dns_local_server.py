import socketserver
from dnslib import DNSRecord, QTYPE, RR, TXT
import threading

# 🔐 Mémoire DNS simulée (clé = nom, valeur = chunk)
dns_chunks = {
    "echochunk1.echo.": "chunk_1_données_en_base64",
    "echochunk2.echo.": "chunk_2_secret_xyz",
}

class DNSHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, socket = self.request
        request = DNSRecord.parse(data)
        reply = request.reply()

        qname = str(request.q.qname)
        qtype = QTYPE[request.q.qtype]

        print(f"[📡] Requête: {qname} ({qtype})")

        if qtype == "TXT" and qname in dns_chunks:
            txt = dns_chunks[qname]
            reply.add_answer(RR(qname, QTYPE.TXT, rdata=TXT(txt), ttl=60))
            socket.sendto(reply.pack(), self.client_address)
            print(f"[✅] Réponse TXT envoyée pour {qname}")
        else:
            print(f"[❌] Aucun chunk trouvé pour {qname}")

def lancer_dns_serveur():
    server = socketserver.UDPServer(("127.0.0.1", 53530), DNSHandler)
    print("[🚀] DNS serveur local actif sur port 53530...")
    server.serve_forever()

if __name__ == "__main__":
    lancer_dns_serveur()

