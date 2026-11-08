"""Vocabulário do negócio compartilhado entre o agente e a geração de dados."""

# Praças atendidas pela revenda: (cidade, UF). A ordem não tem significado.
CITIES = (
    ("Joinville", "SC"),
    ("Blumenau", "SC"),
    ("Jaraguá do Sul", "SC"),
    ("Itajaí", "SC"),
    ("Brusque", "SC"),
    ("Florianópolis", "SC"),
    ("Curitiba", "PR"),
    ("São José dos Pinhais", "PR"),
    ("Porto Alegre", "RS"),
    ("São Paulo", "SP"),
)
CITY_NAMES = tuple(city for city, _ in CITIES)
