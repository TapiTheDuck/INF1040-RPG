"""Módulo combate.

Regras de batalha por turnos (estilo d20). Guarda a tabela fixa de inimigos,
rola dados e iniciativa, resolve as ações de cada turno e informa as
recompensas de um inimigo derrotado.

Convenções do projeto:
  - Todas as funções de acesso retornam (codigo_retorno, resultado).
  - O módulo não guarda estado entre combates: o EstadoCombate é criado em
    orquestrar_combate e descartado ao seu término.
  - Dano no jogador é aplicado por personagem.aplicar_dano; o dano no inimigo
    é aplicado apenas na cópia de trabalho.
"""

import copy
import random

import itens
import personagem

__all__ = ["orquestrar_combate", "dropar_itens"]

# Códigos de retorno (mesmos valores em todos os módulos)
SUCESSO = 0
ERRO_ABORT = 1
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4

ACOES_JOGADOR = ("atacar", "usar_item")

# Dado de dano do jogador quando não há arma equipada
_DADO_DESARMADO = 4

# Atributo usado no ataque e no dano de cada classe
_ATRIBUTO_PRINCIPAL = {
    "guerreiro": "forca",
    "mago": "inteligencia",
    "arqueiro": "destreza",
}

# Tabela fixa de inimigos (privada).
#   acoes : {"atacar": lados do dado de dano}
#   drops : {id_item: quantidade}
_INIMIGOS = {
    "slime": {
        "nome": "Slime",
        "pv": 8,
        "ca": 8,
        "bonus_ataque": 2,
        "acoes": {"atacar": 4},
        "ouro": 3,
        "xp": 40,
        "drops": {},
    },
    "goblin": {
        "nome": "Goblin",
        "pv": 7,
        "ca": 12,
        "bonus_ataque": 4,
        "acoes": {"atacar": 6},
        "ouro": 5,
        "xp": 50,
        "drops": {"pocao_vida": 1},
    },
}


def _texto_valido(valor):
    """Função interna: True se valor é uma string não vazia."""
    return isinstance(valor, str) and valor.strip() != ""


def _rolar_dado(lados):
    """Função interna: devolve um valor aleatório entre 1 e lados."""
    return random.randint(1, lados)


def _calcular_modificador(valor):
    """Função interna: modificador de um atributo, (valor - 10) // 2."""
    return (valor - 10) // 2


def _dados_jogador():
    """Função interna: reúne o que o combate precisa do jogador.

    Retorna (SUCESSO, dados) ou (ERRO_ABORT, None) se a consulta ao
    Personagem ou aos Itens falhar. dados tem: nome, mod_destreza,
    mod_ataque, mod_dano, dado_dano e ca.
    """
    codigo, ficha = personagem.consultar_personagem()
    if codigo != personagem.SUCESSO:
        return ERRO_ABORT, None
    codigo, equipamento = itens.consultar_equipamento()
    if codigo != itens.SUCESSO:
        return ERRO_ABORT, None

    atributos = ficha["classe"]["atributos"]
    principal = _calcular_modificador(atributos[_ATRIBUTO_PRINCIPAL[ficha["classe"]["nome"]]])
    mod_destreza = _calcular_modificador(atributos["destreza"])

    arma, armadura = equipamento["arma"], equipamento["armadura"]
    return SUCESSO, {
        "nome": ficha["nome"],
        "mod_destreza": mod_destreza,
        "mod_ataque": principal,
        "mod_dano": max(0, principal),
        "dado_dano": arma["dano"] if arma else _DADO_DESARMADO,
        "ca": 10 + mod_destreza + (armadura["bonus_ca"] if armadura else 0),
    }


def _rolar_iniciativa(estado):
    """Função interna: define quem age primeiro.

    Jogador: d20 + modificador de Destreza. Inimigo: d20 + bônus de ataque.
    Em empate o jogador age primeiro. Grava a ordem em estado["ordem"].

    Retorna (SUCESSO, None) ou (ERRO_ABORT, None).
    """
    codigo, jogador = _dados_jogador()
    if codigo != SUCESSO:
        return ERRO_ABORT, None
    do_jogador = _rolar_dado(20) + jogador["mod_destreza"]
    do_inimigo = _rolar_dado(20) + estado["inimigo"]["bonus_ataque"]
    estado["ordem"] = "aliado" if do_jogador >= do_inimigo else "inimigo"
    return SUCESSO, None


def _executar_turno(estado, acao_jogador, acao_inimigo):
    """Função interna: resolve uma rodada na ordem da iniciativa.

    Cada ataque rola d20 + modificador contra a CA do alvo; se acertar,
    causa dano. Se o jogador usou item, o efeito já foi aplicado pelo
    Principal e o turno apenas é gasto.

    Retorna (SUCESSO, {"relato": dict, "vencedor": None|"jogador"|"inimigo"})
    ou (ERRO_ABORT, None) se uma chamada ao Personagem/Itens falhar.
    """
    codigo, jogador = _dados_jogador()
    if codigo != SUCESSO:
        return ERRO_ABORT, None

    inimigo = estado["inimigo"]
    relato = {"turno": estado["turno"], "mensagens": []}
    mensagens = relato["mensagens"]
    vencedor = None

    ordem = ["aliado", "inimigo"] if estado["ordem"] == "aliado" else ["inimigo", "aliado"]
    for quem in ordem:
        if quem == "aliado":
            if acao_jogador == "usar_item":
                mensagens.append(f"{jogador['nome']} usa um item e gasta o turno.")
            else:
                rolagem = _rolar_dado(20)
                total = rolagem + jogador["mod_ataque"]
                if total >= inimigo["ca"]:
                    dano = max(1, _rolar_dado(jogador["dado_dano"]) + jogador["mod_dano"])
                    inimigo["pv"] = max(0, inimigo["pv"] - dano)
                    mensagens.append(
                        f"{jogador['nome']} ataca (d20={rolagem}, total {total} vs CA "
                        f"{inimigo['ca']}) e acerta: {dano} de dano em {inimigo['nome']}.")
                else:
                    mensagens.append(
                        f"{jogador['nome']} ataca (d20={rolagem}, total {total} vs CA "
                        f"{inimigo['ca']}) e erra.")
            if inimigo["pv"] == 0:
                vencedor = "jogador"
                break
        else:
            if acao_inimigo == "atacar":
                rolagem = _rolar_dado(20)
                total = rolagem + inimigo["bonus_ataque"]
                if total >= jogador["ca"]:
                    dano = _rolar_dado(inimigo["acoes"]["atacar"])
                    codigo, pv = personagem.aplicar_dano(dano)
                    if codigo != personagem.SUCESSO:
                        return ERRO_ABORT, None
                    mensagens.append(
                        f"{inimigo['nome']} ataca (d20={rolagem}, total {total} vs CA "
                        f"{jogador['ca']}) e acerta: {dano} de dano em {jogador['nome']}.")
                    if pv == 0:
                        vencedor = "inimigo"
                        break
                else:
                    mensagens.append(
                        f"{inimigo['nome']} ataca (d20={rolagem}, total {total} vs CA "
                        f"{jogador['ca']}) e erra.")

    return SUCESSO, {"relato": relato, "vencedor": vencedor}


def orquestrar_combate(id_inimigo, obter_acao):
    """Conduz um combate por turnos até o jogador ou o inimigo cair.

    Cria o EstadoCombate com uma cópia do inimigo, rola a iniciativa e, a
    cada turno, chama obter_acao(copia_do_estado) para obter a ação do
    jogador ("atacar" ou "usar_item"; se usar item, o Principal já o aplicou
    por itens.usar_item e o turno é gasto).

    Assertivas de entrada:
        id_inimigo (str): texto não vazio, identificador na tabela de inimigos.
        obter_acao (função): recebe uma cópia do estado e devolve a ação.
        Exige que um personagem vivo já tenha sido criado.

    Retornos:
        (SUCESSO, vencedor)           "jogador" ou "inimigo"
        (ERRO_ABORT, None)            chamada ao Personagem ou aos Itens
                                      falhou, ou obter_acao falhou/devolveu
                                      ação inválida
        (ERRO_DADOS_INVALIDOS, None)  id_inimigo não é texto ou obter_acao
                                      não é função
        (ERRO_ID_INEXISTENTE, None)   não existe inimigo com esse identificador
    """
    if not _texto_valido(id_inimigo) or not callable(obter_acao):
        return ERRO_DADOS_INVALIDOS, None
    if id_inimigo not in _INIMIGOS:
        return ERRO_ID_INEXISTENTE, None

    codigo, ficha = personagem.consultar_personagem()
    if codigo != personagem.SUCESSO or not ficha["vivo"]:
        return ERRO_ABORT, None

    estado = {
        "inimigo": copy.deepcopy(_INIMIGOS[id_inimigo]),
        "ordem": "aliado",
        "turno": 1,
        "relato": {},
    }
    codigo, _ = _rolar_iniciativa(estado)
    if codigo != SUCESSO:
        return ERRO_ABORT, None

    while True:
        try:
            acao = obter_acao(copy.deepcopy(estado))
        except Exception:
            return ERRO_ABORT, None
        if not isinstance(acao, str) or acao not in ACOES_JOGADOR:
            return ERRO_ABORT, None

        codigo, resultado = _executar_turno(estado, acao, "atacar")
        if codigo != SUCESSO:
            return ERRO_ABORT, None

        estado["relato"] = resultado["relato"]
        if resultado["vencedor"] is not None:
            return SUCESSO, resultado["vencedor"]
        estado["turno"] += 1


def dropar_itens(id_inimigo):
    """Informa a recompensa de um inimigo derrotado (apenas consulta).

    A entrega ao jogador é feita pela Narrativa.

    Assertivas de entrada:
        id_inimigo (str): texto não vazio.

    Retornos:
        (SUCESSO, recompensa)         {"itens": {id: qtd}, "ouro": int, "xp": int}
        (ERRO_DADOS_INVALIDOS, None)  id_inimigo não é texto
        (ERRO_ID_INEXISTENTE, None)   não existe inimigo com esse identificador
    """
    if not _texto_valido(id_inimigo):
        return ERRO_DADOS_INVALIDOS, None
    if id_inimigo not in _INIMIGOS:
        return ERRO_ID_INEXISTENTE, None

    ficha = _INIMIGOS[id_inimigo]
    return SUCESSO, {
        "itens": copy.deepcopy(ficha["drops"]),
        "ouro": ficha["ouro"],
        "xp": ficha["xp"],
    }
