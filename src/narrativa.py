"""Módulo narrativa.

Guarda a história fixa do jogo (cenas, escolhas e transições) e conduz os
momentos em que a história chama outros módulos (combate, itens, personagem).

Convenções do projeto:
  - Todas as funções de acesso retornam (codigo_retorno, resultado).
  - Este módulo não guarda estado: o id da cena atual é sempre passado por
    parâmetro (quem controla a cena atual é o módulo principal).
  - Cada cena pode ter "variantes" por classe, que substituem partes dela
    (texto, escolhas...); o que não for listado vale o da cena base.
"""

import copy

import combate
import itens
import personagem

__all__ = ["iniciar_cena", "processar_escolha", "iniciar_combate"]

# Códigos de retorno (mesmos valores em todos os módulos)
SUCESSO = 0
ERRO_ABORT = 1
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4

# História fixa (textos de exemplo: substituir pelos reais)
#   escolhas : {id_escolha: {"texto": ..., "proxima": id_cena}}
#   combate  : None ou {"inimigo": id_inimigo, "vitoria": id_cena, "derrota": id_cena}
#   variantes: {nome_da_classe: {chaves da cena que mudam para essa classe}}
_CENAS = {
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
        "escolhas": {"1": {"texto": "Voltar para a estrada", "proxima": "inicio"}},
        "combate": None,
        "final": False,
    },
    "ruinas": {
        "texto": "[Texto das ruínas (só o mago chega aqui)]",
        "escolhas": {"1": {"texto": "Voltar para a estrada", "proxima": "inicio"}},
        "combate": None,
        "final": False,
    },
    "floresta": {
        "texto": "[Texto da floresta]",
        "escolhas": {"1": {"texto": "Seguir o rastro", "proxima": "emboscada"}},
        "combate": None,
        "final": False,
    },
    "emboscada": {
        "texto": "[Texto da emboscada de goblins]",
        "escolhas": {},
        "combate": {"inimigo": "goblin", "vitoria": "clareira", "derrota": "fim_derrota"},
        "final": False,
    },
    "clareira": {
        "texto": "[Texto da clareira / final vitorioso]",
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
    """True se valor é uma string não vazia."""
    return isinstance(valor, str) and valor.strip() != ""


def _classe_do_personagem():
    """Lê a classe pelo módulo personagem.

    Retorna (SUCESSO, nome_da_classe) ou (ERRO_ABORT, None) se a consulta
    ao personagem falhar (por exemplo, personagem ainda não criado).
    """
    codigo, dados = personagem.consultar_personagem()
    if codigo != personagem.SUCESSO:
        return ERRO_ABORT, None
    return SUCESSO, dados["classe"]["nome"]


def _cena_para_classe(id_cena, classe):
    """Cópia da cena com a variante da classe aplicada (se existir)."""
    cena = copy.deepcopy(_CENAS[id_cena])
    variantes = cena.pop("variantes", {})
    cena.update(variantes.get(classe, {}))
    cena["id"] = id_cena
    return cena


def iniciar_cena(id_cena):
    """Retorna uma cópia da cena, já adaptada à classe do personagem.

    Assertivas de entrada:
        id_cena (str): texto não vazio; deve ser o identificador de uma cena
            da história (o Principal guarda o identificador da cena atual).
        Exige que um personagem já tenha sido criado, porque a classe dele
        define a variante da cena.

    Retornos:
        (SUCESSO, cena)               cena encontrada e adaptada
        (ERRO_ABORT, None)            a consulta ao personagem falhou
        (ERRO_DADOS_INVALIDOS, None)  id_cena não é texto (ou é vazio)
        (ERRO_ID_INEXISTENTE, None)   não existe cena com esse identificador
    """
    if not _texto_valido(id_cena):
        return ERRO_DADOS_INVALIDOS, None
    if id_cena not in _CENAS:
        return ERRO_ID_INEXISTENTE, None

    codigo, classe = _classe_do_personagem()
    if codigo != SUCESSO:
        return ERRO_ABORT, None

    return SUCESSO, _cena_para_classe(id_cena, classe)


def processar_escolha(id_cena, id_escolha):
    """Informa para qual cena a escolha feita na cena atual leva.

    Assertivas de entrada:
        id_cena (str): texto não vazio; identificador da cena atual.
        id_escolha (str): texto não vazio; identificador de uma das escolhas
            dessa cena para a classe do personagem (escolhas exclusivas de
            outra classe não são aceitas).
        Exige que um personagem já tenha sido criado.

    Retornos:
        (SUCESSO, id_proxima_cena)    escolha válida
        (ERRO_ABORT, None)            a consulta ao personagem falhou
        (ERRO_DADOS_INVALIDOS, None)  id_cena ou id_escolha não é texto
        (ERRO_ID_INEXISTENTE, None)   cena inexistente, ou escolha inexistente
                                      nessa cena para a classe do personagem
    """
    if not _texto_valido(id_cena) or not _texto_valido(id_escolha):
        return ERRO_DADOS_INVALIDOS, None
    if id_cena not in _CENAS:
        return ERRO_ID_INEXISTENTE, None

    codigo, classe = _classe_do_personagem()
    if codigo != SUCESSO:
        return ERRO_ABORT, None

    escolhas = _cena_para_classe(id_cena, classe)["escolhas"]
    if id_escolha not in escolhas:
        return ERRO_ID_INEXISTENTE, None
    return SUCESSO, escolhas[id_escolha]["proxima"]


def iniciar_combate(id_cena, obter_acao):
    """Conduz o combate da cena e aplica as consequências.

    Chama combate.orquestrar_combate. Em caso de vitória, pega a recompensa
    em combate.dropar_itens e a entrega por itens.adicionar_ao_inventario,
    itens.adicionar_ouro e personagem.subir_xp. Em caso de derrota, chama
    personagem.matar_personagem.

    Assertivas de entrada:
        id_cena (str): texto não vazio; identificador de uma cena que tenha
            combate associado.
        obter_acao (função): recebe uma cópia do estado do combate e devolve
            a ação do jogador no turno; é fornecida pelo Principal e apenas
            repassada ao módulo Combate.

    Retornos:
        (SUCESSO, {"vitoria": bool, "proxima_cena": id})  combate concluído
        (ERRO_ABORT, None)            alguma chamada a Combate, Personagem
                                      ou Itens falhou
        (ERRO_DADOS_INVALIDOS, None)  id_cena não é texto ou obter_acao não
                                      é função
        (ERRO_ID_INEXISTENTE, None)   cena inexistente ou sem combate
    """
    if not _texto_valido(id_cena) or not callable(obter_acao):
        return ERRO_DADOS_INVALIDOS, None
    if id_cena not in _CENAS or _CENAS[id_cena]["combate"] is None:
        return ERRO_ID_INEXISTENTE, None

    dados = _CENAS[id_cena]["combate"]
    id_inimigo = dados["inimigo"]

    codigo, vencedor = combate.orquestrar_combate(id_inimigo, obter_acao)
    if codigo != combate.SUCESSO:
        return ERRO_ABORT, None

    if vencedor == "jogador":
        codigo, recompensa = combate.dropar_itens(id_inimigo)
        if codigo != combate.SUCESSO:
            return ERRO_ABORT, None

        for id_item, quantidade in recompensa["itens"].items():
            codigo, _ = itens.adicionar_ao_inventario(id_item, quantidade)
            if codigo != itens.SUCESSO:
                return ERRO_ABORT, None

        codigo, _ = itens.adicionar_ouro(recompensa["ouro"])
        if codigo != itens.SUCESSO:
            return ERRO_ABORT, None

        codigo, _ = personagem.subir_xp(recompensa["xp"])
        if codigo != personagem.SUCESSO:
            return ERRO_ABORT, None

        return SUCESSO, {"vitoria": True, "proxima_cena": dados["vitoria"]}

    if vencedor == "inimigo":
        codigo, _ = personagem.matar_personagem()
        if codigo != personagem.SUCESSO:
            return ERRO_ABORT, None
        return SUCESSO, {"vitoria": False, "proxima_cena": dados["derrota"]}

    return ERRO_ABORT, None