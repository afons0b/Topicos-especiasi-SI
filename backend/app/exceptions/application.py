class RegraDeNegocioError(Exception):
    def __init__(self, campos: dict[str, str]) -> None:
        super().__init__("Os dados enviados são inválidos.")
        self.campos = campos
