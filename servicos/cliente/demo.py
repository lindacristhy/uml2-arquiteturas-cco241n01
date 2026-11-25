"""Roteiro automático do FLUXO PRINCIPAL do chat.

Três clientes (ana, bruno e carla) conversam na sala "geral" e cada passo é
conferido. Todo o tráfego cliente <-> servidor é impresso no terminal, e são
essas linhas que vão para o LOGS.md.

    1. ana e bruno entram na sala "geral"           (RF01, RF05)
    2. ana digita e envia uma mensagem              (RF02)
    3. bruno recebe a mensagem em tempo real         (RF03, RNF01)
    4. bruno responde e ana recebe
    5. carla entra depois e recebe o histórico       (RF04)
    6. o servidor recusa nome repetido e msg vazia   (RNF02)
    7. bruno sai e os outros são avisados            (RF05)

Uso: python demo.py [--host 127.0.0.1] [--porta 5000]
Sai com código 0 se tudo deu certo e 1 se alguma verificação falhou.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

from conexao import ConexaoChat

SALA = "geral"
TEMPO_LIMITE = 3.0  # segundos esperando cada resposta
LATENCIA_MAXIMA_MS = 1000  # RNF01

verificacoes = []


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def log(texto: str) -> None:
    print(f"{agora()} [demo] {texto}", flush=True)


def passo(numero: int, descricao: str) -> None:
    log("")
    log(f"===== Passo {numero}: {descricao} =====")


def verificar(condicao: bool, descricao: str) -> None:
    verificacoes.append((condicao, descricao))
    log(f"{'OK   ' if condicao else 'FALHA'} {descricao}")


def rastreador(usuario: str):
    def ao_trafegar(direcao: str, mensagem: dict) -> None:
        seta = "-> servidor" if direcao == "->" else "<- servidor"
        log(f"{usuario:<6} {seta}  {json.dumps(mensagem, ensure_ascii=False)}")

    return ao_trafegar


async def esperar(conexao: ConexaoChat, tipo: str, **filtros) -> dict:
    """Lê mensagens até chegar uma do tipo (e campos) esperado."""

    async def procurar():
        while True:
            mensagem = await conexao.receber()
            if mensagem.get("tipo") == tipo and all(mensagem.get(k) == v for k, v in filtros.items()):
                return mensagem

    return await asyncio.wait_for(procurar(), TEMPO_LIMITE)


async def conectar(host: str, porta: int, usuario: str) -> ConexaoChat:
    conexao = await ConexaoChat.abrir(host, porta, ao_trafegar=rastreador(usuario))
    log(f"{usuario:<6} conectou em {host}:{porta}")
    return conexao


async def roteiro(host: str, porta: int) -> None:
    passo(1, "ana e bruno entram na sala 'geral'")
    ana = await conectar(host, porta, "ana")
    await ana.entrar("ana", SALA)
    entrou = await esperar(ana, "entrou")
    verificar(entrou["usuarios"] == ["ana"], "ana entrou e é a única online")

    bruno = await conectar(host, porta, "bruno")
    await bruno.entrar("bruno", SALA)
    entrou = await esperar(bruno, "entrou")
    verificar(entrou["usuarios"] == ["ana", "bruno"], "bruno entrou e vê ana online")
    aviso = await esperar(ana, "presenca", evento="entrou", usuario="bruno")
    verificar(aviso["usuarios"] == ["ana", "bruno"], "ana foi avisada da entrada de bruno")

    passo(2, "ana digita e envia uma mensagem")
    await ana.enviar({"tipo": "digitando"})
    await esperar(bruno, "digitando", usuario="ana")
    verificar(True, "bruno viu o aviso 'ana está digitando'")

    texto_ana = "Oi, Bruno! O servidor de chat está no ar?"
    inicio = time.perf_counter()
    await ana.enviar({"tipo": "mensagem", "texto": texto_ana, "id_local": "ana-1"})

    passo(3, "bruno recebe a mensagem em tempo real")
    recebida = await esperar(bruno, "mensagem", usuario="ana")
    latencia_ms = (time.perf_counter() - inicio) * 1000
    verificar(recebida["texto"] == texto_ana, "bruno recebeu exatamente o texto enviado por ana")
    verificar(
        latencia_ms < LATENCIA_MAXIMA_MS,
        f"mensagem entregue em {latencia_ms:.1f} ms (limite do RNF01: {LATENCIA_MAXIMA_MS} ms)",
    )
    eco = await esperar(ana, "mensagem", id_local="ana-1")
    verificar(eco["id"] == recebida["id"], f"ana recebeu a confirmação de entrega (id={eco['id']})")

    passo(4, "bruno responde e ana recebe")
    texto_bruno = "Está sim, Ana! Mensagem recebida na hora."
    await bruno.enviar({"tipo": "mensagem", "texto": texto_bruno, "id_local": "bruno-1"})
    resposta = await esperar(ana, "mensagem", usuario="bruno")
    verificar(resposta["texto"] == texto_bruno, "ana recebeu a resposta de bruno")
    await esperar(bruno, "mensagem", id_local="bruno-1")

    passo(5, "carla entra depois e recebe o histórico da sala")
    carla = await conectar(host, porta, "carla")
    await carla.entrar("carla", SALA)
    entrou = await esperar(carla, "entrou")
    textos = [m["texto"] for m in entrou["historico"]]
    verificar(textos[-2:] == [texto_ana, texto_bruno], f"carla recebeu o histórico ({len(textos)} mensagens)")
    verificar(entrou["usuarios"] == ["ana", "bruno", "carla"], "carla vê ana e bruno online")
    await esperar(ana, "presenca", evento="entrou", usuario="carla")
    await esperar(bruno, "presenca", evento="entrou", usuario="carla")

    passo(6, "o servidor recusa entradas inválidas")
    impostor = await conectar(host, porta, "outro")
    await impostor.entrar("Ana", SALA)
    recusa = await esperar(impostor, "erro")
    verificar(recusa["codigo"] == "NOME_EM_USO", "nome repetido na sala foi recusado (NOME_EM_USO)")
    await impostor.fechar()
    await carla.enviar({"tipo": "mensagem", "texto": "   "})
    recusa = await esperar(carla, "erro")
    verificar(recusa["codigo"] == "MENSAGEM_VAZIA", "mensagem vazia foi recusada (MENSAGEM_VAZIA)")

    passo(7, "bruno sai e os outros são avisados")
    await bruno.fechar()
    log("bruno  desconectou")
    aviso = await esperar(ana, "presenca", evento="saiu", usuario="bruno")
    verificar(aviso["usuarios"] == ["ana", "carla"], "ana foi avisada da saída de bruno")
    await esperar(carla, "presenca", evento="saiu", usuario="bruno")
    verificar(True, "carla foi avisada da saída de bruno")

    await carla.fechar()
    await ana.fechar()
    log("ana e carla desconectaram")


async def principal(host: str, porta: int) -> int:
    log(f"Iniciando o fluxo principal contra o servidor {host}:{porta}")
    try:
        await roteiro(host, porta)
    except (OSError, asyncio.TimeoutError) as e:
        verificar(False, f"o roteiro foi interrompido: {e.__class__.__name__} {e}")

    falhas = [d for ok, d in verificacoes if not ok]
    log("")
    if falhas:
        log(f"RESULTADO: {len(falhas)} de {len(verificacoes)} verificações falharam.")
        return 1
    log(f"RESULTADO: fluxo principal concluído com sucesso ({len(verificacoes)} verificações OK).")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa o fluxo principal do chat")
    parser.add_argument("--host", default=os.environ.get("CHAT_HOST", "127.0.0.1"))
    parser.add_argument("--porta", type=int, default=int(os.environ.get("CHAT_PORTA", "5000")))
    args = parser.parse_args()
    sys.exit(asyncio.run(principal(args.host, args.porta)))
