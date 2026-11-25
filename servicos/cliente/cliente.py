"""Cliente de chat para o terminal.

Uso:
    python cliente.py --usuario ana --sala geral
    python cliente.py --host 192.168.0.10 --porta 5000 --usuario bruno

Comandos dentro do chat:
    /usuarios      mostra quem está online na sala
    /sala <nome>   troca de sala
    /ajuda         mostra os comandos
    /sair          sai do chat

Se a conexão cair, o cliente tenta reconectar sozinho (até 5 tentativas).
"""

import argparse
import asyncio
import os
import sys
import threading
import uuid
from datetime import datetime

from conexao import ConexaoChat, ConexaoEncerrada

TENTATIVAS_DE_RECONEXAO = 5


def hora_local(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S")
    except (ValueError, AttributeError):
        return datetime.now().strftime("%H:%M:%S")


def escrever(texto: str) -> None:
    print(texto, flush=True)


def mostrar(mensagem: dict, estado: dict) -> None:
    tipo = mensagem.get("tipo")
    if tipo == "mensagem":
        escrever(f"[{hora_local(mensagem['enviada_em'])}] {mensagem['usuario']}: {mensagem['texto']}")
    elif tipo == "entrou":
        estado["sala"] = mensagem["sala"]
        estado["usuarios"] = mensagem["usuarios"]
        escrever(f"*** Você entrou na sala '{mensagem['sala']}' como {mensagem['usuario']}.")
        if mensagem["historico"]:
            escrever(f"*** Últimas {len(mensagem['historico'])} mensagens:")
            for antiga in mensagem["historico"]:
                mostrar(antiga, estado)
        escrever(f"*** Online: {', '.join(mensagem['usuarios'])}")
    elif tipo == "presenca":
        estado["usuarios"] = mensagem["usuarios"]
        verbo = "entrou na" if mensagem["evento"] == "entrou" else "saiu da"
        escrever(f"*** {mensagem['usuario']} {verbo} sala. Online: {', '.join(mensagem['usuarios']) or '(ninguém)'}")
    elif tipo == "digitando":
        escrever(f"    ({mensagem['usuario']} está digitando...)")
    elif tipo == "sistema":
        escrever(f"*** {mensagem['texto']}")
    elif tipo == "erro":
        escrever(f"!!! Erro ({mensagem['codigo']}): {mensagem['motivo']}")


def iniciar_leitura_do_teclado(loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
    """Lê o teclado numa thread separada para não travar o recebimento de mensagens."""
    fila = asyncio.Queue()

    def ler():
        for linha in sys.stdin:
            loop.call_soon_threadsafe(fila.put_nowait, linha.rstrip("\r\n"))
        loop.call_soon_threadsafe(fila.put_nowait, None)  # fim da entrada (Ctrl+D / Ctrl+Z)

    threading.Thread(target=ler, daemon=True).start()
    return fila


async def conversar(conexao: ConexaoChat, teclado: asyncio.Queue, estado: dict) -> str:
    """Mantém a conversa até o usuário sair ("sair") ou a conexão cair ("caiu")."""
    recebimento = asyncio.create_task(conexao.receber())
    digitacao = asyncio.create_task(teclado.get())
    try:
        while True:
            prontas, _ = await asyncio.wait({recebimento, digitacao}, return_when=asyncio.FIRST_COMPLETED)

            if recebimento in prontas:
                try:
                    mensagem = recebimento.result()
                except (ConexaoEncerrada, ConnectionError, OSError):
                    return "caiu"
                mostrar(mensagem, estado)
                if mensagem.get("tipo") == "erro" and mensagem.get("codigo") == "NOME_EM_USO":
                    return "sair"
                recebimento = asyncio.create_task(conexao.receber())

            if digitacao in prontas:
                linha = digitacao.result()
                if linha is None or linha.strip() == "/sair":
                    return "sair"
                await tratar_comando(linha.strip(), conexao, estado)
                digitacao = asyncio.create_task(teclado.get())
    finally:
        recebimento.cancel()
        digitacao.cancel()


async def tratar_comando(linha: str, conexao: ConexaoChat, estado: dict) -> None:
    if not linha:
        return
    if linha == "/ajuda":
        escrever("Comandos: /usuarios, /sala <nome>, /ajuda, /sair")
    elif linha == "/usuarios":
        escrever(f"*** Online em '{estado['sala']}': {', '.join(estado['usuarios']) or '(ainda entrando na sala...)'}")
    elif linha.startswith("/sala "):
        await conexao.entrar(estado["usuario"], linha[6:].strip(), estado["sessao"])
    elif linha.startswith("/"):
        escrever("!!! Comando desconhecido. Digite /ajuda.")
    else:
        await conexao.enviar({"tipo": "mensagem", "texto": linha, "id_local": uuid.uuid4().hex[:8]})


async def executar(args) -> None:
    estado = {"usuario": args.usuario, "sala": args.sala, "sessao": uuid.uuid4().hex, "usuarios": []}
    teclado = iniciar_leitura_do_teclado(asyncio.get_running_loop())
    tentativa = 0

    while True:
        try:
            conexao = await ConexaoChat.abrir(args.host, args.porta)
        except (OSError, asyncio.TimeoutError):
            tentativa += 1
            if tentativa > TENTATIVAS_DE_RECONEXAO:
                escrever(f"!!! Não foi possível conectar em {args.host}:{args.porta}. Desisti.")
                return
            espera = min(2 * tentativa, 10)
            escrever(f"*** Servidor indisponível. Nova tentativa em {espera}s ({tentativa}/{TENTATIVAS_DE_RECONEXAO})...")
            await asyncio.sleep(espera)
            continue

        tentativa = 0
        escrever(f"*** Conectado a {args.host}:{args.porta}. Digite /ajuda para ver os comandos.")
        await conexao.entrar(estado["usuario"], estado["sala"], estado["sessao"])
        resultado = await conversar(conexao, teclado, estado)
        await conexao.fechar(avisar_saida=(resultado == "sair"))
        if resultado == "sair":
            escrever("*** Até mais!")
            return
        escrever("*** Conexão perdida. Tentando reconectar...")


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Cliente de terminal do chat em tempo real")
    parser.add_argument("--host", default=os.environ.get("CHAT_HOST", "127.0.0.1"))
    parser.add_argument("--porta", type=int, default=int(os.environ.get("CHAT_PORTA", "5000")))
    parser.add_argument("--usuario", help="seu nome no chat")
    parser.add_argument("--sala", default="geral")
    args = parser.parse_args()
    if not args.usuario:
        args.usuario = input("Seu nome: ").strip()
    return args


if __name__ == "__main__":
    try:
        asyncio.run(executar(ler_argumentos()))
    except KeyboardInterrupt:
        pass
