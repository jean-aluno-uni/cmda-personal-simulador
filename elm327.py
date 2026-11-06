VERSAO = "ELM327 v1.5"


def dois_bytes(valor):
    valor = int(valor)
    return f"{valor >> 8 & 255:02X} {valor & 255:02X}"


def um_byte(valor):
    return f"{int(valor) & 255:02X}"


class Elm327:
    def __init__(self):
        self.eco = True
        self.espacos = True

    def responder(self, comando, valores, dtcs):
        comando = comando.strip().upper().replace(" ", "")
        if comando.startswith("AT"):
            return self.comando_at(comando, valores)
        resposta = self.comando_obd(comando, valores, dtcs)
        if resposta == "NO DATA" or self.espacos:
            return resposta
        return resposta.replace(" ", "")

    def comando_at(self, comando, valores):
        if comando in ("ATZ", "ATI", "ATWS"):
            self.eco = True
            self.espacos = True
            return VERSAO
        if comando in ("ATE0", "ATE1"):
            self.eco = comando == "ATE1"
        if comando in ("ATS0", "ATS1"):
            self.espacos = comando == "ATS1"
        if comando == "ATRV":
            return f"{valores['tensao']:.1f}V"
        return "OK"

    def comando_obd(self, comando, valores, dtcs):
        if comando == "0100":
            return "41 00 BE 1F B8 13"
        if comando == "010C":
            return "41 0C " + dois_bytes(valores["rpm"] * 4)
        if comando == "010D":
            return "41 0D " + um_byte(valores["velocidade"])
        if comando == "0105":
            return "41 05 " + um_byte(valores["liquido"] + 40)
        if comando == "010F":
            return "41 0F " + um_byte(valores["ar"] + 40)
        if comando == "015C":
            return "41 5C " + um_byte(valores["oleo"] + 40)
        if comando == "0142":
            return "41 42 " + dois_bytes(valores["tensao"] * 1000)
        if comando == "03":
            return self.codigos_de_falha(dtcs)
        return "NO DATA"

    def codigos_de_falha(self, dtcs):
        bytes_dtc = [codigo[1:3] + " " + codigo[3:5] for codigo in dtcs]
        while len(bytes_dtc) == 0 or len(bytes_dtc) % 3:
            bytes_dtc.append("00 00")
        linhas = ["43 " + " ".join(bytes_dtc[i:i + 3]) for i in range(0, len(bytes_dtc), 3)]
        return "\r".join(linhas)
