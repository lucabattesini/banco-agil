import pandas as pd

from app.config import CLIENTES_CSV, SCORE_LIMITE_CSV
from db.migrate_csv import migrate

CUSTOMERS = [
    {"cpf": "11111111111", "nome": "Ana Silva", "data_nascimento": "1990-05-12", "score": 750, "limite_credito": 5000.0},
    {"cpf": "22222222222", "nome": "Bruno Costa", "data_nascimento": "1985-11-30", "score": 420, "limite_credito": 1500.0},
    {"cpf": "33333333333", "nome": "Carla Souza", "data_nascimento": "1998-02-20", "score": 900, "limite_credito": 12000.0},
    {"cpf": "44444444444", "nome": "Diego Santos", "data_nascimento": "1975-07-08", "score": 150, "limite_credito": 500.0},
    {"cpf": "55555555555", "nome": "Elisa Martins", "data_nascimento": "2000-09-15", "score": 600, "limite_credito": 3000.0},
]

SCORE_LIMITS = [
    {"score_min": 0, "score_max": 200, "limite_maximo": 500.0},
    {"score_min": 201, "score_max": 400, "limite_maximo": 1500.0},
    {"score_min": 401, "score_max": 600, "limite_maximo": 3000.0},
    {"score_min": 601, "score_max": 800, "limite_maximo": 6000.0},
    {"score_min": 801, "score_max": 1000, "limite_maximo": 12000.0},
]


def seed() -> None:
    migrate()
    pd.DataFrame(CUSTOMERS).to_csv(CLIENTES_CSV, index=False)
    pd.DataFrame(SCORE_LIMITS).to_csv(SCORE_LIMITE_CSV, index=False)


if __name__ == "__main__":
    seed()
