"""Protocolo de comunicação entre cliente e servidor do chat.

Transporte: conexão TCP. Cada mensagem é um objeto JSON em UMA linha (terminada em \\n),
codificado em UTF-8 (formato "JSON Lines").

Cliente -> servidor
    {"tipo": "entrar",    "usuario": "ana", "sala": "geral", "sessao": "<opcional>"}
    {"tipo": "mensagem",  "texto": "Oi!", "id_local": "<opcional>"}
    {"tipo": "digitando"}
    {"tipo": "pong"}
    {"tipo": "sair"}

Servidor -> cliente
    {"tipo": "entrou",    "sala", "usuario", "historico": [...], "usuarios": [...]}
    {"tipo": "mensagem",  "id", "sala", "usuario", "texto", "enviada_em", "id_local"}
    {"tipo": "presenca",  "evento": "entrou" | "saiu", "usuario", "usuarios": [...]}
    {"tipo": "digitando", "usuario"}
    {"tipo": "ping"}
    {"tipo": "sistema",   "texto"}
    {"tipo": "erro",      "codigo", "motivo"}
"""

import json
import re

LIMITE_USUARIO = 20  # caracteres
LIMITE_SALA = 30  # caracteres
LIMITE_TEXTO = 500  # caracteres
TAMANHO_MAXIMO_LINHA = 4096  # bytes por mensagem recebida

PADRAO_USUARIO = re.compile(r"[\w.-]+")  # letras (inclusive acentuadas), números, _ . -
PADRAO_SALA = re.compile(r"[a-z0-9-]+")  # minúsculas, números e hífen


class ErroDeProtocolo(Exception):
    """Mensagem recebida inválida. O código e o motivo são enviados de volta ao cliente."""

    def __init__(self, codigo: str, motivo: str):
        super().__init__(motivo)
        self.codigo = codigo
        self.motivo = motivo

    def como_mensagem(self) -> dict:
        return {"tipo": "erro", "codigo": self.codigo, "motivo": self.motivo}


def codificar(mensagem: dict) -> bytes:
    """Transforma um dicionário em uma linha JSON pronta para enviar pelo socket."""
    return (json.dumps(mensagem, ensure_ascii=False) + "\n").encode("utf-8")


def _texto(dados: dict, campo: str) -> str:
    valor = dados.get(campo)
    return valor.strip() if isinstance(valor, str) else ""


def _validar_entrar(dados: dict) -> dict:
    usuario = _texto(dados, "usuario")
    sala = _texto(dados, "sala").lower()
    sessao = _texto(dados, "sessao")[:64] or None

    if not usuario:
        raise ErroDeProtocolo("USUARIO_INVALIDO", "Informe um nome de usuário.")
    if len(usuario) > LIMITE_USUARIO:
        raise ErroDeProtocolo("USUARIO_INVALIDO", f"O nome deve ter no máximo {LIMITE_USUARIO} caracteres.")
    if not PADRAO_USUARIO.fullmatch(usuario):
        raise ErroDeProtocolo("USUARIO_INVALIDO", "Use apenas letras, números, ponto, hífen ou sublinhado no nome.")

    if not sala:
        raise ErroDeProtocolo("SALA_INVALIDA", "Informe o nome da sala.")
    if len(sala) > LIMITE_SALA:
        raise ErroDeProtocolo("SALA_INVALIDA", f"O nome da sala deve ter no máximo {LIMITE_SALA} caracteres.")
    if not PADRAO_SALA.fullmatch(sala):
        raise ErroDeProtocolo("SALA_INVALIDA", "Use apenas letras minúsculas, números e hífen no nome da sala.")

    return {"tipo": "entrar", "usuario": usuario, "sala": sala, "sessao": sessao}


def _validar_mensagem(dados: dict) -> dict:
    texto = _texto(dados, "texto")
    if not texto:
        raise ErroDeProtocolo("MENSAGEM_VAZIA", "A mensagem não pode ser vazia.")
    if len(texto) > LIMITE_TEXTO:
        raise ErroDeProtocolo("MENSAGEM_LONGA", f"A mensagem deve ter no máximo {LIMITE_TEXTO} caracteres.")
    id_local = _texto(dados, "id_local")[:64] or None
    return {"tipo": "mensagem", "texto": texto, "id_local": id_local}


def interpretar(linha: bytes) -> dict:
    """Decodifica e valida uma linha recebida do cliente.

    Devolve o comando já normalizado ou levanta ErroDeProtocolo.
    """
    try:
        dados = json.loads(linha.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ErroDeProtocolo("JSON_INVALIDO", "A mensagem enviada não é um JSON válido.") from None

    if not isinstance(dados, dict):
        raise ErroDeProtocolo("JSON_INVALIDO", "A mensagem deve ser um objeto JSON.")

    tipo = dados.get("tipo")
    if tipo == "entrar":
        return _validar_entrar(dados)
    if tipo == "mensagem":
        return _validar_mensagem(dados)
    if tipo in ("digitando", "pong", "sair"):
        return {"tipo": tipo}
    raise ErroDeProtocolo("TIPO_DESCONHECIDO", f"Tipo de mensagem desconhecido: {tipo!r}.")
