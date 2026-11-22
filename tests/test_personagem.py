"""Testes do módulo personagem (funções de acesso).

Os casos P01 a P21 seguem a seção 7.1 do documento. Os casos P22 a P29 cobrem
as funções de persistência acrescentadas depois (gravar_personagem e
recuperar_personagem).

Como rodar (a partir da raiz do projeto):
    python tests/test_personagem.py
    python tests/rodar_testes.py        (todos os módulos, com relatório)
"""

import importlib
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import personagem


class TestePersonagem(unittest.TestCase):

    def setUp(self):
        """Cenário padrão: guerreiro Lia (nível 1, xp 0, xp_max 100, pv 12)."""
        self.sem_personagem()
        personagem.criar_personagem("Lia", "guerreiro")
        pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        self.caminho = os.path.join(pasta, "personagem.xml")

    def sem_personagem(self):
        """Reinicia o módulo: volta ao estado em que nenhum personagem existe."""
        importlib.reload(personagem)

    def dados(self):
        """Consulta o personagem atual (que precisa existir)."""
        codigo, dados = personagem.consultar_personagem()
        self.assertEqual(codigo, 0)
        return dados

    # ------------------------------------------------------------------
    # criar_personagem
    # ------------------------------------------------------------------
    def test_P01_criar_personagem_ok(self):
        print("Caso de Teste P01 - Criar personagem com nome e classe válidos")
        self.sem_personagem()
        self.assertEqual(personagem.criar_personagem("Lia", "guerreiro"), (0, None))
        dados = self.dados()
        self.assertEqual((dados["nivel"], dados["pv"]), (1, 12))

    def test_P02_criar_personagem_nok_nome_vazio(self):
        print("Caso de Teste P02 - Criar personagem com nome vazio")
        self.sem_personagem()
        self.assertEqual(personagem.criar_personagem("", "mago"), (3, None))
        self.assertEqual(personagem.consultar_personagem(), (4, None))

    def test_P03_criar_personagem_nok_classe_inexistente(self):
        print("Caso de Teste P03 - Criar personagem com classe inexistente")
        self.sem_personagem()
        self.assertEqual(personagem.criar_personagem("Lia", "paladino"), (3, None))
        self.assertEqual(personagem.consultar_personagem(), (4, None))

    def test_P04_criar_personagem_nok_nome_tipo_incorreto(self):
        print("Caso de Teste P04 - Criar personagem com nome de tipo incorreto")
        self.sem_personagem()
        self.assertEqual(personagem.criar_personagem(123, "arqueiro"), (3, None))
        self.assertEqual(personagem.consultar_personagem(), (4, None))

    # ------------------------------------------------------------------
    # consultar_personagem
    # ------------------------------------------------------------------
    def test_P05_consultar_personagem_ok(self):
        print("Caso de Teste P05 - Consultar personagem existente")
        codigo, dados = personagem.consultar_personagem()
        self.assertEqual(codigo, 0)
        self.assertEqual(dados["nome"], "Lia")
        self.assertEqual(dados["classe"]["nome"], "guerreiro")
        self.assertEqual([dados[campo] for campo in ("nivel", "xp", "xp_max", "pv", "pv_max", "vivo")],
                         [1, 0, 100, 12, 12, True])
        self.assertEqual(sorted(dados["classe"]["atributos"]),
                         ["carisma", "constituicao", "destreza", "forca", "inteligencia", "sabedoria"])
        dados["pv"] = 0  # alterar a cópia não pode alterar o personagem
        self.assertEqual(self.dados()["pv"], 12)

    def test_P06_consultar_personagem_nok_sem_personagem(self):
        print("Caso de Teste P06 - Consultar sem personagem criado")
        self.sem_personagem()
        self.assertEqual(personagem.consultar_personagem(), (4, None))

    # ------------------------------------------------------------------
    # subir_xp
    # ------------------------------------------------------------------
    def test_P07_subir_xp_ok_sem_passar_de_nivel(self):
        print("Caso de Teste P07 - Somar experiência sem passar de nível")
        self.assertEqual(personagem.subir_xp(30), (0, 1))
        dados = self.dados()
        self.assertEqual((dados["nivel"], dados["xp"]), (1, 30))

    def test_P08_subir_xp_ok_passando_de_nivel(self):
        print("Caso de Teste P08 - Somar experiência suficiente para passar de nível")
        self.assertEqual(personagem.subir_xp(150), (0, 2))
        dados = self.dados()
        self.assertEqual((dados["nivel"], dados["xp"]), (2, 50))
        self.assertGreater(dados["pv_max"], 12)

    def test_P09_subir_xp_nok_valor_negativo(self):
        print("Caso de Teste P09 - Somar experiência negativa")
        self.assertEqual(personagem.subir_xp(-5), (3, None))
        self.assertEqual(self.dados()["xp"], 0)

    def test_P10_subir_xp_nok_tipo_incorreto(self):
        print("Caso de Teste P10 - Somar experiência de tipo incorreto")
        self.assertEqual(personagem.subir_xp("50"), (3, None))

    def test_P11_subir_xp_nok_sem_personagem(self):
        print("Caso de Teste P11 - Somar experiência sem personagem")
        self.sem_personagem()
        self.assertEqual(personagem.subir_xp(50), (4, None))

    # ------------------------------------------------------------------
    # aplicar_dano
    # ------------------------------------------------------------------
    def test_P12_aplicar_dano_ok_menor_que_pv(self):
        print("Caso de Teste P12 - Aplicar dano menor que o PV")
        self.assertEqual(personagem.aplicar_dano(5), (0, 7))

    def test_P13_aplicar_dano_ok_maior_que_pv(self):
        print("Caso de Teste P13 - Aplicar dano maior que o PV")
        self.assertEqual(personagem.aplicar_dano(20), (0, 0))
        dados = self.dados()
        self.assertEqual(dados["pv"], 0)
        self.assertFalse(dados["vivo"])

    def test_P14_aplicar_dano_nok_valor_negativo(self):
        print("Caso de Teste P14 - Aplicar dano negativo")
        self.assertEqual(personagem.aplicar_dano(-3), (3, None))
        self.assertEqual(self.dados()["pv"], 12)

    def test_P15_aplicar_dano_nok_sem_personagem(self):
        print("Caso de Teste P15 - Aplicar dano sem personagem")
        self.sem_personagem()
        self.assertEqual(personagem.aplicar_dano(5), (4, None))

    # ------------------------------------------------------------------
    # curar
    # ------------------------------------------------------------------
    def test_P16_curar_ok_parte_dos_pontos(self):
        print("Caso de Teste P16 - Curar parte dos pontos de vida")
        personagem.aplicar_dano(5)
        self.assertEqual(personagem.curar(3), (0, 10))

    def test_P17_curar_ok_alem_do_maximo(self):
        print("Caso de Teste P17 - Curar além do máximo")
        personagem.aplicar_dano(5)
        self.assertEqual(personagem.curar(20), (0, 12))
        dados = self.dados()
        self.assertEqual(dados["pv"], dados["pv_max"])

    def test_P18_curar_nok_valor_negativo(self):
        print("Caso de Teste P18 - Curar com valor negativo")
        self.assertEqual(personagem.curar(-1), (3, None))
        self.assertEqual(self.dados()["pv"], 12)

    def test_P19_curar_nok_sem_personagem(self):
        print("Caso de Teste P19 - Curar sem personagem")
        self.sem_personagem()
        self.assertEqual(personagem.curar(5), (4, None))

    # ------------------------------------------------------------------
    # matar_personagem
    # ------------------------------------------------------------------
    def test_P20_matar_personagem_ok(self):
        print("Caso de Teste P20 - Registrar a morte de personagem existente")
        self.assertEqual(personagem.matar_personagem(), (0, None))
        dados = self.dados()
        self.assertEqual(dados["pv"], 0)
        self.assertFalse(dados["vivo"])

    def test_P21_matar_personagem_nok_sem_personagem(self):
        print("Caso de Teste P21 - Registrar morte sem personagem")
        self.sem_personagem()
        self.assertEqual(personagem.matar_personagem(), (4, None))

    # ------------------------------------------------------------------
    # gravar_personagem
    # ------------------------------------------------------------------
    def test_P22_gravar_personagem_ok(self):
        print("Caso de Teste P22 - Gravar personagem em arquivo")
        self.assertEqual(personagem.gravar_personagem(self.caminho), (0, None))
        self.assertTrue(os.path.isfile(self.caminho))

    def test_P23_gravar_personagem_nok_caminho_invalido(self):
        print("Caso de Teste P23 - Gravar com caminho vazio ou de tipo incorreto")
        self.assertEqual(personagem.gravar_personagem(""), (3, None))
        self.assertEqual(personagem.gravar_personagem(123), (3, None))

    def test_P24_gravar_personagem_nok_sem_personagem(self):
        print("Caso de Teste P24 - Gravar sem personagem criado")
        self.sem_personagem()
        self.assertEqual(personagem.gravar_personagem(self.caminho), (4, None))
        self.assertFalse(os.path.exists(self.caminho))

    def test_P25_gravar_personagem_nok_falha_no_arquivo(self):
        print("Caso de Teste P25 - Gravar em pasta que não existe")
        caminho = os.path.join(os.path.dirname(self.caminho), "pasta_inexistente", "personagem.xml")
        self.assertEqual(personagem.gravar_personagem(caminho), (5, None))

    # ------------------------------------------------------------------
    # recuperar_personagem
    # ------------------------------------------------------------------
    def test_P26_recuperar_personagem_ok(self):
        print("Caso de Teste P26 - Recuperar personagem gravado")
        personagem.subir_xp(150)
        personagem.aplicar_dano(3)
        gravado = self.dados()
        self.assertEqual(personagem.gravar_personagem(self.caminho), (0, None))
        personagem.criar_personagem("Outro", "mago")  # estado diferente em memória
        self.assertEqual(personagem.recuperar_personagem(self.caminho), (0, None))
        self.assertEqual(self.dados(), gravado)

    def test_P27_recuperar_personagem_nok_caminho_invalido(self):
        print("Caso de Teste P27 - Recuperar com caminho vazio ou de tipo incorreto")
        self.assertEqual(personagem.recuperar_personagem(""), (3, None))
        self.assertEqual(personagem.recuperar_personagem(None), (3, None))

    def test_P28_recuperar_personagem_nok_arquivo_inexistente(self):
        print("Caso de Teste P28 - Recuperar de arquivo que não existe")
        self.assertEqual(personagem.recuperar_personagem(self.caminho), (4, None))

    def test_P29_recuperar_personagem_nok_arquivo_invalido(self):
        print("Caso de Teste P29 - Arquivo ilegível ou inválido não altera o personagem")
        antes = self.dados()
        with open(self.caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write("isto não é xml")
        self.assertEqual(personagem.recuperar_personagem(self.caminho), (5, None))
        self.assertEqual(self.dados(), antes)

        personagem.gravar_personagem(self.caminho)
        with open(self.caminho, encoding="utf-8") as arquivo:
            texto = arquivo.read()
        with open(self.caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(texto.replace("<pv>12</pv>", "<pv>99</pv>"))  # PV acima do máximo
        self.assertEqual(personagem.recuperar_personagem(self.caminho), (5, None))
        self.assertEqual(self.dados(), antes)


if __name__ == "__main__":
    unittest.main()