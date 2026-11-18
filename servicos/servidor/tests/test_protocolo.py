import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from protocolo import LIMITE_TEXTO, ErroDeProtocolo, codificar, interpretar  # noqa: E402


def linha(texto: str) -> bytes:
    return (texto + "\n").encode("utf-8")


class TestInterpretar(unittest.TestCase):
    def assertErro(self, bruto: str, codigo: str):
        with self.assertRaises(ErroDeProtocolo) as ctx:
            interpretar(linha(bruto))
        self.assertEqual(ctx.exception.codigo, codigo)

    def test_entrar_valido_normaliza_campos(self):
        comando = interpretar(linha('{"tipo": "entrar", "usuario": "  João ", "sala": "Geral"}'))
        self.assertEqual(comando, {"tipo": "entrar", "usuario": "João", "sala": "geral", "sessao": None})

    def test_entrar_sem_usuario(self):
        self.assertErro('{"tipo": "entrar", "usuario": "", "sala": "geral"}', "USUARIO_INVALIDO")

    def test_entrar_usuario_com_caractere_proibido(self):
        self.assertErro('{"tipo": "entrar", "usuario": "<script>", "sala": "geral"}', "USUARIO_INVALIDO")

    def test_entrar_sala_invalida(self):
        self.assertErro('{"tipo": "entrar", "usuario": "ana", "sala": "sala geral!"}', "SALA_INVALIDA")

    def test_mensagem_valida(self):
        comando = interpretar(linha('{"tipo": "mensagem", "texto": " Olá ", "id_local": "x1"}'))
        self.assertEqual(comando, {"tipo": "mensagem", "texto": "Olá", "id_local": "x1"})

    def test_mensagem_vazia(self):
        self.assertErro('{"tipo": "mensagem", "texto": "   "}', "MENSAGEM_VAZIA")

    def test_mensagem_longa(self):
        texto = "a" * (LIMITE_TEXTO + 1)
        self.assertErro('{"tipo": "mensagem", "texto": "%s"}' % texto, "MENSAGEM_LONGA")

    def test_json_invalido(self):
        self.assertErro("isso não é json", "JSON_INVALIDO")
        self.assertErro("[1, 2, 3]", "JSON_INVALIDO")

    def test_tipo_desconhecido(self):
        self.assertErro('{"tipo": "apagar_tudo"}', "TIPO_DESCONHECIDO")

    def test_codificar_gera_uma_linha_utf8(self):
        dados = codificar({"tipo": "sistema", "texto": "ação"})
        self.assertTrue(dados.endswith(b"\n"))
        self.assertEqual(dados.count(b"\n"), 1)
        self.assertIn("ação".encode("utf-8"), dados)


if __name__ == "__main__":
    unittest.main()
