import random

NORMAL = {"rpm": 850, "velocidade": 0, "liquido": 90, "oleo": 95, "ar": 25, "tensao": 14.2}

VARIACAO = {"rpm": 40, "velocidade": 2, "liquido": 1, "oleo": 1, "ar": 1, "tensao": 0.1}

DESCRICAO_DTC = {
    "P0217": "Superaquecimento do motor",
    "P0301": "Falha de ignição no cilindro 1",
    "P0562": "Tensão do sistema baixa",
    "P0563": "Tensão do sistema alta",
    "P0700": "Falha no sistema de transmissão",
}

CENARIOS = [
    {
        "nome": "Painel inicial, melhor caso",
        "descricao": "conectado, tudo dentro da faixa e sem códigos de falha",
        "valores": NORMAL,
        "dtcs": [],
    },
    {
        "nome": "Condições do motor, melhor caso",
        "descricao": "rodando na cidade com temperaturas ideais",
        "valores": {**NORMAL, "rpm": 2000, "velocidade": 60},
        "dtcs": [],
    },
    {
        "nome": "Condições do motor, pior caso",
        "descricao": "superaquecimento do líquido e do óleo",
        "valores": {**NORMAL, "rpm": 2500, "velocidade": 60, "liquido": 118, "oleo": 135, "ar": 55},
        "dtcs": ["P0217"],
    },
    {
        "nome": "RPM, melhor caso",
        "descricao": "marcha lenta estável",
        "valores": {**NORMAL, "rpm": 800},
        "variacao": {"rpm": 15},
        "dtcs": [],
    },
    {
        "nome": "RPM, pior caso",
        "descricao": "rotação acima da faixa vermelha e oscilando",
        "valores": {**NORMAL, "rpm": 6600, "velocidade": 120, "liquido": 102, "oleo": 112},
        "variacao": {"rpm": 300},
        "dtcs": [],
    },
    {
        "nome": "Bateria, pior caso",
        "descricao": "bateria fraca e alternador sem carregar",
        "valores": {**NORMAL, "tensao": 11.4},
        "dtcs": ["P0562"],
    },
    {
        "nome": "Bateria, pior caso de sobrecarga",
        "descricao": "regulador de tensão com defeito",
        "valores": {**NORMAL, "tensao": 15.6},
        "dtcs": ["P0563"],
    },
    {
        "nome": "Velocidade, pior caso",
        "descricao": "velocidade muito alta em rodovia",
        "valores": {**NORMAL, "rpm": 4500, "velocidade": 180, "liquido": 100, "oleo": 110},
        "dtcs": [],
    },
    {
        "nome": "Diagnóstico e alertas, pior caso",
        "descricao": "vários códigos de falha de motor, transmissão e bateria",
        "valores": {**NORMAL, "rpm": 3200, "velocidade": 70, "liquido": 112, "oleo": 128, "tensao": 11.6},
        "dtcs": ["P0217", "P0301", "P0562", "P0700"],
    },
    {
        "nome": "Conexão, pior caso instável",
        "descricao": "respostas atrasadas e leituras sem dado",
        "valores": NORMAL,
        "dtcs": [],
        "sem_resposta": 0.3,
        "atraso": 0.8,
    },
    {
        "nome": "Conexão, pior caso de queda",
        "descricao": "adaptador desligado, o app deve mostrar o veículo desconectado",
        "valores": NORMAL,
        "dtcs": [],
        "queda": True,
    },
    {
        "nome": "Diagnóstico e alertas, melhor caso",
        "descricao": "reconectado, valores normalizados e nenhum código de falha",
        "valores": {**NORMAL, "rpm": 1800, "velocidade": 50},
        "dtcs": [],
    },
]


def valores_do_cenario(cenario):
    variacao = {**VARIACAO, **cenario.get("variacao", {})}
    valores = {}
    for chave, base in cenario["valores"].items():
        valor = max(0, base + random.uniform(-variacao[chave], variacao[chave]))
        valores[chave] = round(valor, 1) if chave == "tensao" else int(valor)
    if cenario["valores"]["velocidade"] == 0:
        valores["velocidade"] = 0
    return valores


def origem_do_dtc(codigo):
    if codigo.startswith("P07"):
        return "Transmissao"
    if codigo.startswith("P056"):
        return "Bateria"
    return "Motor"
