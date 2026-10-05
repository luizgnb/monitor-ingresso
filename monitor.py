#!/usr/bin/env python3
"""
Monitor de abertura de venda de ingressos do Flamengo.
Alvo: Flamengo x Estudiantes - semifinal da Libertadores, 22/10/2026, Maracana.

Roda no GitHub Actions a cada 10 minutos e avisa no Telegram assim que
o clube publicar a pagina de venda. Custo zero.
"""

import datetime
import json
import os
import re
import sys
import urllib.parse

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------------
# Configuracao
# ----------------------------------------------------------------------------

PAGINAS = [
    "https://www.flamengo.com.br/ingressos",
    "https://www.flamengo.com.br/noticias/ingressos",
]

# Se o link novo contiver qualquer um destes termos, o alerta vira URGENTE.
TERMOS_URGENTES = [
    "estudiantes",
    "semifinal",
    "libertadores",
]

ARQUIVO_ESTADO = "estado.json"

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}

TIMEOUT = 25
HORA_HEARTBEAT_UTC = 12  # 09h de Brasilia

TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()


# ----------------------------------------------------------------------------
# Estado (persistido no proprio repositorio)
# ----------------------------------------------------------------------------

def carregar_estado():
    try:
        with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
            estado = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        estado = {}

    estado.setdefault("links_vistos", [])
    estado.setdefault("primeira_execucao", True)
    estado.setdefault("erro_avisado_em", None)
    estado.setdefault("heartbeat_em", None)
    return estado


def salvar_estado(estado):
    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2, sort_keys=True)


# ----------------------------------------------------------------------------
# Telegram
# ----------------------------------------------------------------------------

def avisar(texto):
    if not TOKEN or not CHAT_ID:
        print("[ERRO] TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID nao configurados.")
        print(texto)
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": texto,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            print(f"[ERRO] Telegram respondeu {r.status_code}: {r.text[:300]}")
            return False
        print("[OK] Alerta enviado.")
        return True
    except requests.RequestException as e:
        print(f"[ERRO] Falha ao falar com o Telegram: {e}")
        return False


# ----------------------------------------------------------------------------
# Coleta
# ----------------------------------------------------------------------------

def coletar_links(pagina):
    """Devolve {url_absoluta: titulo} dos links de noticia/ingresso da pagina."""
    r = requests.get(pagina, headers=CABECALHOS, timeout=TIMEOUT)
    r.raise_for_status()

    sopa = BeautifulSoup(r.text, "html.parser")
    encontrados = {}

    for a in sopa.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        url = urllib.parse.urljoin(pagina, href)
        if "flamengo.com.br" not in url:
            continue

        caminho = urllib.parse.urlparse(url).path.lower()
        # So interessam paginas de noticia/ingresso, nao menus e rodape.
        if not re.search(r"/(noticias|ingressos)/", caminho):
            continue
        if caminho.rstrip("/") in ("/noticias", "/ingressos", "/noticias/ingressos"):
            continue

        titulo = " ".join(a.get_text(" ", strip=True).split())
        if not titulo:
            titulo = caminho.rstrip("/").rsplit("/", 1)[-1].replace("-", " ")

        url = url.split("#")[0].rstrip("/")
        # Mantem o titulo mais descritivo quando o mesmo link aparece duas vezes.
        if len(titulo) > len(encontrados.get(url, "")):
            encontrados[url] = titulo[:200]

    return encontrados


def eh_urgente(url, titulo):
    alvo = f"{url} {titulo}".lower()
    return any(termo in alvo for termo in TERMOS_URGENTES)


# ----------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------

def main():
    agora = datetime.datetime.now(datetime.timezone.utc)
    hoje = agora.date().isoformat()

    estado = carregar_estado()
    vistos = set(estado["links_vistos"])

    atuais = {}
    falhas = []

    for pagina in PAGINAS:
        try:
            atuais.update(coletar_links(pagina))
            print(f"[OK] {pagina}")
        except Exception as e:
            falhas.append(f"{pagina} -> {type(e).__name__}: {e}")
            print(f"[FALHA] {pagina}: {e}")

    # Todas as paginas falharam: avisa no maximo uma vez por dia e sai.
    if falhas and not atuais:
        if estado["erro_avisado_em"] != hoje:
            avisar(
                "⚠️ <b>Monitor com problema</b>\n\n"
                "Nao consegui ler o site do Flamengo:\n\n"
                + "\n".join(falhas[:3])
                + "\n\nSe isso se repetir, confira o site na mao."
            )
            estado["erro_avisado_em"] = hoje
            salvar_estado(estado)
        sys.exit(0)

    novos = {u: t for u, t in atuais.items() if u not in vistos}

    # Primeira execucao: registra a base sem disparar dezenas de alertas.
    if estado["primeira_execucao"]:
        estado["links_vistos"] = sorted(atuais)
        estado["primeira_execucao"] = False
        estado["heartbeat_em"] = hoje
        salvar_estado(estado)
        avisar(
            "✅ <b>Monitor ligado</b>\n\n"
            f"Acompanhando {len(atuais)} publicacoes do Flamengo.\n"
            "Te aviso assim que sair a venda de <b>Flamengo x Estudiantes</b> "
            "(semifinal, 22/10).\n\n"
            "Checagem a cada 10 minutos."
        )
        print(f"Base inicial: {len(atuais)} links.")
        return

    urgentes = {u: t for u, t in novos.items() if eh_urgente(u, t)}
    comuns = {u: t for u, t in novos.items() if u not in urgentes}

    for url, titulo in urgentes.items():
        avisar(
            "🚨🚨 <b>SAIU A VENDA — E O JOGO QUE VOCE QUER</b> 🚨🚨\n\n"
            f"<b>{titulo}</b>\n{url}\n\n"
            "Abra agora, confirme a onda do seu plano e coloque no calendario.\n"
            "👉 https://ingressos.flamengo.com.br"
        )

    for url, titulo in comuns.items():
        avisar(f"🔔 <b>Nova publicacao de ingressos</b>\n\n{titulo}\n{url}")

    if novos:
        estado["links_vistos"] = sorted(vistos | set(atuais))
        print(f"{len(novos)} link(s) novo(s), {len(urgentes)} urgente(s).")
    else:
        print("Nada novo.")

    # Heartbeat diario: prova de que o robo continua vivo.
    if agora.hour == HORA_HEARTBEAT_UTC and estado["heartbeat_em"] != hoje:
        faltam = (datetime.date(2026, 10, 22) - agora.date()).days
        avisar(
            "🤖 Monitor ativo. Nenhuma venda aberta ate agora.\n"
            f"Faltam {faltam} dias para o jogo."
        )
        estado["heartbeat_em"] = hoje

    if falhas and estado["erro_avisado_em"] != hoje:
        avisar("⚠️ Uma das paginas falhou:\n\n" + falhas[0])
        estado["erro_avisado_em"] = hoje

    salvar_estado(estado)


if __name__ == "__main__":
    main()
