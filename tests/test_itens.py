"""Testes do módulo itens (funções de acesso).

Este arquivo traz só os casos das funções de persistência acrescentadas
(gravar_inventario e recuperar_inventario), numerados a partir de I27. Os
casos I01 a I26 do documento, das demais funções do módulo, são de quem
implementa o itens.py e entram na mesma classe.

Cenário de cada caso: inventário reiniciado (vazio, nada equipado, ouro 0).
Catálogo usado: "espada_curta" (arma) e "pocao_vida" (consumível).

Como rodar (a partir da raiz do projeto):
    python tests/test_itens.py
    python tests/rodar_testes.py        (todos os módulos, com relatório)
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import itens


class TesteItens(unittest.TestCase):

    def setUp(self):
        """Cenário padrão: inventário reiniciado."""
        itens.reiniciar_inventario()
        pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        self.caminho = os.path.join(pasta, "inventario.xml")

    def encher_inventario(self):
        """2 poções, 1 espada equipada e 25 de ouro."""
        itens.adicionar_ao_inventario("pocao_vida", 2)
        itens.adicionar_ao_inventario("espada_curta", 1)
        itens.equipar_item("espada_curta")
        itens.adicionar_ouro(25)

    def inventario(self):
        """Lê o inventário atual."""
        codigo, inventario = itens.listar_inventario()
        self.assertEqual(codigo, 0)
        return inventario

    # ------------------------------------------------------------------
    # gravar_inventario
    # ------------------------------------------------------------------
    def test_I27_gravar_inventario_ok(self):
        print("Caso de Teste I27 - Gravar inventário em arquivo")
        self.encher_inventario()
        self.assertEqual(itens.gravar_inventario(self.caminho), (0, None))
        self.assertTrue(os.path.isfile(self.caminho))

    def test_I28_gravar_inventario_nok_caminho_invalido(self):
        print("Caso de Teste I28 - Gravar com caminho vazio ou de tipo incorreto")
        self.assertEqual(itens.gravar_inventario(""), (3, None))
        self.assertEqual(itens.gravar_inventario(123), (3, None))

    def test_I29_gravar_inventario_nok_falha_no_arquivo(self):
        print("Caso de Teste I29 - Gravar em pasta que não existe")
        caminho = os.path.join(os.path.dirname(self.caminho), "pasta_inexistente", "inventario.xml")
        self.assertEqual(itens.gravar_inventario(caminho), (5, None))

    # ------------------------------------------------------------------
    # recuperar_inventario
    # ------------------------------------------------------------------
    def test_I30_recuperar_inventario_ok(self):
        print("Caso de Teste I30 - Recuperar inventário gravado")
        self.encher_inventario()
        gravado = self.inventario()
        self.assertEqual(itens.gravar_inventario(self.caminho), (0, None))
        itens.reiniciar_inventario()
        self.assertEqual(itens.recuperar_inventario(self.caminho), (0, None))
        self.assertEqual(self.inventario(), gravado)

    def test_I31_recuperar_inventario_nok_caminho_invalido(self):
        print("Caso de Teste I31 - Recuperar com caminho vazio ou de tipo incorreto")
        self.assertEqual(itens.recuperar_inventario(""), (3, None))
        self.assertEqual(itens.recuperar_inventario(None), (3, None))

    def test_I32_recuperar_inventario_nok_arquivo_inexistente(self):
        print("Caso de Teste I32 - Recuperar de arquivo que não existe")
        self.assertEqual(itens.recuperar_inventario(self.caminho), (4, None))

    def test_I33_recuperar_inventario_nok_arquivo_invalido(self):
        print("Caso de Teste I33 - Arquivo ilegível ou inválido não altera o inventário")
        itens.adicionar_ao_inventario("pocao_vida", 1)
        antes = self.inventario()
        with open(self.caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write("isto não é xml")
        self.assertEqual(itens.recuperar_inventario(self.caminho), (5, None))
        self.assertEqual(self.inventario(), antes)


if __name__ == "__main__":
    unittest.main()