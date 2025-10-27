import polars as pd
import matplotlib.pyplot as plt
import pathlib


ruta = pathlib.Path().parent.resolve()
data = f"{ruta}/data/sapal_salarios_clean.csv"


salarios_sapal = pd.read_csv(data)

print(salarios_sapal.head())
print(salarios_sapal.columns)
# Tamaño del DataFrame
print(salarios_sapal.shape)
