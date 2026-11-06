import argparse
import json
import random
import time
import urllib.error
import urllib.request

from cenarios import CENARIOS, DESCRICAO_DTC, origem_do_dtc, valores_do_cenario
from elm327 import Elm327


class Ciclo:
    def __init__(self, duracao):
        self.duracao = duracao
        self.inicio = time.monotonic()
        self.anterior = None

    def atual(self):
        indice = int((time.monotonic() - self.inicio) // self.duracao) % len(CENARIOS)
        cenario = CENARIOS[indice]
        if indice != self.anterior:
            self.anterior = indice
            print(f"[{time.strftime('%H:%M:%S')}] cenário {indice + 1}/{len(CENARIOS)}  {cenario['nome']}  ({cenario['descricao']})")
        return cenario


def abrir_porta(porta):
    import serial

    while True:
        try:
            return serial.Serial(porta, 38400, timeout=0.1)
        except serial.SerialException as erro:
            print(f"não foi possível abrir {porta}: {erro}. tentando de novo em 3 s")
            time.sleep(3)


def modo_bluetooth(porta, ciclo):
    import serial

    conexao = None
    elm = Elm327()
    buffer = ""
    print(f"simulando um ELM327 na porta {porta}. Ctrl+C para parar")
    while True:
        cenario = ciclo.atual()
        if cenario.get("queda"):
            if conexao is not None:
                conexao.close()
                conexao = None
                print("conexão derrubada de propósito")
            time.sleep(0.2)
            continue
        if conexao is None:
            conexao = abrir_porta(porta)
            elm = Elm327()
            buffer = ""
            print(f"porta {porta} aberta, aguardando o aplicativo")
        try:
            buffer += conexao.read(64).decode("ascii", errors="ignore")
            while "\r" in buffer:
                comando, buffer = buffer.split("\r", 1)
                comando = comando.strip()
                if not comando:
                    continue
                eco = elm.eco
                if not comando.upper().startswith("AT") and random.random() < cenario.get("sem_resposta", 0):
                    resposta = "NO DATA"
                else:
                    resposta = elm.responder(comando, valores_do_cenario(cenario), cenario["dtcs"])
                time.sleep(cenario.get("atraso", 0))
                saida = (comando + "\r" if eco else "") + resposta + "\r\r>"
                conexao.write(saida.encode("ascii"))
        except serial.SerialException as erro:
            print(f"conexão perdida: {erro}")
            conexao.close()
            conexao = None
            time.sleep(1)


def chamar_api(base, caminho, metodo="GET", corpo=None, token=None):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    requisicao = urllib.request.Request(base + caminho, data=dados, method=metodo)
    requisicao.add_header("Content-Type", "application/json")
    if token:
        requisicao.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(requisicao, timeout=5) as resposta:
        texto = resposta.read()
    return json.loads(texto) if texto else None


def leitura_da_api(valores):
    return {
        "velocidadeKmh": valores["velocidade"],
        "rpm": valores["rpm"],
        "tempMotorC": round((valores["liquido"] + valores["oleo"]) / 2, 1),
        "tempOleoC": valores["oleo"],
        "tempArrefecimentoC": valores["liquido"],
        "tempArC": valores["ar"],
        "tensaoBateriaV": valores["tensao"],
    }


def modo_api(base, email, senha, intervalo, ciclo):
    token = chamar_api(base, "/auth/login", "POST", {"email": email, "senha": senha})["accessToken"]
    veiculo_id = chamar_api(base, "/vehicles", token=token)[0]["id"]
    print(f"logado como {email}, enviando leituras do veículo {veiculo_id} direto para {base}. Ctrl+C para parar")
    conectado = False
    dtcs_anteriores = set()
    while True:
        cenario = ciclo.atual()
        try:
            if cenario.get("queda"):
                if conectado:
                    chamar_api(base, f"/vehicles/{veiculo_id}/disconnect", "POST", token=token)
                    conectado = False
                    dtcs_anteriores = set()
                time.sleep(intervalo)
                continue
            if not conectado:
                chamar_api(base, f"/vehicles/{veiculo_id}/connect", "POST", token=token)
                conectado = True
            chamar_api(base, f"/vehicles/{veiculo_id}/readings", "POST", leitura_da_api(valores_do_cenario(cenario)), token)
            for codigo in set(cenario["dtcs"]) - dtcs_anteriores:
                alerta = {
                    "origem": origem_do_dtc(codigo),
                    "titulo": f"Código de falha {codigo}",
                    "descricao": DESCRICAO_DTC.get(codigo, "Código de falha informado pelo veículo"),
                    "nivel": "high",
                }
                chamar_api(base, f"/vehicles/{veiculo_id}/alerts", "POST", alerta, token)
            dtcs_anteriores = set(cenario["dtcs"])
        except urllib.error.URLError as erro:
            print(f"falha ao falar com a API: {erro}")
        time.sleep(intervalo)


def main():
    parser = argparse.ArgumentParser(description="Simulador do veículo do CMDA Personal")
    parser.add_argument("--porta", default="COM5", help="porta COM de entrada do Bluetooth")
    parser.add_argument("--tempo", type=float, default=20, help="segundos em cada cenário")
    parser.add_argument("--api", help="endereço da API para o modo reserva, ex http://127.0.0.1:8000/api/v1")
    parser.add_argument("--email", default="demo@cmda.app")
    parser.add_argument("--senha", default="Demo@1234")
    parser.add_argument("--intervalo", type=float, default=2, help="segundos entre leituras no modo API")
    args = parser.parse_args()

    ciclo = Ciclo(args.tempo)
    try:
        if args.api:
            modo_api(args.api.rstrip("/"), args.email, args.senha, args.intervalo, ciclo)
        else:
            modo_bluetooth(args.porta, ciclo)
    except KeyboardInterrupt:
        print("\nsimulador encerrado")


if __name__ == "__main__":
    main()
