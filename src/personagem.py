"""Módulo personagem.

Guarda e manipula os dados do personagem do jogador. Por enquanto existe
um único personagem por vez, mantido em estado privado do módulo.

Todas as funções de acesso retornam (codigo_retorno, resultado).
"""

import copy

# ---------------------------------------------------------------------------
# Códigos de retorno
# ---------------------------------------------------------------------------
SUCESSO = 0
ERRO_ABORT = 1
ERRO_ID_REPETIDO = 2
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4

# ---------------------------------------------------------------------------
# Dados fixos do módulo
# ---------------------------------------------------------------------------
XP_BASE = 100  # XP para sair do nível N: XP_BASE * N (nível 1 -> 100, nível 2 -> 200...)

# Valores iniciais de cada classe (pv_inicial = dado de vida + mod. de Constituição).
CLASSES = {
    "guerreiro": {
        "pv_inicial": 12,
        "atributos": {"forca": 15, "destreza": 13, "constituicao": 14,
                      "inteligencia": 8, "sabedoria": 10, "carisma": 12},
    },
    "mago": {
        "pv_inicial": 7,
        "atributos": {"forca": 8, "destreza": 14, "constituicao": 12,
                      "inteligencia": 15, "sabedoria": 13, "carisma": 10},
    },
    "arqueiro": {
        "pv_inicial": 9,
        "atributos": {"forca": 10, "destreza": 15, "constituicao": 13,
                      "inteligencia": 8, "sabedoria": 14, "carisma": 12},
    },
}

# ---------------------------------------------------------------------------
# Estado privado do módulo (None = ainda não existe personagem)
# ---------------------------------------------------------------------------
_personagem = None


def criar_personagem(nome, classe):
    """Cria o personagem do jogador, substituindo o anterior (se houver).

    Retornos:
        (SUCESSO, None)               personagem criado
        (ERRO_DADOS_INVALIDOS, None)  nome vazio/não texto ou classe não texto
        (ERRO_ID_INEXISTENTE, None)   classe não existe (guerreiro, mago, arqueiro)
    """
    global _personagem

    if not isinstance(nome, str) or nome.strip() == "":
        return ERRO_DADOS_INVALIDOS, None
    if not isinstance(classe, str):
        return ERRO_DADOS_INVALIDOS, None
    if classe not in CLASSES:
        return ERRO_ID_INEXISTENTE, None

    pv = CLASSES[classe]["pv_inicial"]
    _personagem = {
        "nome": nome.strip(),
        "classe": {
            "nome": classe,
            "atributos": copy.deepcopy(CLASSES[classe]["atributos"]),
        },
        "nivel": 1,
        "xp": 0,
        "xp_max": XP_BASE,
        "pv_max": pv,
        "pv": pv,
        "inventario": {},
    }
    return SUCESSO, None


def consultar_personagem():
    """Retorna uma cópia dos dados atuais do personagem.

    Retornos:
        (SUCESSO, personagem)         cópia do personagem
        (ERRO_ID_INEXISTENTE, None)   ainda não existe personagem criado
    """
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None
    return SUCESSO, copy.deepcopy(_personagem)


def passar_nivel():
    """Sobe o personagem um nível, aplicando os ganhos da sua classe.

    Zera o XP do nível e recalcula o XP necessário para o próximo.

    Retornos:
        (SUCESSO, novo_nivel)         nível aumentado
        (ERRO_DADOS_INVALIDOS, None)  classe do personagem não é reconhecida
        (ERRO_ID_INEXISTENTE, None)   ainda não existe personagem criado
    """
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None

    classe = _personagem["classe"]["nome"]
    atributos = _personagem["classe"]["atributos"]

    if classe == "guerreiro":
        # TODO: trocar por ganhos específicos, ex.: atributos["forca"] += 2
        for nome_atributo in atributos:
            atributos[nome_atributo] += 1
        ganho_pv = 1
    elif classe == "mago":
        for nome_atributo in atributos:
            atributos[nome_atributo] += 1
        ganho_pv = 1
    elif classe == "arqueiro":
        for nome_atributo in atributos:
            atributos[nome_atributo] += 1
        ganho_pv = 1
    else:
        return ERRO_DADOS_INVALIDOS, None

    _personagem["nivel"] += 1
    _personagem["pv_max"] += ganho_pv
    _personagem["pv"] += ganho_pv
    _personagem["xp"] = 0
    _personagem["xp_max"] = XP_BASE * _personagem["nivel"]
    return SUCESSO, _personagem["nivel"]


def subir_xp(xp):
    """Adiciona XP ao personagem, subindo de nível quantas vezes for preciso.

    Se o XP atingir o máximo do nível, chama passar_nivel e chama a si mesma
    com o XP que sobrou.

    Retornos:
        (SUCESSO, niveis_ganhos)      XP adicionado; niveis_ganhos pode ser 0
        (ERRO_ABORT, None)            passar_nivel (ou a chamada recursiva) falhou
        (ERRO_DADOS_INVALIDOS, None)  xp não é inteiro ou é menor ou igual a zero
        (ERRO_ID_INEXISTENTE, None)   ainda não existe personagem criado
    """
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None
    if not isinstance(xp, int) or isinstance(xp, bool) or xp <= 0:
        return ERRO_DADOS_INVALIDOS, None

    total = _personagem["xp"] + xp

    # Não chegou ao máximo do nível: só acumula.
    if total < _personagem["xp_max"]:
        _personagem["xp"] = total
        return SUCESSO, 0

    # Chegou ao máximo: sobe de nível e reaplica o que sobrou.
    sobra = total - _personagem["xp_max"]
    codigo, _ = passar_nivel()
    if codigo != SUCESSO:
        return ERRO_ABORT, None

    niveis_ganhos = 1
    if sobra > 0:
        codigo, niveis_extras = subir_xp(sobra)
        if codigo != SUCESSO:
            return ERRO_ABORT, None
        niveis_ganhos += niveis_extras

    return SUCESSO, niveis_ganhos


def matar_personagem():
    """Zera os pontos de vida do personagem (usado quando ele perde um combate).

    Retornos:
        (SUCESSO, None)               pontos de vida zerados
        (ERRO_ID_INEXISTENTE, None)   ainda não existe personagem criado
    """
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None
    _personagem["pv"] = 0
    return SUCESSO, None