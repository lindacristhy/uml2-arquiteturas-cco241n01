"""Cliente gráfico do chat (janela feita com Tkinter, que já vem com o Python).

Uso:
    python cliente_gui.py
    python cliente_gui.py --usuario ana --sala geral --host 127.0.0.1 --porta 5000

O servidor precisa estar rodando (docker compose up). Abra duas janelas com
nomes diferentes para conversar.
"""

import argparse
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from interface import CORES, TelaChat, TelaEntrada
from rede import ClienteRede

INTERVALO_LEITURA_MS = 50  # de quanto em quanto tempo a janela olha a fila de eventos
INTERVALO_DIGITANDO_S = 2  # não avisa "digitando" mais de uma vez a cada 2 segundos


def hora_local(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone().strftime("%H:%M")
    except (ValueError, AttributeError):
        return datetime.now().strftime("%H:%M")


class AplicativoChat:
    def __init__(self, padrao: dict):
        self.padrao = padrao
        self.raiz = tk.Tk()
        self.raiz.title("Chat em tempo real")
        self.raiz.geometry("780x540")
        self.raiz.minsize(560, 380)
        self.raiz.configure(background=CORES["fundo"])
        self.raiz.protocol("WM_DELETE_WINDOW", self.fechar)
        ttk.Style(self.raiz).configure("TFrame", background=CORES["fundo"])
        ttk.Style(self.raiz).configure("TLabel", background=CORES["fundo"])

        self.tela = None
        self.rede = None
        self._ultimo_digitando = 0.0
        self.mostrar_entrada()

    # ----------------------------------------------------------- navegação

    def _trocar_tela(self, nova) -> None:
        if self.tela is not None:
            self.tela.destroy()
        self.tela = nova
        self.tela.pack(fill="both", expand=True)

    def mostrar_entrada(self, erro: str = None) -> None:
        self.raiz.title("Chat em tempo real")
        self._trocar_tela(TelaEntrada(self.raiz, self.entrar, self.padrao, erro))

    def entrar(self, usuario: str, sala: str, host: str, porta: int) -> None:
        self.padrao.update(usuario=usuario, sala=sala, host=host, porta=porta)
        self.raiz.title(f"#{sala} · {usuario}")
        self._trocar_tela(TelaChat(self.raiz, usuario, sala, self.enviar, self.digitar, self.sair))
        self.rede = ClienteRede(host, porta, usuario, sala)
        self.rede.iniciar()
        self._ler_eventos(self.rede)

    def sair(self) -> None:
        if self.rede:
            self.rede.encerrar()
            self.rede = None
        self.mostrar_entrada()

    def fechar(self) -> None:
        if self.rede:
            self.rede.encerrar()
        self.raiz.destroy()

    # ----------------------------------------------------------- ações vindas da tela

    def enviar(self, texto: str) -> bool:
        if self.rede and self.rede.enviar_texto(texto):
            return True
        self.tela.adicionar_sistema("Sem conexão com o servidor. A mensagem não foi enviada.", erro=True)
        return False

    def digitar(self) -> None:
        agora = datetime.now().timestamp()
        if self.rede and agora - self._ultimo_digitando > INTERVALO_DIGITANDO_S:
            self._ultimo_digitando = agora
            self.rede.avisar_digitando()

    # ----------------------------------------------------------- eventos vindos da rede

    def _ler_eventos(self, rede: ClienteRede) -> None:
        if rede is not self.rede:  # o usuário saiu: para de ler esta conexão
            return
        while not rede.eventos.empty():
            self._tratar(rede.eventos.get_nowait())
            if rede is not self.rede:
                return
        self.raiz.after(INTERVALO_LEITURA_MS, self._ler_eventos, rede)

    def _tratar(self, mensagem: dict) -> None:
        tela = self.tela
        tipo = mensagem.get("tipo")

        if tipo == "mensagem":
            tela.adicionar_mensagem(mensagem["usuario"], mensagem["texto"], hora_local(mensagem["enviada_em"]))
        elif tipo == "entrou":
            if mensagem["historico"]:
                tela.adicionar_sistema(f"Últimas {len(mensagem['historico'])} mensagens da sala:")
                for antiga in mensagem["historico"]:
                    tela.adicionar_mensagem(antiga["usuario"], antiga["texto"], hora_local(antiga["enviada_em"]))
            tela.adicionar_sistema(f"Você entrou na sala #{mensagem['sala']}.")
            tela.atualizar_usuarios(mensagem["usuarios"])
        elif tipo == "presenca":
            verbo = "entrou na" if mensagem["evento"] == "entrou" else "saiu da"
            tela.adicionar_sistema(f"{mensagem['usuario']} {verbo} sala.")
            tela.atualizar_usuarios(mensagem["usuarios"])
        elif tipo == "digitando":
            tela.mostrar_digitando(mensagem["usuario"])
        elif tipo == "sistema":
            tela.adicionar_sistema(mensagem["texto"])
        elif tipo == "erro":
            if mensagem["codigo"] in ("NOME_EM_USO", "USUARIO_INVALIDO", "SALA_INVALIDA"):
                self.rede.encerrar()
                self.rede = None
                self.mostrar_entrada(erro=mensagem["motivo"])
            else:
                tela.adicionar_sistema(mensagem["motivo"], erro=True)
        elif tipo == "_estado":
            tela.definir_estado(mensagem["texto"], mensagem["estado"] == "conectado")
            if mensagem["estado"] != "conectado":
                tela.adicionar_sistema(mensagem["texto"], erro=True)

    def executar(self) -> None:
        self.raiz.mainloop()


def ler_argumentos() -> dict:
    parser = argparse.ArgumentParser(description="Cliente gráfico do chat em tempo real")
    parser.add_argument("--host", default=os.environ.get("CHAT_HOST", "127.0.0.1"))
    parser.add_argument("--porta", type=int, default=int(os.environ.get("CHAT_PORTA", "5000")))
    parser.add_argument("--usuario", default="")
    parser.add_argument("--sala", default="geral")
    return vars(parser.parse_args())


if __name__ == "__main__":
    AplicativoChat(ler_argumentos()).executar()
