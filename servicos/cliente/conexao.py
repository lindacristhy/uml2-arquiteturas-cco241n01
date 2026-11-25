"""Conexão do cliente com o servidor de chat (TCP + JSON, uma mensagem por linha).

Usada tanto pelo cliente interativo (cliente.py) quanto pelo roteiro do
fluxo principal (demo.py). Responde sozinha aos "ping" do servidor.
"""

import asyncio
import json


class ConexaoEncerrada(Exception):
    """O servidor fechou a conexão."""


class ConexaoChat:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, ao_trafegar=None):
        self._reader = reader
        self._writer = writer
        # ao_trafegar(direcao, mensagem): chamado a cada mensagem enviada ("->") ou recebida ("<-").
        self._ao_trafegar = ao_trafegar

    @classmethod
    async def abrir(cls, host: str, porta: int, ao_trafegar=None, tempo_limite: float = 5.0) -> "ConexaoChat":
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, porta), tempo_limite)
        return cls(reader, writer, ao_trafegar)

    async def enviar(self, mensagem: dict) -> None:
        if self._ao_trafegar and mensagem.get("tipo") != "pong":
            self._ao_trafegar("->", mensagem)
        self._writer.write((json.dumps(mensagem, ensure_ascii=False) + "\n").encode("utf-8"))
        await self._writer.drain()

    async def receber(self) -> dict:
        """Espera a próxima mensagem do servidor (os pings são respondidos aqui mesmo)."""
        while True:
            linha = await self._reader.readline()
            if not linha:
                raise ConexaoEncerrada("o servidor encerrou a conexão")
            mensagem = json.loads(linha.decode("utf-8"))
            if mensagem.get("tipo") == "ping":
                await self.enviar({"tipo": "pong"})
                continue
            if self._ao_trafegar:
                self._ao_trafegar("<-", mensagem)
            return mensagem

    async def entrar(self, usuario: str, sala: str, sessao: str = None) -> None:
        mensagem = {"tipo": "entrar", "usuario": usuario, "sala": sala}
        if sessao:
            mensagem["sessao"] = sessao
        await self.enviar(mensagem)

    async def fechar(self, avisar_saida: bool = True) -> None:
        if avisar_saida and not self._writer.is_closing():
            try:
                await self.enviar({"tipo": "sair"})
            except (ConnectionError, OSError):
                pass
        self._writer.close()
        try:
            await self._writer.wait_closed()
        except (ConnectionError, OSError):
            pass
