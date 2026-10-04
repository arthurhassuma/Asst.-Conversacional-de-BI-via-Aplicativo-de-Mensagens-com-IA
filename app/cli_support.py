"""Erros de argumentos também seguem o idioma do produto."""

from argparse import ArgumentParser


class PortugueseArgumentParser(ArgumentParser):
    def error(self, message):
        self.exit(2, "Argumentos inválidos. Use --help para consultar as opções.\n")
