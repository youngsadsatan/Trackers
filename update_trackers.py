#!/usr/bin/env python3
"""
update_trackers.py - Baixa, combina e deduplica listas públicas de trackers BitTorrent.

Funcionalidades:
- Download de múltiplas listas de trackers a partir de URLs brutas do GitHub.
- Filtragem de linhas vazias e comentários (linhas iniciadas com '#').
- Remoção de duplicatas, preservando a ordem de primeira aparição.
- Geração de um arquivo final limpo (trackers.txt) sem cabeçalhos ou metadados.
- Tratamento robusto de erros com retries e timeouts.
- Logs detalhados para fácil depuração.
"""

import logging
from datetime import datetime
from typing import List, Set
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# ------------------------------------------------------------------------------
# CONSTANTES E CONFIGURAÇÕES
# ------------------------------------------------------------------------------

# Lista de URLs (ATUALIZADA com as listas mais recentes do ngosang)
URLS: List[str] = [
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_udp.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_http.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_https.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_ws.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_i2p.txt",
    # NOVAS LISTAS (yggdrasil)
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_yggdrasil.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best_ip.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_ip.txt",
    # NOVA LISTA (yggdrasil IP)
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_yggdrasil_ip.txt",
]

OUTFILE: str = "trackers.txt"
TIMEOUT: int = 15  # segundos
RETRIES: int = 3
BACKOFF_FACTOR: float = 1.0  # para backoff exponencial entre retries

# Configuração do logging (saída clara e timestamp)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------------------------------------------------------

def create_robust_session() -> requests.Session:
    """
    Cria uma sessão HTTP com retry automático e backoff exponencial.

    Returns:
        requests.Session: Sessão configurada para ser resiliente.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_url_content(session: requests.Session, url: str) -> str | None:
    """
    Baixa o conteúdo de uma URL de forma segura.

    Args:
        session (requests.Session): Sessão HTTP a ser usada.
        url (str): URL do arquivo de trackers.

    Returns:
        str | None: Conteúdo do arquivo como string, ou None em caso de falha.
    """
    try:
        logger.info(f"Baixando: {url}")
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        logger.debug(f"Download concluído: {len(response.text)} bytes")
        return response.text
    except requests.exceptions.Timeout:
        logger.error(f"Timeout ao acessar {url}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP {e.response.status_code} ao acessar {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão ao acessar {url}: {e}")
    return None


def extract_valid_lines(content: str) -> List[str]:
    """
    Extrai linhas válidas de um conteúdo bruto.
    Critérios de validade: não vazia e não iniciada com '#'.

    Args:
        content (str): Conteúdo bruto do arquivo.

    Returns:
        List[str]: Lista de linhas consideradas trackers.
    """
    lines = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line and not line.startswith('#'):
            lines.append(line)
    return lines


def merge_unique_preserve_order(new_lines: List[str], seen: Set[str], ordered: List[str]) -> None:
    """
    Adiciona linhas novas à lista ordenada, evitando duplicatas.

    Args:
        new_lines (List[str]): Lista de linhas recém-processadas.
        seen (Set[str]): Conjunto de trackers já vistos (para checagem O(1)).
        ordered (List[str]): Lista que mantém a ordem de inserção.
    """
    for line in new_lines:
        if line not in seen:
            seen.add(line)
            ordered.append(line)


# ------------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ------------------------------------------------------------------------------

def main() -> None:
    """
    Fluxo principal do script:
    1. Cria sessão HTTP.
    2. Itera sobre as URLs, baixa e processa cada uma.
    3. Remove duplicatas e mantém ordem.
    4. Escreve o resultado final no arquivo.
    5. Exibe estatísticas.
    """
    logger.info("=" * 50)
    logger.info("Iniciando atualização da lista de trackers...")
    logger.info("=" * 50)

    session = create_robust_session()
    seen_trackers: Set[str] = set()
    ordered_trackers: List[str] = []

    for url in URLS:
        content = fetch_url_content(session, url)
        if content is None:
            logger.warning(f"  -> Pulando URL devido a erro: {url}")
            continue

        valid_lines = extract_valid_lines(content)
        logger.info(f"  -> {len(valid_lines)} trackers encontrados em {url}")

        merge_unique_preserve_order(valid_lines, seen_trackers, ordered_trackers)

    # Prepara o conteúdo final
    final_content = "\n".join(ordered_trackers)
    if ordered_trackers:
        final_content += "\n"  # Garante uma nova linha ao final do arquivo

    # Escreve o arquivo
    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info("=" * 50)
    logger.info(f"Arquivo '{OUTFILE}' gerado com sucesso!")
    logger.info(f"Total de trackers únicos: {len(ordered_trackers)}")
    logger.info(f"Total de URLs processadas: {len(URLS)}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
