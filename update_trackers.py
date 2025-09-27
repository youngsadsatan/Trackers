#!/usr/bin/env python3
# update_trackers.py
# Baixa várias listas de trackers (raw.githubusercontent.com), concatena,
# filtra comentários/linhas vazias, remove duplicatas (preservando ordem)
# e grava trackers.txt na raiz do repositório.
#
# Requisitos: requests
# (o workflow instalado abaixo instala requests automaticamente)

from datetime import datetime
import requests
from requests.adapters import HTTPAdapter, Retry

# Lista de URLs (na ordem que você forneceu)
URLS = [
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_udp.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_http.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_https.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_ws.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_i2p.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best_ip.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_ip.txt",
]

OUTFILE = "trackers.txt"
TIMEOUT = 15  # segundos por request
RETRIES = 3

def create_session():
    s = requests.Session()
    retries = Retry(
        total=RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

def fetch_url_text(session, url):
    try:
        r = session.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[WARN] Erro ao baixar {url}: {e}")
        return None

def process_text_to_lines(text):
    """
    Recebe todo o texto do arquivo e devolve lista de linhas 'válidas':
    - remove linhas vazias
    - remove linhas que começam com '#'
    - mantém demais linhas (presumidas como trackers)
    """
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        lines.append(line)
    return lines

def main():
    print("Iniciando update_trackers.py")
    session = create_session()

    seen = set()
    ordered = []

    for url in URLS:
        print(f"Baixando: {url}")
        txt = fetch_url_text(session, url)
        if txt is None:
            print(f"  -> falha (pulando).")
            continue
        lines = process_text_to_lines(txt)
        print(f"  -> {len(lines)} linhas não-comment extraídas.")
        for ln in lines:
            if ln not in seen:
                seen.add(ln)
                ordered.append(ln)

    # Se quisermos também adicionar uma nota no topo com timestamp e fontes:
    header_lines = [
        "# trackers.txt gerado automaticamente",
        f"# fonte(s): {', '.join(URLS)}",
        f"# gerado em: {datetime.utcnow().isoformat()}Z",
        "# linhas em ordem de aparição (duplicatas removidas)",
        ""
    ]

    final_content = "\n".join(header_lines + ordered) + "\n"

    # grava o arquivo
    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"Escrito {OUTFILE} com {len(ordered)} entradas únicas.")

if __name__ == "__main__":
    main()
