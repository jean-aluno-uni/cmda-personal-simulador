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

Os cenários contam uma viagem, da partida a frio até a chegada em casa, passando pelos melhores e piores casos de cada tela. Cada cenário dura 25 segundos por padrão. Nos primeiros 60% do tempo os valores mudam aos poucos a partir do cenário anterior, então a temperatura sobe ou desce gradualmente e a velocidade acelera ou freia, e os códigos de falha só aparecem quando o problema já se instalou.

O RPM é calculado a partir da velocidade e da marcha, como num carro de cinco marchas, então ele sempre combina com a velocidade. Abaixo de 5 km/h o carro está parado em marcha lenta, por isso aparece RPM com velocidade zero.

O terminal mostra o cenário ativo e a tela do app que ele demonstra.

| # | Cenário | Tela demonstrada | O que acontece |
|---|---|---|---|
| 1 | Partida a frio | Painel inicial, melhor caso | motor ligado parado, marcha lenta em 1050 RPM, motor aquecendo de 26 °C para 55 °C |
| 2 | Saindo de casa | Condições do motor, aquecimento | até 35 km/h, motor chega em 88 °C |
| 3 | Cidade com temperatura ideal | Condições do motor, melhor caso | anda e para entre 30 e 60 km/h, líquido 91 °C e óleo 98 °C |
| 4 | Parado no semáforo | RPM, melhor caso | freia até parar, marcha lenta em 800 RPM |
| 5 | Rodovia em velocidade de cruzeiro | Velocidade e RPM, melhor caso | 100 km/h em quinta marcha, cerca de 2600 RPM |
| 6 | Ultrapassagem com marcha reduzida | Velocidade e RPM, pior caso | 135 km/h em quarta, cerca de 4300 RPM |
| 7 | Congestionamento com a ventoinha falhando | Condições do motor, pior caso | quase parado, líquido 117 °C, óleo 132 °C, ar 52 °C, P0217 |
| 8 | Parado no acostamento | Condições do motor, recuperação | marcha lenta enquanto o motor esfria |
| 9 | Alternador falhando | Bateria, pior caso | tensão cai até 11,4 V, P0562 |
| 10 | Regulador de tensão com defeito | Bateria, pior caso de sobrecarga | tensão sobe até 15,7 V, P0563 |
| 11 | Falha de ignição e câmbio patinando | Diagnóstico e alertas, pior caso | RPM alto demais para 40 km/h, P0301 e P0700 |
| 12 | Conexão instável | Conexão, pior caso | 30% de `NO DATA` e respostas atrasadas |
| 13 | Adaptador desconectado | Conexão, queda | porta fechada por 10 segundos, o app mostra o veículo desconectado e reconecta sozinho |
| 14 | Chegando em casa | Diagnóstico e alertas, melhor caso | tudo normalizado e sem códigos de falha |

## Preparar o Bluetooth no Windows

1. Parear o celular com o notebook nas configurações de Bluetooth.
2. Abrir Configurações, Bluetooth e dispositivos, Dispositivos, Mais configurações de Bluetooth.
3. Na aba Portas COM, clicar em Adicionar, escolher Entrada e confirmar.
4. Anotar o número da porta criada, por exemplo COM4.

Deixe só uma porta de Entrada na lista. Se houver mais de uma, o celular pode se conectar numa porta em que o simulador não está escutando.

No celular, renomeie o notebook pareado para `OBDII`, em Configurações, Bluetooth, engrenagem ao lado do notebook, Renomear. O app mostra esse nome, igual ao de um adaptador ELM327 real.

## Rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python simulador.py --porta COM4
```

Quando o app conecta, o terminal mostra `aplicativo conectado na COM4, recebendo comandos`.

Opções

- `--tempo 15` muda quantos segundos cada cenário dura.
- `--api http://127.0.0.1:8000/api/v1` liga o modo reserva, que não usa Bluetooth e manda as leituras direto para a API com o usuário `demo@cmda.app`. Serve para a apresentação continuar se o Bluetooth falhar.
