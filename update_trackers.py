#!/usr/bin/env python3

import logging
from typing import List, Set
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

URLS: List[str] = [
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_udp.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_http.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_https.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_ws.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_i2p.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_yggdrasil.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best_ip.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_ip.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all_yggdrasil_ip.txt",
]

OUTFILE_LINES: str = "trackers.txt"
OUTFILE_COMMA: str = "trackers_comma.txt"
TIMEOUT: int = 15
RETRIES: int = 3
BACKOFF_FACTOR: float = 1.0

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_robust_session() -> requests.Session:
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
    lines = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line and not line.startswith('#'):
            lines.append(line)
    return lines


def merge_unique_preserve_order(
    new_lines: List[str],
    seen: Set[str],
    ordered: List[str]
) -> None:
    for line in new_lines:
        if line not in seen:
            seen.add(line)
            ordered.append(line)


def write_lines_output(trackers: List[str]) -> None:
    content = "\n".join(trackers)
    if trackers:
        content += "\n"
    with open(OUTFILE_LINES, "w", encoding="utf-8") as f:
        f.write(content)


def write_comma_output(trackers: List[str]) -> None:
    content = ", ".join(trackers)
    if trackers:
        content += "\n"
    with open(OUTFILE_COMMA, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
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

    write_lines_output(ordered_trackers)
    write_comma_output(ordered_trackers)

    logger.info("=" * 50)
    logger.info(f"Arquivos gerados com sucesso:")
    logger.info(f"  - {OUTFILE_LINES} : {len(ordered_trackers)} trackers (um por linha)")
    logger.info(f"  - {OUTFILE_COMMA} : {len(ordered_trackers)} trackers (formato vírgula)")
    logger.info(f"Total de URLs processadas: {len(URLS)}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
