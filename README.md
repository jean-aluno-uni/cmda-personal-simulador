# CMDA Personal, simulador do veículo

Simulador em Python que faz o notebook se comportar como um carro com adaptador OBD2 ELM327. O aplicativo [cmda-personal-mobile](https://github.com/jean-aluno-uni/cmda-personal-mobile) se conecta nele por Bluetooth, envia os mesmos comandos que mandaria para um ELM327 real e recebe as respostas no mesmo formato. Assim dá para demonstrar o fluxo completo do sistema sem levar um carro para a sala.

O simulador percorre em ciclo cenários de melhor e pior caso de cada tela do aplicativo e só para com Ctrl+C.

## Como funciona

```
notebook                                          celular
simulador.py  <- Bluetooth SPP, comandos OBD2 ->  aplicativo CMDA Personal
backend FastAPI + MySQL  <- HTTP JSON + JWT  --   aplicativo CMDA Personal
```

O app pede os valores ao simulador, monta cada leitura e envia para a API do [cmda-personal-backend](https://github.com/jean-aluno-uni/cmda-personal-backend). As telas mostram o que está gravado na API.

## Comandos atendidos

| Comando | O que devolve |
|---|---|
| `ATZ`, `ATI` | versão `ELM327 v1.5` |
| `ATE0`, `ATS0` e demais `AT` | `OK` |
| `ATRV` | tensão da bateria |
| `010C` | RPM |
| `010D` | velocidade em km/h |
| `0105` | temperatura do líquido de arrefecimento |
| `015C` | temperatura do óleo |
| `010F` | temperatura do ar de admissão |
| `0142` | tensão do módulo de controle |
| `03` | códigos de falha DTC |

Qualquer outro PID responde `NO DATA`, como um adaptador real.

## Cenários

Cada cenário fica ativo por 20 segundos por padrão, com pequena variação nos valores. O terminal mostra qual cenário está ativo.

| # | Cenário | Valores principais |
|---|---|---|
| 1 | Painel inicial, melhor caso | marcha lenta, temperaturas e bateria normais, sem DTC |
| 2 | Condições do motor, melhor caso | 2000 RPM, 60 km/h, líquido 90 °C, óleo 95 °C |
| 3 | Condições do motor, pior caso | líquido 118 °C, óleo 135 °C, ar 55 °C, DTC P0217 |
| 4 | RPM, melhor caso | 800 RPM estável |
| 5 | RPM, pior caso | cerca de 6600 RPM oscilando |
| 6 | Bateria, pior caso | 11,4 V, DTC P0562 |
| 7 | Bateria, pior caso de sobrecarga | 15,6 V, DTC P0563 |
| 8 | Velocidade, pior caso | 180 km/h |
| 9 | Diagnóstico e alertas, pior caso | P0217, P0301, P0562 e P0700 ao mesmo tempo |
| 10 | Conexão, pior caso instável | 30% de `NO DATA` e respostas atrasadas |
| 11 | Conexão, pior caso de queda | porta fechada, o app mostra o veículo desconectado |
| 12 | Diagnóstico e alertas, melhor caso | reconectado e tudo normalizado |

## Preparar o Bluetooth no Windows

1. Parear o celular com o notebook nas configurações de Bluetooth.
2. Abrir Configurações, Bluetooth e dispositivos, Dispositivos, Mais configurações de Bluetooth.
3. Na aba Portas COM, clicar em Adicionar, escolher Entrada e confirmar.
4. Anotar o número da porta criada, por exemplo COM5.

## Rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python simulador.py --porta COM5
```

Opções

- `--tempo 10` muda quantos segundos cada cenário dura.
- `--api http://127.0.0.1:8000/api/v1` liga o modo reserva, que não usa Bluetooth e manda as leituras direto para a API com o usuário `demo@cmda.app`. Serve para a apresentação continuar se o Bluetooth falhar.
