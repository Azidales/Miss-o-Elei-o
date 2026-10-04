#!/usr/bin/env python3
"""Proxy local do app "Apuração Missão 2026".

Serve o HTML em http://localhost:8765 e repassa ao TSE as requisições /proxy?url=...
Aceita só URLs https de resultados.tse.jus.br e resultados-sim.tse.jus.br e limita o
ritmo (10 req/s, abaixo do limite de 100 req/s por IP informado pelo TSE).
Uso: python3 proxy_tse.py   (Python 3.8+, sem dependências)
"""
import http.server, pathlib, threading, time, urllib.error, urllib.parse, urllib.request, webbrowser

PORTA = 8765
HTML = pathlib.Path(__file__).with_name("apuracao-missao-2026.html")
HOSTS = {"resultados.tse.jus.br", "resultados-sim.tse.jus.br"}
MAX_REQ_POR_SEG = 10
_trava, _ultima = threading.Lock(), [0.0]


class SemRedirecionar(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # não segue redirecionamentos para outros hosts
        return None


abrir = urllib.request.build_opener(SemRedirecionar).open


def aguardar_vez():
    with _trava:  # uma requisição por vez ao TSE, com intervalo mínimo entre elas
        espera = _ultima[0] + 1 / MAX_REQ_POR_SEG - time.monotonic()
        if espera > 0:
            time.sleep(espera)
        _ultima[0] = time.monotonic()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        rota = urllib.parse.urlsplit(self.path)
        if rota.path in ("/", "/index.html"):
            if not HTML.exists():
                return self.responder(404, f"Coloque {HTML.name} na pasta do proxy.".encode(), "text/plain; charset=utf-8")
            return self.responder(200, HTML.read_bytes(), "text/html; charset=utf-8")
        if rota.path != "/proxy":
            return self.responder(404, b"nao encontrado", "text/plain")
        query = urllib.parse.parse_qs(rota.query)
        if "ping" in query:
            return self.responder(200, b"ok", "text/plain")
        alvo = query.get("url", [""])[0]
        u = urllib.parse.urlsplit(alvo)
        if u.scheme != "https" or u.hostname not in HOSTS or u.port or u.username or u.password:
            return self.responder(400, b"URL nao permitida", "text/plain")
        cabecalhos = {"User-Agent": "apuracao-missao-2026-proxy/1.0"}
        for nome in ("If-None-Match", "If-Modified-Since"):  # permite respostas 304 (contam no limite)
            if self.headers.get(nome):
                cabecalhos[nome] = self.headers[nome]
        aguardar_vez()
        try:
            with abrir(urllib.request.Request(alvo, headers=cabecalhos), timeout=30) as r:
                self.responder(r.status, r.read(), r.headers.get("Content-Type", "application/octet-stream"), r.headers)
        except urllib.error.HTTPError as e:  # 304, 404, 429... repassados ao app como vieram
            corpo = b"" if e.code == 304 else e.read()
            self.responder(e.code, corpo, e.headers.get("Content-Type", "text/plain"), e.headers)
        except Exception as e:
            self.responder(502, f"falha ao acessar o TSE: {e}".encode(), "text/plain; charset=utf-8")

    def responder(self, codigo, corpo, tipo, origem=None):
        self.send_response(codigo)
        for nome in ("ETag", "Last-Modified"):
            if origem is not None and origem.get(nome):
                self.send_header(nome, origem[nome])
        self.send_header("Cache-Control", "no-cache")
        if codigo != 304:  # 304 não tem corpo: o navegador reaproveita o que já tem em cache
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        if corpo:
            self.wfile.write(corpo)

    def log_message(self, formato, *args):  # log curto: método, caminho e status
        print(time.strftime("%H:%M:%S"), formato % args)


if __name__ == "__main__":
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    print(f"Abra http://localhost:{PORTA}  (Ctrl+C para encerrar)")
    threading.Timer(1, webbrowser.open, [f"http://localhost:{PORTA}"]).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
