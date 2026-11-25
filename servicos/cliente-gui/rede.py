"""Comunicação do cliente gráfico com o servidor.

A conexão roda numa thread separada para a janela não travar. Tudo o que chega
do servidor é colocado na fila `eventos`; a janela lê essa fila de tempos em
tempos (o Tkinter só pode ser alterado pela thread principal).

Além das mensagens do servidor, a fila recebe eventos de estado:
    {"tipo": "_estado", "estado": "conectado" | "reconectando" | "desconectado", "texto": "..."}
"""

import json
import queue
import socket
import threading
import time
import uuid

TENTATIVAS_DE_RECONEXAO = 5
ERROS_QUE_IMPEDEM_ENTRAR = {"NOME_EM_USO", "USUARIO_INVALIDO", "SALA_INVALIDA"}


class ClienteRede:
    def __init__(self, host: str, porta: int, usuario: str, sala: str):
        self.host = host
        self.porta = porta
        self.usuario = usuario
        self.sala = sala
        self.sessao = uuid.uuid4().hex  # permite ao servidor reconhecer uma reconexão
        self.eventos = queue.Queue()
        self._sock = None
        self._trava = threading.Lock()
        self._encerrando = False

    # ----------------------------------------------------------- usado pela janela

    def iniciar(self) -> None:
        threading.Thread(target=self._executar, name="rede-chat", daemon=True).start()

    def enviar(self, mensagem: dict) -> bool:
        dados = (json.dumps(mensagem, ensure_ascii=False) + "\n").encode("utf-8")
        with self._trava:
            if self._sock is None:
                return False
            try:
                self._sock.sendall(dados)
                return True
            except OSError:
                return False

    def enviar_texto(self, texto: str) -> bool:
        return self.enviar({"tipo": "mensagem", "texto": texto, "id_local": uuid.uuid4().hex[:8]})

    def avisar_digitando(self) -> None:
        self.enviar({"tipo": "digitando"})

    def encerrar(self) -> None:
        self._encerrando = True
        self.enviar({"tipo": "sair"})
        with self._trava:
            if self._sock is not None:
                try:
                    self._sock.shutdown(socket.SHUT_RDWR)  # acorda a thread que está lendo
                except OSError:
                    pass
                self._sock.close()
                self._sock = None

    # ----------------------------------------------------------- thread de rede

    def _estado(self, estado: str, texto: str) -> None:
        self.eventos.put({"tipo": "_estado", "estado": estado, "texto": texto})

    def _executar(self) -> None:
        tentativa = 0
        while not self._encerrando:
            try:
                sock = socket.create_connection((self.host, self.porta), timeout=5)
                sock.settimeout(None)
            except OSError:
                tentativa += 1
                if tentativa > TENTATIVAS_DE_RECONEXAO:
                    self._estado("desconectado", f"Não foi possível conectar em {self.host}:{self.porta}.")
                    return
                espera = min(2 * tentativa, 10)
                self._estado("reconectando", f"servidor indisponível, nova tentativa em {espera}s")
                time.sleep(espera)
                continue

            tentativa = 0
            with self._trava:
                self._sock = sock
            self._estado("conectado", "conectado")
            self.enviar({"tipo": "entrar", "usuario": self.usuario, "sala": self.sala, "sessao": self.sessao})
            self._ler(sock)

            with self._trava:
                if self._sock is sock:
                    self._sock = None
            sock.close()
            if not self._encerrando:
                self._estado("reconectando", "conexão perdida, reconectando...")
                time.sleep(1)

    def _ler(self, sock: socket.socket) -> None:
        try:
            with sock.makefile("r", encoding="utf-8", newline="\n") as arquivo:
                for linha in arquivo:
                    mensagem = json.loads(linha)
                    if mensagem.get("tipo") == "ping":
                        self.enviar({"tipo": "pong"})
                        continue
                    self.eventos.put(mensagem)
                    if mensagem.get("tipo") == "erro" and mensagem.get("codigo") in ERROS_QUE_IMPEDEM_ENTRAR:
                        self._encerrando = True  # não adianta reconectar com o mesmo nome
                        return
        except (OSError, ValueError):
            pass  # conexão caiu ou dado corrompido: o laço de _executar decide se reconecta
