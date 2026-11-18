"""Servidor do chat em tempo real (arquitetura cliente-servidor).

Usa apenas a biblioteca padrão do Python (asyncio + sockets TCP).
Cada cliente abre uma conexão TCP e troca mensagens JSON, uma por linha
(veja protocolo.py). O servidor é o ponto central: valida tudo o que chega,
guarda o histórico de cada sala e repassa (difunde) as mensagens para os
outros clientes conectados.

Variáveis de ambiente:
    CHAT_HOST   endereço de escuta (padrão 0.0.0.0)
    CHAT_PORTA  porta TCP (padrão 5000)
"""

import asyncio
import contextlib
import itertools
import os
import signal
import time

import registro as log
from protocolo import TAMANHO_MAXIMO_LINHA, ErroDeProtocolo, codificar, interpretar
from salas import GerenciadorDeSalas

INTERVALO_PING = 15  # segundos entre verificações de conexões
TEMPO_LIMITE_INATIVO = 45  # segundos sem resposta até derrubar a conexão
LIMITE_BUFFER_SAIDA = 1024 * 1024  # 1 MB pendente = cliente lento demais, desconecta


class Conexao:
    """Um cliente conectado ao servidor."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.id = "-"  # recebe um número (c1, c2, ...) quando envia o primeiro dado
        self.reader = reader
        self.writer = writer
        endereco = writer.get_extra_info("peername") or ("?", 0)
        self.endereco = f"{endereco[0]}:{endereco[1]}"
        self.usuario = None
        self.sala = None
        self.sessao = None
        self.anunciada = False  # já apareceu no log?
        self.ultimo_contato = time.monotonic()

    def enviar(self, mensagem: dict) -> bool:
        """Envia sem bloquear. Devolve False se a conexão já estiver fechada."""
        if self.writer.is_closing():
            return False
        if self.writer.transport.get_write_buffer_size() > LIMITE_BUFFER_SAIDA:
            log.aviso("conexao.lenta", cliente=self.id, usuario=self.usuario)
            self.fechar()
            return False
        self.writer.write(codificar(mensagem))
        return True

    def fechar(self) -> None:
        if not self.writer.is_closing():
            self.writer.close()


class ServidorDeChat:
    def __init__(self, host: str, porta: int):
        self.host = host
        self.porta = porta
        self.salas = GerenciadorDeSalas()
        self.conexoes = set()
        self._ids = itertools.count(1)
        self._servidor = None
        self._tarefa_ping = None

    async def iniciar(self) -> None:
        self._servidor = await asyncio.start_server(
            self._atender, self.host, self.porta, limit=TAMANHO_MAXIMO_LINHA
        )
        self._tarefa_ping = asyncio.create_task(self._verificar_conexoes())
        log.info("servidor.iniciado", host=self.host, porta=self.porta)

    async def encerrar(self) -> None:
        log.info("servidor.encerrando", conexoes=len(self.conexoes))
        if self._tarefa_ping:
            self._tarefa_ping.cancel()
        if self._servidor:
            self._servidor.close()
        for conexao in list(self.conexoes):
            conexao.enviar({"tipo": "sistema", "texto": "O servidor está sendo desligado."})
            conexao.fechar()
        await asyncio.sleep(0.1)  # dá tempo de os clientes receberem o aviso
        log.info("servidor.encerrado")

    # ------------------------------------------------------------------ conexões

    async def _atender(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        conexao = Conexao(reader, writer)
        self.conexoes.add(conexao)
        motivo = "cliente desconectou"
        try:
            while True:
                try:
                    linha = await reader.readline()
                except ValueError:  # linha maior que TAMANHO_MAXIMO_LINHA (o asyncio descarta o excesso)
                    self._anunciar(conexao)
                    log.aviso("comando.recusado", cliente=conexao.id, codigo="MENSAGEM_LONGA")
                    conexao.enviar(ErroDeProtocolo("MENSAGEM_LONGA", "Mensagem grande demais.").como_mensagem())
                    continue
                if not linha:
                    break
                self._anunciar(conexao)
                conexao.ultimo_contato = time.monotonic()
                if not linha.strip():
                    continue
                try:
                    comando = interpretar(linha)
                    if comando["tipo"] == "sair":
                        motivo = "cliente saiu"
                        break
                    self._tratar(conexao, comando)
                except ErroDeProtocolo as e:
                    log.aviso("comando.recusado", cliente=conexao.id, codigo=e.codigo)
                    conexao.enviar(e.como_mensagem())
        except (ConnectionError, OSError) as e:
            motivo = f"erro de rede: {e.__class__.__name__}"
        finally:
            self._remover(conexao, motivo)
            conexao.fechar()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    def _anunciar(self, conexao: Conexao) -> None:
        # Só registra a conexão quando chega o primeiro dado. Assim as sondagens de porta
        # (como o healthcheck do Docker, que conecta e desconecta) não poluem o log.
        if not conexao.anunciada:
            conexao.anunciada = True
            conexao.id = f"c{next(self._ids)}"
            log.info("conexao.aberta", cliente=conexao.id, endereco=conexao.endereco)

    def _remover(self, conexao: Conexao, motivo: str) -> None:
        self._sair_da_sala(conexao)
        self.conexoes.discard(conexao)
        if conexao.anunciada:
            log.info("conexao.fechada", cliente=conexao.id, motivo=motivo, online=len(self.conexoes))

    def _sair_da_sala(self, conexao: Conexao) -> None:
        if conexao.sala and self.salas.sair(conexao.sala, conexao):
            usuarios = self.salas.usuarios(conexao.sala)
            self.salas.difundir(
                conexao.sala,
                {"tipo": "presenca", "evento": "saiu", "usuario": conexao.usuario, "usuarios": usuarios},
            )
            log.info("usuario.saiu", sala=conexao.sala, usuario=conexao.usuario, online_na_sala=len(usuarios))
        conexao.sala = None

    # ------------------------------------------------------------------ comandos

    def _tratar(self, conexao: Conexao, comando: dict) -> None:
        tipo = comando["tipo"]
        if tipo == "entrar":
            self._entrar(conexao, comando)
        elif tipo == "pong":
            pass  # o horário do último contato já foi atualizado
        elif conexao.sala is None:
            raise ErroDeProtocolo("NAO_ENTROU", "Entre em uma sala antes de enviar mensagens.")
        elif tipo == "mensagem":
            self._mensagem(conexao, comando)
        elif tipo == "digitando":
            self.salas.difundir(conexao.sala, {"tipo": "digitando", "usuario": conexao.usuario}, exceto=conexao)

    def _entrar(self, conexao: Conexao, comando: dict) -> None:
        if conexao.sala:  # trocou de sala
            self._sair_da_sala(conexao)

        conexao.usuario = comando["usuario"]
        conexao.sessao = comando["sessao"]
        sala = comando["sala"]
        try:
            antiga = self.salas.entrar(sala, conexao)
        except ErroDeProtocolo:
            conexao.usuario = None
            raise
        conexao.sala = sala

        usuarios = self.salas.usuarios(sala)
        historico = self.salas.historico(sala)
        conexao.enviar(
            {"tipo": "entrou", "sala": sala, "usuario": conexao.usuario, "historico": historico, "usuarios": usuarios}
        )

        if antiga is not None:  # reconexão: fecha a conexão antiga sem anunciar "saiu"
            antiga.sala = None
            antiga.enviar({"tipo": "sistema", "texto": "Sua sessão foi aberta em outra conexão."})
            antiga.fechar()
            log.info("usuario.reconectou", sala=sala, usuario=conexao.usuario, cliente=conexao.id)
            return

        self.salas.difundir(
            sala, {"tipo": "presenca", "evento": "entrou", "usuario": conexao.usuario, "usuarios": usuarios}, exceto=conexao
        )
        log.info(
            "usuario.entrou",
            sala=sala,
            usuario=conexao.usuario,
            cliente=conexao.id,
            online_na_sala=len(usuarios),
            historico_enviado=len(historico),
        )

    def _mensagem(self, conexao: Conexao, comando: dict) -> None:
        inicio = time.perf_counter()
        mensagem = self.salas.registrar_mensagem(conexao.sala, conexao.usuario, comando["texto"], comando["id_local"])
        entregues = self.salas.difundir(conexao.sala, mensagem)
        duracao_ms = (time.perf_counter() - inicio) * 1000
        log.info(
            "mensagem.difundida",
            sala=conexao.sala,
            de=conexao.usuario,
            id=mensagem["id"],
            destinatarios=entregues,
            tempo_ms=f"{duracao_ms:.2f}",
        )

    # ------------------------------------------------------------------ heartbeat

    async def _verificar_conexoes(self) -> None:
        """Envia ping periódico e derruba conexões que pararam de responder."""
        while True:
            await asyncio.sleep(INTERVALO_PING)
            agora = time.monotonic()
            for conexao in list(self.conexoes):
                if agora - conexao.ultimo_contato > TEMPO_LIMITE_INATIVO:
                    log.aviso("conexao.inativa", cliente=conexao.id, usuario=conexao.usuario)
                    conexao.fechar()
                else:
                    conexao.enviar({"tipo": "ping"})


async def principal() -> None:
    host = os.environ.get("CHAT_HOST", "0.0.0.0")
    porta = int(os.environ.get("CHAT_PORTA", "5000"))

    servidor = ServidorDeChat(host, porta)
    await servidor.iniciar()

    parar = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sinal in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):  # no Windows, o Ctrl+C chega como KeyboardInterrupt
            loop.add_signal_handler(sinal, parar.set)
    try:
        await parar.wait()
    finally:
        await servidor.encerrar()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(principal())
