"""Testes do módulo narrativa (funções de acesso).

Os casos N01 a N16 seguem a seção 7.2 do documento.

Cenário de cada caso: personagem padrão (guerreiro Lia) criado, inventário
reiniciado e uma tabela de cenas de teste no lugar da história real (assim os
testes não dependem do texto da história, que muda). Nos casos de combate, o
resultado da luta é forçado com unittest.mock em vez de fixar a semente do
gerador aleatório, para o teste não depender das rolagens do módulo Combate.

Precisa dos módulos combate.py e itens.py na pasta src.

Como rodar (a partir da raiz do projeto):
    python tests/test_narrativa.py
    python tests/rodar_testes.py        (todos os módulos, com relatório)
"""

import copy
import importlib
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import combate
import itens
import narrativa
import personagem

# Cenas usadas pelos casos de teste (seção 7.2 do documento).
CENAS_TESTE = {
    "inicio": {
        "texto": "Texto base da cena inicial",
        "escolhas": {
            "1": {"texto": "Seguir pela floresta", "proxima": "floresta"},
            "2": {"texto": "Entrar na vila", "proxima": "vila"},
        },
        "combate": None,
        "final": False,
        "variantes": {
            "mago": {
                "texto": "Texto da cena inicial para o mago",
                "escolhas": {
                    "1": {"texto": "Seguir pela floresta", "proxima": "floresta"},
                    "2": {"texto": "Entrar na vila", "proxima": "vila"},
                    "3": {"texto": "Examinar as runas na pedra", "proxima": "ruinas"},
                },
            },
        },
    },
    "floresta": {
        "texto": "Texto da floresta",
        "escolhas": {"1": {"texto": "Seguir o rastro", "proxima": "emboscada"}},
        "combate": None,
        "final": False,
    },
    "emboscada": {
        "texto": "Texto da emboscada",
        "escolhas": {},
        "combate": {"inimigo": "goblin", "vitoria": "clareira", "derrota": "fim_derrota"},
        "final": False,
    },
    "clareira": {"texto": "Texto da clareira", "escolhas": {}, "combate": None, "final": True},
    "fim_derrota": {"texto": "Texto de game over", "escolhas": {}, "combate": None, "final": True},
}


def acao_atacar(estado):
    """Ação do jogador usada nos testes: sempre ataca."""
    return "atacar"


class TesteNarrativa(unittest.TestCase):

    def setUp(self):
        """Cenário padrão: guerreiro Lia, inventário vazio e cenas de teste."""
        self.sem_personagem()
        personagem.criar_personagem("Lia", "guerreiro")
        itens.reiniciar_inventario()
        cenas = mock.patch.object(narrativa, "_CENAS", copy.deepcopy(CENAS_TESTE))
        cenas.start()
        self.addCleanup(cenas.stop)

    def sem_personagem(self):
        """Reinicia o módulo personagem: nenhum personagem criado."""
        importlib.reload(personagem)

    # ------------------------------------------------------------------
    # iniciar_cena
    # ------------------------------------------------------------------
    def test_N01_iniciar_cena_ok(self):
        print("Caso de Teste N01 - Iniciar cena existente")
        codigo, cena = narrativa.iniciar_cena("inicio")
        self.assertEqual(codigo, 0)
        self.assertEqual(cena["texto"], CENAS_TESTE["inicio"]["texto"])
        self.assertEqual(sorted(cena["escolhas"]), ["1", "2"])
        self.assertIsNone(cena["combate"])
        self.assertFalse(cena["final"])
        cena["texto"] = "alterado"  # a cena devolvida é uma cópia
        self.assertEqual(narrativa.iniciar_cena("inicio")[1]["texto"], CENAS_TESTE["inicio"]["texto"])

    def test_N02_iniciar_cena_ok_variante_de_classe(self):
        print("Caso de Teste N02 - Iniciar cena com variante de classe")
        personagem.criar_personagem("Lia", "mago")
        codigo, cena = narrativa.iniciar_cena("inicio")
        self.assertEqual(codigo, 0)
        self.assertEqual(cena["texto"], "Texto da cena inicial para o mago")
        self.assertEqual(sorted(cena["escolhas"]), ["1", "2", "3"])

    def test_N03_iniciar_cena_nok_sem_personagem(self):
        print("Caso de Teste N03 - Iniciar cena sem personagem criado")
        self.sem_personagem()
        self.assertEqual(narrativa.iniciar_cena("inicio"), (1, None))

    def test_N04_iniciar_cena_nok_identificador_tipo_incorreto(self):
        print("Caso de Teste N04 - Iniciar cena com identificador de tipo incorreto")
        self.assertEqual(narrativa.iniciar_cena(10), (3, None))

    def test_N05_iniciar_cena_nok_cena_inexistente(self):
        print("Caso de Teste N05 - Iniciar cena inexistente")
        self.assertEqual(narrativa.iniciar_cena("cena_999"), (4, None))

    # ------------------------------------------------------------------
    # processar_escolha
    # ------------------------------------------------------------------
    def test_N06_processar_escolha_ok(self):
        print("Caso de Teste N06 - Processar escolha válida")
        self.assertEqual(narrativa.processar_escolha("inicio", "1"), (0, "floresta"))

    def test_N07_processar_escolha_nok_sem_personagem(self):
        print("Caso de Teste N07 - Processar escolha sem personagem criado")
        self.sem_personagem()
        self.assertEqual(narrativa.processar_escolha("inicio", "1"), (1, None))

    def test_N08_processar_escolha_nok_tipo_incorreto(self):
        print("Caso de Teste N08 - Processar escolha com parâmetro de tipo incorreto")
        self.assertEqual(narrativa.processar_escolha("inicio", 1), (3, None))

    def test_N09_processar_escolha_nok_escolha_inexistente(self):
        print("Caso de Teste N09 - Processar escolha inexistente")
        self.assertEqual(narrativa.processar_escolha("inicio", "9"), (4, None))

    def test_N10_processar_escolha_nok_escolha_de_outra_classe(self):
        print("Caso de Teste N10 - Processar escolha exclusiva de outra classe")
        self.assertEqual(narrativa.processar_escolha("inicio", "3"), (4, None))

    # ------------------------------------------------------------------
    # iniciar_combate
    # ------------------------------------------------------------------
    def test_N11_iniciar_combate_ok_vitoria(self):
        print("Caso de Teste N11 - Combate com vitória do jogador")
        with mock.patch.object(combate, "orquestrar_combate", return_value=(0, "jogador")):
            retorno = narrativa.iniciar_combate("emboscada", acao_atacar)
        self.assertEqual(retorno, (0, {"vitoria": True, "proxima_cena": "clareira"}))
        inventario = itens.listar_inventario()[1]
        self.assertEqual(inventario["itens"], {"pocao_vida": 1})
        self.assertEqual(inventario["ouro"], 5)
        self.assertEqual(personagem.consultar_personagem()[1]["xp"], 50)

    def test_N12_iniciar_combate_ok_derrota(self):
        print("Caso de Teste N12 - Combate com derrota do jogador")
        with mock.patch.object(combate, "orquestrar_combate", return_value=(0, "inimigo")):
            retorno = narrativa.iniciar_combate("emboscada", acao_atacar)
        self.assertEqual(retorno, (0, {"vitoria": False, "proxima_cena": "fim_derrota"}))
        self.assertFalse(personagem.consultar_personagem()[1]["vivo"])
        inventario = itens.listar_inventario()[1]
        self.assertEqual(inventario["itens"], {})
        self.assertEqual(inventario["ouro"], 0)

    def test_N13_iniciar_combate_nok_falha_no_combate(self):
        print("Caso de Teste N13 - Combate interrompido por falha no módulo Combate")
        self.sem_personagem()
        self.assertEqual(narrativa.iniciar_combate("emboscada", acao_atacar), (1, None))

    def test_N14_iniciar_combate_nok_obter_acao_invalida(self):
        print("Caso de Teste N14 - Combate com obter_acao que não é função")
        self.assertEqual(narrativa.iniciar_combate("emboscada", "atacar"), (3, None))

    def test_N15_iniciar_combate_nok_cena_sem_combate(self):
        print("Caso de Teste N15 - Combate em cena sem combate")
        self.assertEqual(narrativa.iniciar_combate("inicio", acao_atacar), (4, None))

    def test_N16_iniciar_combate_nok_cena_inexistente(self):
        print("Caso de Teste N16 - Combate em cena inexistente")
        self.assertEqual(narrativa.iniciar_combate("cena_999", acao_atacar), (4, None))


if __name__ == "__main__":
    unittest.main()