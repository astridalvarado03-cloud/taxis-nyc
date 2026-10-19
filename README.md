# 🚕 Taxis NYC: una app para quien toma decisiones

Aplicación interactiva para apoyar la planificación operativa
de taxis en Nueva York mediante pronósticos probabilísticos,
segmentación de zonas y simulación de decisiones de despacho.

## Funcionalidades

La aplicación Streamlit contiene cinco páginas:

1. **Inicio:** presentación del proyecto e indicadores.
2. **Pronóstico de demanda:** estimaciones horarias por zona
   mediante nueve cuantiles (p10 a p90).
3. **Segmentación de zonas:** agrupación de zonas operativas
   mediante KMeans.
4. **Decisiones de despacho:** recomendaciones simuladas
   considerando costos de demanda no atendida y capacidad ociosa.
5. **Ficha del modelo:** resultados, limitaciones y
   consideraciones para el uso responsable.

## Arquitectura

- **Preparación y análisis:** Google Colab / Python.
- **Pronóstico:** XGBoost con cuantiles.
- **Segmentación:** KMeans.
- **API:** FastAPI, publicada en Render.
- **Interfaz:** Streamlit Community Cloud.
- **Comunicación:** Streamlit consulta los pronósticos
  a través de los endpoints de FastAPI.

## Estructura del proyecto

```text
taxis-nyc/
├── preparacion.ipynb
├── README.md
├── render.yaml
├── api/
│   ├── main.py
│   ├── requirements.txt
│   ├── modelo_pronostico.ubj
│   ├── configuracion_modelo.json
│   ├── demanda.parquet
│   └── zonas_pronostico.csv
└── app/
    ├── streamlit_app.py
    ├── requirements.txt
    └── data/
        ├── zonas_pronostico.csv
        ├── segmentos_zonas.csv
        ├── plan_despacho_2024-02-01.csv
        ├── model_card.md
        ├── evaluacion_global_despacho.csv
        ├── evaluacion_diaria_despacho.csv
        ├── evaluacion_por_tipo_zona.csv
        └── evaluacion_cobertura_zonas.csv
```

## Resultados principales

### Pronóstico

- 59 zonas pronosticadas.
- Pronósticos horarios para el 25 al 31 de enero de 2024.
- Pronóstico futuro para el 1 de febrero de 2024.
- MAE global de XGBoost (p50): **11.88**.
- Cobertura empírica del intervalo p10-p90: **89.86 %**.

### Segmentación

- 100 zonas analizadas.
- 6 segmentos operativos mediante KMeans.
- Silhouette score: **0.4507**.

### Simulación de despacho

Bajo el escenario de costos de referencia:

- Costo por demanda no atendida: **USD 40**.
- Costo por taxi-hora ocioso: **USD 10**.
- Estrategia basada en p80: **USD 2,354,830**.
- Estrategia basada en la semana anterior:
  **USD 3,180,750**.
- Diferencia de costo simulado: **-25.97 %**.

Estos valores corresponden a una simulación retrospectiva,
no a ahorros reales observados.

## Ejecución local

### FastAPI

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

Documentación interactiva:

`http://127.0.0.1:8000/docs`

### Streamlit

Desde la carpeta principal del proyecto:

```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```

En producción, configurar `API_URL` con la dirección
pública de FastAPI en Render.

## Endpoints

- `GET /info`: zonas, fechas y cuantiles disponibles.
- `GET /pronostico?zona_id=4&fecha=2024-01-25`:
  pronósticos horarios y datos de comparación.

## Limitaciones

- Los resultados no representan decisiones reales de despacho.
- El desempeño varía según la zona y su nivel de demanda.
- La disponibilidad de vehículos y las restricciones
  geográficas no se modelan completamente.
- Los resultados corresponden al período analizado.

Para más información, consultar `app/data/model_card.md`.

## Enlaces de publicación

- **Aplicación Streamlit:** pendiente de publicación.
- **API FastAPI:** pendiente de publicación.
- **Repositorio GitHub:** pendiente de publicación.

## Equipo

Agregar aquí los nombres de los integrantes del equipo.
