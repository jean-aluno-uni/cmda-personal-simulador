import math
import random
import time

MARCHAS = [(12, 110), (25, 62), (40, 42), (65, 32), (999, 26)]

MOTOR_FRIO = {"velocidade": 0, "lenta": 1150, "liquido": 26, "oleo": 25, "ar": 24, "tensao": 14.5}

NORMAL_CIDADE = {"velocidade": 45, "lenta": 800, "liquido": 91, "oleo": 98, "ar": 30, "tensao": 14.2}

DESCRICAO_DTC = {
    "P0217": "Superaquecimento do motor",
    "P0301": "Falha de ignição no cilindro 1",
    "P0562": "Tensão do sistema baixa",
    "P0563": "Tensão do sistema alta",
    "P0700": "Falha no sistema de transmissão",
}

CENARIOS = [
    {
        "nome": "Partida a frio",
        "tela": "Painel inicial, melhor caso",
        "descricao": "motor recém ligado na garagem, marcha lenta mais alta enquanto aquece",
        "de": MOTOR_FRIO,
        "alvo": {"velocidade": 0, "lenta": 1050, "liquido": 55, "oleo": 50, "ar": 25, "tensao": 14.4},
        "dtcs": [],
    },
    {
        "nome": "Saindo de casa",
        "tela": "Condições do motor, aquecimento",
        "descricao": "trânsito leve, o motor chega na temperatura de trabalho",
        "alvo": {"velocidade": 35, "lenta": 850, "liquido": 88, "oleo": 90, "ar": 28, "tensao": 14.3},
        "ondulacao": 10,
        "dtcs": [],
    },
    {
        "nome": "Cidade com temperatura ideal",
        "tela": "Condições do motor, melhor caso",
        "descricao": "anda e para no trânsito com todas as temperaturas na faixa",
        "alvo": NORMAL_CIDADE,
        "ondulacao": 15,
        "dtcs": [],
    },
    {
        "nome": "Parado no semáforo",
        "tela": "RPM, melhor caso",
        "descricao": "carro parado com o motor em marcha lenta, por isso há RPM com velocidade zero",
        "alvo": {**NORMAL_CIDADE, "velocidade": 0},
        "dtcs": [],
    },
    {
        "nome": "Rodovia em velocidade de cruzeiro",
        "tela": "Velocidade e RPM, melhor caso",
        "descricao": "quinta marcha a 100 km/h, giro baixo e estável",
        "alvo": {**NORMAL_CIDADE, "velocidade": 100, "liquido": 92, "oleo": 103, "ar": 32},
        "ondulacao": 3,
        "dtcs": [],
    },
    {
        "nome": "Ultrapassagem com marcha reduzida",
        "tela": "Velocidade e RPM, pior caso",
        "descricao": "reduz a marcha e acelera, giro acima de 3000 RPM e velocidade acima de 120 km/h",
        "alvo": {**NORMAL_CIDADE, "velocidade": 135, "liquido": 97, "oleo": 112, "ar": 34},
        "reduzida": True,
        "dtcs": [],
    },
    {
        "nome": "Congestionamento com a ventoinha falhando",
        "tela": "Condições do motor, pior caso",
        "descricao": "quase parado no trânsito e o motor superaquecendo",
        "alvo": {**NORMAL_CIDADE, "velocidade": 6, "liquido": 117, "oleo": 132, "ar": 52},
        "ondulacao": 6,
        "dtcs": ["P0217"],
    },
    {
        "nome": "Parado no acostamento",
        "tela": "Condições do motor, recuperação",
        "descricao": "motor em marcha lenta esfriando depois do superaquecimento",
        "alvo": {**NORMAL_CIDADE, "velocidade": 0, "liquido": 95, "oleo": 106, "ar": 33},
        "dtcs": [],
    },
    {
        "nome": "Alternador falhando",
        "tela": "Bateria, pior caso",
        "descricao": "a bateria deixa de ser carregada e a tensão cai enquanto o carro roda",
        "alvo": {**NORMAL_CIDADE, "tensao": 11.4},
        "ondulacao": 12,
        "dtcs": ["P0562"],
    },
    {
        "nome": "Regulador de tensão com defeito",
        "tela": "Bateria, pior caso de sobrecarga",
        "descricao": "o alternador manda tensão demais para a bateria",
        "alvo": {**NORMAL_CIDADE, "tensao": 15.7},
        "ondulacao": 12,
        "dtcs": ["P0563"],
    },
    {
        "nome": "Falha de ignição e câmbio patinando",
        "tela": "Diagnóstico e alertas, pior caso",
        "descricao": "motor falhando e giro alto demais para a velocidade, com códigos de motor e transmissão",
        "alvo": {**NORMAL_CIDADE, "velocidade": 40, "liquido": 99, "oleo": 110},
        "ondulacao": 5,
        "patinando": 2.0,
        "tremor": 250,
        "dtcs": ["P0301", "P0700"],
    },
    {
        "nome": "Conexão instável",
        "tela": "Conexão, pior caso",
        "descricao": "adaptador mal encaixado, respostas atrasadas e leituras sem dado",
        "alvo": NORMAL_CIDADE,
        "ondulacao": 12,
        "sem_resposta": 0.3,
        "atraso": 0.8,
        "dtcs": [],
    },
    {
        "nome": "Adaptador desconectado",
        "tela": "Conexão, queda",
        "descricao": "o adaptador sai da tomada OBD2 e o app deve mostrar o veículo desconectado",
        "alvo": NORMAL_CIDADE,
        "queda": True,
        "dtcs": [],
    },
    {
        "nome": "Chegando em casa",
        "tela": "Diagnóstico e alertas, melhor caso",
        "descricao": "adaptador reconectado, tudo normalizado e sem códigos de falha",
        "alvo": {**NORMAL_CIDADE, "velocidade": 25, "liquido": 90, "oleo": 95},
        "ondulacao": 8,
        "dtcs": [],
    },
]


def rpm_da_velocidade(velocidade, reduzida):
    marcha = next(i for i, (limite, _) in enumerate(MARCHAS) if velocidade < limite)
    if reduzida:
        marcha = max(0, marcha - 1)
    return velocidade * MARCHAS[marcha][1]


def valores_do_cenario(indice, decorrido, duracao):
    cenario = CENARIOS[indice]
    de = cenario.get("de") or CENARIOS[indice - 1]["alvo"]
    alvo = cenario["alvo"]
    progresso = min(1, decorrido / (duracao * 0.6))
    base = {chave: de[chave] + (alvo[chave] - de[chave]) * progresso for chave in alvo}

    velocidade = 0
    if base["velocidade"] >= 1:
        onda = cenario.get("ondulacao", 0) * math.sin(time.monotonic() / 3)
        velocidade = max(0, base["velocidade"] + onda + random.uniform(-1, 1))

    if velocidade < 5:
        rpm = base["lenta"]
    else:
        rpm = rpm_da_velocidade(velocidade, cenario.get("reduzida", False)) * cenario.get("patinando", 1)
        rpm = max(base["lenta"], rpm)
    tremor = cenario.get("tremor", 20)
    rpm = max(0, rpm + random.uniform(-tremor, tremor))

    valores = {
        "rpm": int(rpm),
        "velocidade": int(velocidade),
        "liquido": int(round(base["liquido"] + random.uniform(-0.5, 0.5))),
        "oleo": int(round(base["oleo"] + random.uniform(-0.5, 0.5))),
        "ar": int(round(base["ar"] + random.uniform(-0.5, 0.5))),
        "tensao": round(base["tensao"] + random.uniform(-0.05, 0.05), 1),
    }
    dtcs = cenario["dtcs"] if progresso >= 1 else []
    return valores, dtcs


def origem_do_dtc(codigo):
    if codigo.startswith("P07"):
        return "Transmissao"
    if codigo.startswith("P056"):
        return "Bateria"
    return "Motor"
