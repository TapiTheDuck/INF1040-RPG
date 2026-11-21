"""Módulo narrativa.

Guarda a história fixa do jogo (cenas, escolhas e transições) e orquestra
os momentos em que a história chama outros módulos (combate, personagem).

Convenções do projeto:
  - Todas as funções de acesso retornam (codigo_retorno, resultado).
  - Entre módulos circulam identificadores (texto), nunca a struct do personagem.
  - Este módulo não guarda estado: o id da cena atual é sempre passado por
    parâmetro (quem controla a cena atual é o módulo principal).
  - A classe do personagem é lida pelo módulo personagem; cada cena pode ter
    "variantes" por classe que substituem partes da cena (texto, escolhas...).
"""

import copy

import combate      # assumido: combate.executar_combate(id_inimigo) -> (codigo, "vitoria"|"derrota")
import personagem

# ---------------------------------------------------------------------------
# Códigos de retorno (mesmos valores em todos os módulos)
# ---------------------------------------------------------------------------
SUCESSO = 0
ERRO_ABORT = 1
ERRO_ID_REPETIDO = 2
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4

# ---------------------------------------------------------------------------
# História fixa (textos e rotas de exemplo: substituir pelos reais)
#   escolhas : {id_escolha: {"texto": ..., "proxima": id_cena}}
#   combate  : None ou {"inimigo": id_inimigo, "vitoria": id_cena, "derrota": id_cena}
#   variantes: {nome_da_classe: {chaves da cena que mudam para essa classe}}
#              (o que não for listado na variante vale o da cena base)
# ---------------------------------------------------------------------------
CENA_INICIAL = "inicio"

CENAS = {
    "inicio": {
        "texto": "[Texto padrão da cena inicial]",
        "escolhas": {
            "1": {"texto": "Seguir pela floresta", "proxima": "floresta"},
            "2": {"texto": "Entrar na vila", "proxima": "vila"},
        },
        "combate": None,
        "final": False,
        "variantes": {
            "guerreiro": {"texto": "[Texto da cena inicial para o guerreiro]"},
            "arqueiro": {"texto": "[Texto da cena inicial para o arqueiro]"},
            "mago": {
                "texto": "[Texto da cena inicial para o mago]",
                "escolhas": {
                    "1": {"texto": "Seguir pela floresta", "proxima": "floresta"},
                    "2": {"texto": "Entrar na vila", "proxima": "vila"},
                    "3": {"texto": "Examinar as runas na pedra", "proxima": "ruinas"},
                },
            },
        },
    },
    "vila": {
        "texto": "[Texto da vila]",
        "escolhas": {
            "1": {"texto": "Voltar para a estrada", "proxima": "inicio"},
        },
        "combate": None,
        "final": False,
    },
    "ruinas": {
        "texto": "[Texto das ruínas (só o mago chega aqui)]",
        "escolhas": {
            "1": {"texto": "Voltar para a estrada", "proxima": "inicio"},
        },
        "combate": None,
        "final": False,
    },
    "floresta": {
        "texto": "[Texto da emboscada na floresta]",
        "escolhas": {},
        "combate": {"inimigo": "goblin", "vitoria": "fim_vitoria", "derrota": "fim_derrota"},
        "final": False,
    },
    "fim_vitoria": {
        "texto": "[Texto do final vitorioso]",
        "escolhas": {},
        "combate": None,
        "final": True,
    },
    "fim_derrota": {
        "texto": "[Texto de game over]",
        "escolhas": {},
        "combate": None,
        "final": True,
    },
}


def _texto_valido(valor):
    return isinstance(valor, str) and valor.strip() != ""


def _classe_do_personagem():
    """Lê a classe do personagem pelo módulo personagem.

    Retorna (SUCESSO, nome_da_classe), (ERRO_ID_INEXISTENTE, None) se ainda não
    existe personagem, ou (ERRO_ABORT, None) para qualquer outro retorno.
    """
    codigo, dados = personagem.consultar_personagem()
    if codigo == personagem.SUCESSO:
        return SUCESSO, dados["classe"]["nome"]
    if codigo == personagem.ERRO_ID_INEXISTENTE:
        return ERRO_ID_INEXISTENTE, None
    return ERRO_ABORT, None


def _cena_para_classe(id_cena, classe):
    """Cópia da cena com a variante da classe aplicada (se existir)."""
    cena = copy.deepcopy(CENAS[id_cena])
    variantes = cena.pop("variantes", {})
    cena.update(variantes.get(classe, {}))
    cena["id"] = id_cena
    return cena


def iniciar_cena(id_cena):
    """Retorna os dados da cena, já adaptados à classe do personagem.

    O resultado é uma cópia: {"id", "texto", "escolhas", "combate", "final"}.

    Retornos:
        (SUCESSO, cena)               cena encontrada e adaptada à classe
        (ERRO_ABORT, None)            falha inesperada ao consultar o personagem
        (ERRO_DADOS_INVALIDOS, None)  id_cena vazio ou que não é texto
        (ERRO_ID_INEXISTENTE, None)   cena inexistente ou personagem não criado
    """
    if not _texto_valido(id_cena):
        return ERRO_DADOS_INVALIDOS, None
    if id_cena not in CENAS:
        return ERRO_ID_INEXISTENTE, None

    codigo, classe = _classe_do_personagem()
    if codigo != SUCESSO:
        return codigo, None

    return SUCESSO, _cena_para_classe(id_cena, classe)


def processar_escolha(id_cena, id_escolha):
    """Informa para qual cena a escolha feita na cena atual leva.

    Considera as escolhas disponíveis para a classe do personagem.

    Retornos:
        (SUCESSO, id_proxima_cena)    escolha válida
        (ERRO_ABORT, None)            falha ao consultar o personagem ou a escolha
                                      aponta para uma cena que não existe
        (ERRO_DADOS_INVALIDOS, None)  id_cena ou id_escolha vazio ou que não é texto
        (ERRO_ID_INEXISTENTE, None)   cena inexistente, escolha inexistente para a
                                      classe ou personagem não criado
    """
    if not _texto_valido(id_cena) or not _texto_valido(id_escolha):
        return ERRO_DADOS_INVALIDOS, None
    if id_cena not in CENAS:
        return ERRO_ID_INEXISTENTE, None

    codigo, classe = _classe_do_personagem()
    if codigo != SUCESSO:
        return codigo, None

    escolhas = _cena_para_classe(id_cena, classe)["escolhas"]
    if id_escolha not in escolhas:
        return ERRO_ID_INEXISTENTE, None

    id_proxima = escolhas[id_escolha]["proxima"]
    if id_proxima not in CENAS:
        return ERRO_ABORT, None
    return SUCESSO, id_proxima


def iniciar_combate(id_inimigo):
    """Executa o combate contra o inimigo; se o jogador perder, o mata.

    O módulo principal usa o resultado ("vitoria" ou "derrota") para escolher
    a próxima cena em cena["combate"].

    Retornos:
        (SUCESSO, "vitoria"|"derrota")  combate concluído
        (ERRO_ABORT, None)              combate/personagem falharam ou resultado inesperado
        (ERRO_DADOS_INVALIDOS, None)    id_inimigo vazio ou que não é texto
        (ERRO_ID_INEXISTENTE, None)     ainda não existe personagem criado
    """
    if not _texto_valido(id_inimigo):
        return ERRO_DADOS_INVALIDOS, None

    codigo, _ = personagem.consultar_personagem()
    if codigo == personagem.ERRO_ID_INEXISTENTE:
        return ERRO_ID_INEXISTENTE, None
    if codigo != personagem.SUCESSO:
        return ERRO_ABORT, None

    codigo, resultado = combate.executar_combate(id_inimigo)
    if codigo != combate.SUCESSO or resultado not in ("vitoria", "derrota"):
        return ERRO_ABORT, None

    if resultado == "derrota":
        codigo, _ = personagem.matar_personagem()
        if codigo != personagem.SUCESSO:
            return ERRO_ABORT, None

    return SUCESSO, resultado

def aplicar_dano(valor):
    """Assertiva de entrada: valor é inteiro maior ou igual a zero.
    Assertivas de saída: (0, pv) -> PV reduzido em valor, nunca abaixo de 0;
    (3, None) valor inválido; (4, None) sem personagem; em erro, nada é alterado."""
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None
    if not isinstance(valor, int) or valor < 0:
        return ERRO_DADOS_INVALIDOS, None
    _personagem["pv"] = max(0, _personagem["pv"] - valor)
    return SUCESSO, _personagem["pv"]