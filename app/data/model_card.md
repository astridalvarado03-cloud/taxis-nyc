# Model Card — Taxis NYC

## 1. Propósito

Sistema de apoyo a decisiones para pronosticar demanda
horaria de taxis por zona, segmentar zonas y comparar
políticas simuladas de despacho.

## 2. Datos

- Fuente: NYC Taxi & Limousine Commission (TLC).
- Período: enero de 2024.
- Entrenamiento: hasta el 24 de enero de 2024.
- Prueba: del 25 al 31 de enero de 2024.
- Pronóstico futuro: 1 de febrero de 2024.
- Zonas del pronóstico: 59.

## 3. Modelos

### Pronóstico
- Algoritmo: XGBoost.
- Enfoque: regresión cuantílica.
- Cuantiles: p10, p20, p30, p40, p50,
  p60, p70, p80 y p90.
- Variables: rezagos históricos, media móvil
  del día anterior, calendario y zona.

### Segmentación
- Algoritmo: KMeans.
- Número de grupos: 6.
- Zonas segmentadas: 100.
- Silhouette score: 0.4507.

## 4. Evaluación del pronóstico

- MAE XGBoost p50: 11.88 viajes.
- MAE referencia semanal: 11.76 viajes.
- RMSE XGBoost p50: 22.82 viajes.
- RMSE referencia semanal: 21.71 viajes.
- Cobertura p10-p90: 89.86%.
- Cobertura nominal p10-p90: 80%.
- Amplitud media del intervalo: 48.88 viajes.

El modelo XGBoost no superó a la referencia
semanal en precisión puntual.

## 5. Evaluación de despacho

Supuestos:
- Costo por pasajero no atendido: $40.
- Costo por taxi ocioso: $10.
- Cuantil seleccionado: p80.

Resultados:
- Costo simulado p80: $2,354,830.
- Costo simulado referencia semanal: $3,180,750.
- Reducción de costo simulado: 25.97%.

La reducción de costos corresponde a la
simulación y depende de los supuestos utilizados.

## 6. Limitaciones

- Datos de un solo mes.
- Precisión puntual inferior a la referencia.
- Intervalos con cobertura superior a la nominal.
- Costos operativos ilustrativos.
- No se modela reposicionamiento de vehículos.
- No se considera disponibilidad real de conductores.
- Zona 264 sin ubicación geográfica identificada.
- El sistema no ejecuta despachos reales.

## 7. Uso previsto

Apoyo al análisis de demanda, planificación
operativa y comparación de escenarios.

No debe utilizarse como sistema autónomo
de asignación de vehículos sin validación
y supervisión humana.

## 8. Evaluación por tipo de zona

Las 59 zonas se clasificaron en tres grupos de tamaño
similar según su demanda promedio horaria durante el
entrenamiento (1 al 24 de enero de 2024).

La clasificación no utiliza demanda observada del
período de prueba (25 al 31 de enero de 2024).

### 8.1. Precisión por nivel de demanda

| Grupo | Zonas | MAE XGBoost | MAE semanal | RMSE XGBoost | RMSE semanal |
|---|---:|---:|---:|---:|---:|
| Baja demanda | 20 | 3.90 | 4.40 | 6.22 | 7.01 |
| Media demanda | 19 | 11.49 | 11.35 | 22.20 | 19.87 |
| Alta demanda | 20 | 20.22 | 19.51 | 32.09 | 31.09 |

Las métricas se expresan en viajes por hora.
Un valor menor indica mayor precisión.

XGBoost presenta menor MAE que la referencia
semanal en zonas de baja demanda. En zonas de
media y alta demanda, la referencia semanal
obtiene un MAE ligeramente menor.

Los errores absolutos no deben compararse entre
grupos sin considerar sus diferentes volúmenes
de demanda.

### 8.2. Cobertura probabilística por nivel de demanda

| Grupo | Cobertura p10-p90 | Amplitud media (viajes) |
|---|---:|---:|
| Baja demanda | 92.32% | 23.44 |
| Media demanda | 90.10% | 47.14 |
| Alta demanda | 87.17% | 75.97 |

- Cobertura nominal del intervalo p10-p90: 80%.
- Cobertura empírica global: 89.86%.
- Amplitud media global: 48.88 viajes.

Los tres grupos presentan una cobertura superior
a la nominal. La cobertura disminuye en las
zonas de mayor demanda, mientras que la amplitud
absoluta de los intervalos aumenta.

La cobertura observada en este período no garantiza
el mismo comportamiento en fechas futuras.

## 9. Resultados globales de la simulación de despacho

Evaluación retrospectiva de 59 zonas durante siete
días, con 9,912 registros horarios.

Supuestos ilustrativos:

- Pasajero potencialmente no atendido: $40.
- Taxi-hora ocioso: $10.
- Capacidad redondeada hacia arriba.
- Un taxi atiende como máximo un viaje por hora.

| Estrategia | Costo total simulado |
|---|---:|
| p80 | $2,354,830 |
| p50 | $3,266,940 |
| Semana anterior | $3,180,750 |

La estrategia p80 presentó un costo simulado
25.97% menor que la referencia semanal,
una diferencia de $825,920.

Estos importes no representan pérdidas o ahorros
financieros reales. La simulación no incorpora
tiempos de traslado, reposicionamiento, turnos,
disponibilidad real de vehículos ni restricciones
geográficas completas.

## 10. Consideraciones de uso responsable

- **Desempeño desigual:** los errores y la cobertura
  varían entre zonas de distinta demanda.
- **Riesgo de capacidad insuficiente:** subestimar
  demanda puede producir pasajeros potencialmente
  no atendidos en la simulación.
- **Riesgo de capacidad excesiva:** sobreestimar
  demanda puede incrementar taxis-hora ociosos.
- **Calibración:** la cobertura global supera la
  nominal; conviene revisar los intervalos con
  nuevos períodos de datos.
- **Datos limitados:** la evaluación corresponde a
  enero de 2024 y no garantiza generalización.
- **Supervisión humana:** las recomendaciones son
  apoyo a la decisión, no instrucciones automáticas
  de despacho.

Antes de un uso operativo real se requerirían
validación con datos adicionales, monitoreo continuo,
revisión de costos y evaluación de impactos por zona.
