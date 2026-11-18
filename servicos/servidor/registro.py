"""Registro (log) do servidor: uma linha por evento.

Formato: <data/hora UTC> [servidor] <NÍVEL> <evento> chave=valor ...
Exemplo: 2026-11-18T20:15:02.311Z [servidor] INFO  mensagem.difundida sala=geral de=ana destinatarios=2
"""

import json
import sys
from datetime import datetime, timezone


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _formatar_valor(valor) -> str:
    texto = valor if isinstance(valor, str) else json.dumps(valor, ensure_ascii=False)
    if not texto or any(c.isspace() for c in texto):
        return json.dumps(texto, ensure_ascii=False)
    return texto


def _escrever(nivel: str, evento: str, dados: dict) -> None:
    pares = " ".join(f"{chave}={_formatar_valor(valor)}" for chave, valor in dados.items())
    linha = f"{_agora()} [servidor] {nivel:<5} {evento} {pares}".rstrip()
    print(linha, file=sys.stderr if nivel == "ERRO" else sys.stdout, flush=True)


def info(evento: str, **dados) -> None:
    _escrever("INFO", evento, dados)


def aviso(evento: str, **dados) -> None:
    _escrever("AVISO", evento, dados)


def erro(evento: str, **dados) -> None:
    _escrever("ERRO", evento, dados)
