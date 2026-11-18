"""Salas de chat: quem está em cada sala, histórico recente e difusão de mensagens.

Esta parte não conhece sockets. Cada participante só precisa ter os atributos
`usuario` e `sessao` e o método `enviar(mensagem: dict) -> bool`.
Isso deixa a regra de negócio fácil de testar (veja tests/test_salas.py).
"""

import itertools
from collections import deque
from datetime import datetime, timezone

from protocolo import ErroDeProtocolo

TAMANHO_HISTORICO = 50  # últimas mensagens guardadas por sala


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class Sala:
    def __init__(self, nome: str, tamanho_historico: int):
        self.nome = nome
        self.membros = {}  # nome do usuário em minúsculas -> participante
        self.historico = deque(maxlen=tamanho_historico)

    def usuarios(self) -> list:
        return sorted((p.usuario for p in self.membros.values()), key=str.casefold)


class GerenciadorDeSalas:
    def __init__(self, tamanho_historico: int = TAMANHO_HISTORICO):
        self._salas = {}
        self._tamanho_historico = tamanho_historico
        self._proximo_id = itertools.count(1)

    def _sala(self, nome: str) -> Sala:
        if nome not in self._salas:
            self._salas[nome] = Sala(nome, self._tamanho_historico)
        return self._salas[nome]

    def entrar(self, sala: str, participante) -> object:
        """Coloca o participante na sala.

        Devolve o participante antigo quando for uma reconexão (mesmo nome e mesma sessão),
        para que o servidor encerre a conexão antiga. Devolve None numa entrada normal.
        Levanta ErroDeProtocolo se o nome já estiver em uso por outra pessoa.
        """
        s = self._sala(sala)
        chave = participante.usuario.casefold()
        atual = s.membros.get(chave)
        substituido = None
        if atual is not None and atual is not participante:
            mesma_sessao = participante.sessao is not None and atual.sessao == participante.sessao
            if not mesma_sessao:
                raise ErroDeProtocolo(
                    "NOME_EM_USO", f"Já existe alguém chamado '{atual.usuario}' na sala '{sala}'."
                )
            substituido = atual
        s.membros[chave] = participante
        return substituido

    def sair(self, sala: str, participante) -> bool:
        """Remove o participante da sala. Devolve True se ele estava lá."""
        s = self._salas.get(sala)
        if s is None:
            return False
        chave = participante.usuario.casefold()
        if s.membros.get(chave) is participante:
            del s.membros[chave]
            return True
        return False

    def registrar_mensagem(self, sala: str, usuario: str, texto: str, id_local=None) -> dict:
        mensagem = {
            "tipo": "mensagem",
            "id": next(self._proximo_id),
            "sala": sala,
            "usuario": usuario,
            "texto": texto,
            "enviada_em": _agora_iso(),
        }
        if id_local:
            mensagem["id_local"] = id_local
        self._sala(sala).historico.append(mensagem)
        return mensagem

    def difundir(self, sala: str, mensagem: dict, exceto=None) -> int:
        """Envia a mensagem para todos da sala (menos `exceto`). Devolve quantos receberam."""
        s = self._salas.get(sala)
        if s is None:
            return 0
        entregues = 0
        for participante in list(s.membros.values()):
            if participante is exceto:
                continue
            if participante.enviar(mensagem):
                entregues += 1
        return entregues

    def usuarios(self, sala: str) -> list:
        s = self._salas.get(sala)
        return s.usuarios() if s else []

    def historico(self, sala: str) -> list:
        s = self._salas.get(sala)
        return list(s.historico) if s else []

    def total_online(self) -> int:
        return sum(len(s.membros) for s in self._salas.values())
