# %%
import polars as pl
import matplotlib.pyplot as plt
import pathlib


# %%
ruta = pathlib.Path().parent.resolve()
data = f"{ruta}/data/sapal_salarios_clean.csv"


salarios_sapal =(
    pl.scan_csv(data)
)

df_filtrado = (
    salarios_sapal
    .select([
        pl.col("denominacion_del_cargo").alias("cargo"),
        pl.col("monto_mensual_bruto_de_la_remuneracion_en_tabulador").alias("salario_bruto_mensual")
    ])

)



df_cargos_unicos = (
    df_filtrado
    .select(
        pl.col("cargo")
    )
    .unique()
    .sort("cargo")
    .collect()
    .get_column("cargo")
    .to_list()
)


df_filtrado.collect()


# %%


lf = (
    pl.scan_csv("data/sapal_salarios_clean.csv")
    .select([
        pl.col("denominacion_del_cargo").alias("cargo"),
        pl.col("monto_mensual_bruto_de_la_remuneracion_en_tabulador")
          .alias("salario_bruto_mensual"),
    ])
    .filter(
        pl.col("cargo").is_not_null() & (pl.col("cargo") != "")
    )
    .filter(
        pl.col("salario_bruto_mensual").is_not_null()
    )
)

lf_resumen_cargos = (
    lf
    .group_by("cargo")
    .agg([
        pl.len().alias("num_personas_en_cargo"),
        pl.col("salario_bruto_mensual").mean().alias("salario_bruto_promedio"),
        pl.col("salario_bruto_mensual").max().alias("salario_bruto_max"),
        pl.col("salario_bruto_mensual").sum().alias("costo_bruto_total_mensual_cargo"),
    ])
    .sort("salario_bruto_promedio", descending=True)
)

# ahora sí ejecutamos:
df_resumen_cargos = lf_resumen_cargos.collect()
df_resumen_cargos

# %%
print(f"Total de trabajadores: {df_resumen_cargos['num_personas_en_cargo'].sum()}")

# %%


lista_cargos_importantes = [
    'DIRECTOR GENERAL',
    'JEFE DE SISTEMAS COMPUTACIONALES',
    'GERENTE COMERCIAL',
    'GERENTE DE CALIDAD DEL AGUA Y FISCALIZACION',
    'GERENTE DE SUPERVISION DE OBRA',
    'JEFE DE PROYECTOS',
    'GERENTE DE FINANZAS',
    'GERENTE DE PROYECTOS Y COSTOS',
    'SUBDIRECTORA DE PLANEACION',
    'ADMINISTRADOR DE REDES Y COMUNICACIONES',
    'GERENTE DE AGUA POTABLE Y ALCANTARILLADO',
    'PROGRAMADORA ANALISTA "A"',
    'PROGRAMADOR ANALISTA"B"',
    'PROGRAMADOR ANALISTA',
    'PROGRAMADORA ANALISTA',
    'JEFE DE TECNOLOGIAS DE LA OPERACION',
    'SUBDIRECTOR GENERAL OPERATIVO',
    'JEFE DE PLANEACION HIDRICA',
    'JEFE DE COMUNICACION',
    'JEFE DE COSTOS Y EVALUACION',
    'GERENTE DE TECNOLOGIAS DE LA INFORMACION Y COMUNICACION',
    'GERENTE SERVICIOS ADMINISTRATIVOS'
]


cargo_encontrados = []

for cargo in df_cargos_unicos:
    if cargo  in lista_cargos_importantes:
        cargo_encontrados.append(cargo)
if len(cargo_encontrados) == len(lista_cargos_importantes):
    print(f"Se encontraron todos los cargos importantes: {len(lista_cargos_importantes)}/{len(cargo_encontrados)}")



# %%
df_trabajadores_de_interes = (
    df_filtrado
    .filter(
        pl.col("cargo").is_in(cargo_encontrados)
    )
    .sort("salario_bruto_mensual", descending=True)
    .collect()
)



# %%
df_trabajadores_de_interes.shape

# %%
for cargo,sueldo in zip(
    df_trabajadores_de_interes["cargo"],
    df_trabajadores_de_interes["salario_bruto_mensual"]
):
    print(f"{cargo:>60}: ${sueldo:,.0f}")


# %%
df = df_trabajadores_de_interes.clone()


df = df.with_columns([
    (pl.col("salario_bruto_mensual") / 4.33).alias("sueldo_semanal"),
    (pl.col("salario_bruto_mensual") / 4.33 / 48).alias("sueldo_hora"),
])






def estimador_costo_decisiones_por_mes(df: pl.DataFrame,horas_dedicadas: int = 72) -> float:
    """
    Arguments:
        df: DataFrame con columna "sueldo_hora"
        horas_dedicadas: Horas totales dedicadas por el equipo en toma de decisiones por mes
    Returns:
        Costo total mensual del tiempo dedicado a toma de decisiones por el equipo 
    """
    sueldo_hora_del_equipo = df["sueldo_hora"].sum()
    costo_tiempo_decision_mes = sueldo_hora_del_equipo * horas_dedicadas # "horas_dedicadas" es a 72 horas/mes
    return costo_tiempo_decision_mes


def estimador_costo_decisiones_por_años(df: pl.DataFrame, horas_dedicadas: int = 72, años: int = 1) -> float:
    """
    Arguments:
        df: DataFrame con columna "sueldo_hora"
        horas_dedicadas: Horas totales dedicadas por el equipo en toma de decisiones por mes
    Returns:
        Costo total anual del tiempo dedicado a toma de decisiones por el equipo
    """
    costo_tiempo_decision_mes = estimador_costo_decisiones_por_mes(df, horas_dedicadas)
    costo_tiempo_decision_anual = costo_tiempo_decision_mes * 12 * años
    return costo_tiempo_decision_anual


HORAS_AL_MES = 72
num_años = 5
costo_mensual = estimador_costo_decisiones_por_mes(df, horas_dedicadas=HORAS_AL_MES)
costo_anual = estimador_costo_decisiones_por_años(df, horas_dedicadas=HORAS_AL_MES, años=num_años)




print(f"{"="*40} Datos de salarios y costos por hora {"="*40}")
#print(df)

print(f"Costo en la toma de decisiones dedicandole {HORAS_AL_MES} horas al mes:")
print(f"- Costo mensual: ${costo_mensual:,.0f}")
print(f'- Costo anualizado con una proyección a "{num_años}" año(s): ${costo_anual:,.0f}')


# %%
# Calcular participación de cada cargo en el costo mensual total
df_prop = df.with_columns(
    ((pl.col("sueldo_hora") * HORAS_AL_MES) / costo_mensual * 100).alias("porcentaje_participacion")
).sort("porcentaje_participacion", descending=True).to_pandas()

plt.figure(figsize=(10, 6))
plt.bar(df_prop["cargo"], df_prop["porcentaje_participacion"], color="#F28E2B")
plt.xticks(rotation=90)
plt.ylabel("Porcentaje del costo mensual total (%)")
plt.title(f"Distribución del costo mensual en la toma de decisiones ({HORAS_AL_MES}h/mes)")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()

# %%
import matplotlib.pyplot as plt
import numpy as np

# calculamos el costo mensual atribuible a cada cargo
# costo_mensual_individual = sueldo_hora * HORAS_AL_MES
df_costo_roles = df.with_columns([
    (pl.col("sueldo_hora") * HORAS_AL_MES).alias("costo_mensual_rol")
]).select([
    "cargo",
    "costo_mensual_rol"
]).sort("costo_mensual_rol", descending=True).to_pandas()

plt.figure(figsize=(10,6))
plt.barh(df_costo_roles["cargo"], df_costo_roles["costo_mensual_rol"])
plt.xlabel("Costo mensual de decisión por rol (MXN)")
plt.title(f"Costo mensual de decisión por rol\n(asumiendo {HORAS_AL_MES} h/mes dedicadas a decidir)")
plt.gca().invert_yaxis()
plt.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()

# %%
import matplotlib.pyplot as plt

# Calculamos el costo mensual por rol (ya en MXN)
df_factor = df.with_columns([
    (pl.col("sueldo_hora") * HORAS_AL_MES).alias("costo_mensual_rol")
]).sort("costo_mensual_rol", descending=True).to_pandas()

# Factor relativo respecto al más alto (Director General)
df_factor["factor_importancia"] = df_factor["costo_mensual_rol"] / df_factor["costo_mensual_rol"].max()

plt.figure(figsize=(10,6))
plt.barh(df_factor["cargo"], df_factor["factor_importancia"], color="#7D6DDF")
plt.xlabel("Factor de importancia relativo")
plt.title("Factor de importancia del rol en la toma de decisiones")
plt.gca().invert_yaxis()
plt.grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()

# %%
import numpy as np
import matplotlib.pyplot as plt

# Base anual (lo que ya calculaste)
costo_anual_base = estimador_costo_decisiones_por_años(df, horas_dedicadas=HORAS_AL_MES, años=1)

# Escenarios a 5 años con diferentes reducciones
anios = np.arange(1, num_años + 1)
escenarios = {
    "Sin cambio (0%)": costo_anual_base * anios,
    "Reducción 25%": costo_anual_base * 0.75 * anios,
    "Reducción 50%": costo_anual_base * 0.50 * anios,
    "Reducción 75%": costo_anual_base * 0.25 * anios,
}

plt.figure(figsize=(10,6))
for label, valores in escenarios.items():
    plt.plot(anios, valores / 1e6, marker="o", label=label)  # en millones

plt.title("Proyección de costo acumulado a 5 años")
plt.xlabel("Años")
plt.ylabel("Costo acumulado (millones MXN)")
plt.grid(True, linestyle="--", alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()


