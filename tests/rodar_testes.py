"""Roda todos os testes da pasta tests e grava o relatório de execução.

O relatório (console e arquivo relatorio_testes.txt) lista cada caso de teste
executado e o resultado final: E indica erro ao executar o código testado e F
indica falha, quando o código funciona mas gera comportamento diferente do
esperado.

Como rodar (a partir da raiz do projeto):
    python tests/rodar_testes.py
"""

import contextlib
import io
import os
import sys
import unittest

PASTA = os.path.dirname(os.path.abspath(__file__))
RELATORIO = os.path.join(PASTA, "relatorio_testes.txt")

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(PASTA, pattern="test_*.py")

    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        resultado = unittest.TextTestRunner(stream=saida).run(suite)

    texto = saida.getvalue()
    print(texto)
    with open(RELATORIO, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    print("Relatório gravado em " + RELATORIO)
    sys.exit(0 if resultado.wasSuccessful() else 1)