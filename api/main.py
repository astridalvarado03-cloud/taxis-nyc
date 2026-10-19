from pathlib import Path
from datetime import date
import json

import numpy as np
import pandas as pd
import xgboost as xgb

from fastapi import FastAPI, HTTPException, Query


# ------------------------------------------------------------
# 1. CONFIGURACIÓN Y ARCHIVOS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
RUTA_MODELO = BASE_DIR / "modelo_pronostico.ubj"
RUTA_CONFIG = BASE_DIR / "configuracion_modelo.json"
RUTA_DATOS = BASE_DIR / "demanda.parquet"

RUTA_ZONAS = (
    BASE_DIR / "zonas_pronostico.csv"
)

app = FastAPI(
    title="Taxis NYC — API de Pronósticos",
    description=(
        "Pronósticos probabilísticos de demanda horaria "
        "de taxis por zona de Nueva York."
    ),
    version="1.1.0"
)


# ------------------------------------------------------------
# 2. CARGA DEL MODELO Y DATOS
# ------------------------------------------------------------

with open(
    RUTA_CONFIG,
    "r",
    encoding="utf-8"
) as archivo:
    configuracion = json.load(archivo)

variables = configuracion["variables"]
cuantiles = configuracion["cuantiles"]
categorias_zona = configuracion["categorias_zona"]

modelo = xgb.XGBRegressor()
modelo.load_model(str(RUTA_MODELO))

datos = pd.read_parquet(RUTA_DATOS)
datos["hora"] = pd.to_datetime(datos["hora"])

datos["PULocationID"] = pd.Categorical(
    datos["PULocationID"],
    categories=categorias_zona
)

zonas = pd.read_csv(RUTA_ZONAS)

catalogo_zonas = {
    int(fila["LocationID"]): {
        "zona_id": int(fila["LocationID"]),
        "nombre": str(fila["Zone"]),
        "borough": str(fila["Borough"])
    }
    for _, fila in zonas.iterrows()
}

columnas_cuantiles = [
    f"p{q}" for q in range(10, 100, 10)
]


# ------------------------------------------------------------
# 3. ENDPOINT DE INICIO
# ------------------------------------------------------------

@app.get("/")
def inicio():
    return {
        "mensaje": "API Taxis NYC funcionando",
        "version": "1.1.0",
        "endpoints": [
            "/",
            "/info",
            "/pronostico",
            "/docs"
        ]
    }


# ------------------------------------------------------------
# 4. ENDPOINT DE INFORMACIÓN
# ------------------------------------------------------------

@app.get("/info")
def informacion():

    fechas = sorted(
        datos["hora"].dt.strftime("%Y-%m-%d").unique()
    )

    return {
        "modelo": "XGBoost probabilístico",
        "cuantiles": cuantiles,
        "numero_zonas": len(catalogo_zonas),
        "zonas": sorted(
            catalogo_zonas.values(),
            key=lambda z: (
                z["borough"],
                z["nombre"]
            )
        ),
        "fechas_disponibles": fechas,
        "periodos": {
            "prueba": "2024-01-25 a 2024-01-31",
            "futuro": "2024-02-01"
        },
        "registros_disponibles": len(datos),
        "version_xgboost_entrenamiento": (
            configuracion["version_xgboost"]
        ),
        "limitacion": (
            "Solo se admiten fechas y zonas "
            "incluidas en los datos preparados."
        )
    }


# ------------------------------------------------------------
# 5. ENDPOINT DE PRONÓSTICO
# ------------------------------------------------------------

@app.get("/pronostico")
def pronostico(
    zona_id: int = Query(
        ...,
        description="Identificador de zona TLC"
    ),
    fecha: date = Query(
        ...,
        description="Fecha en formato AAAA-MM-DD"
    )
):

    if zona_id not in catalogo_zonas:
        raise HTTPException(
            status_code=404,
            detail="La zona solicitada no está disponible."
        )

    mascara = (
        (datos["PULocationID"] == zona_id)
        & (datos["hora"].dt.date == fecha)
    )

    seleccion = (
        datos.loc[mascara]
        .sort_values("hora")
        .copy()
    )

    if seleccion.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                "No hay datos preparados para "
                "esa zona y fecha."
            )
        )

    # Ejecutar el modelo ya entrenado.
    X = seleccion[variables].copy()

    predicciones = modelo.predict(X)

    # Mantener cuantiles ordenados y no negativos.
    predicciones = np.maximum(
        np.sort(predicciones, axis=1),
        0
    )

    registros = []

    for i, (_, fila) in enumerate(
        seleccion.iterrows()
    ):

        valores = {
            nombre: round(
                float(predicciones[i, j]),
                3
            )
            for j, nombre in enumerate(
                columnas_cuantiles
            )
        }

        # La demanda real solo existe en prueba.
        real = (
            float(fila["viajes"])
            if pd.notna(fila["viajes"])
            else None
        )

        # Referencia: misma hora, 7 días antes.
        semana_anterior = (
            float(fila["lag_168"])
            if pd.notna(fila["lag_168"])
            else None
        )

        registros.append({
            "hora": fila["hora"].isoformat(),
            "cuantiles": valores,
            "real": real,
            "hace_una_semana": semana_anterior
        })

    return {
        "zona_id": zona_id,
        "nombre_zona": catalogo_zonas[zona_id]["nombre"],
        "borough": catalogo_zonas[zona_id]["borough"],
        "fecha": fecha.isoformat(),
        "periodo": str(seleccion["periodo"].iloc[0]),
        "numero_horas": len(registros),
        "pronosticos": registros
    }
