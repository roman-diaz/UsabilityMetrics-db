# Esquema de Base de Datos PostgreSQL - Dashboard BMO

Este documento define la estructura de tablas para soportar la arquitectura de "Aislamiento de Fallos" requerida por el Dashboard BMO.

---

## 1. Tablas Maestras (Core)

Estas tablas centralizan los identificadores para asegurar integridad referencial en todo el sistema.

### `plants`
| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Identificador único de la planta |
| `name` | VARCHAR(100) | Nombre de la planta |
| `country` | VARCHAR(100) | País (ej: Chile, Brasil) |
| `timezone` | VARCHAR(50) | Zona horaria (ej: 'America/Santiago', 'America/Sao_Paulo') |
| `created_at` | TIMESTAMPTZ | Fecha de creación del registro en UTC |

### `turnos`
Define los periodos operativos específicos de cada planta (ej: Turno AM, Turno PM).

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Identificador único del turno |
| `plant_id` | INT (FK) | Planta a la que pertenece este turno |
| `name` | VARCHAR(50) | Nombre del turno (ej: 'Vespertino') |
| `start_time` | TIME | Hora de inicio del turno |
| `end_time` | TIME | Hora de fin del turno |
| `created_at` | TIMESTAMPTZ | Fecha de registro en UTC |

---

## 2. Tablas de Tendencias (Independientes)

Siguiendo el principio de **aislamiento de fallos**, cada métrica reside en su propia tabla. Esto permite que equipos distintos operen de forma asíncrona.

Todas estas tablas comparten la misma estructura base para facilitar el mantenimiento.

### `trend_mae`, `trend_adherence`, `trend_adoption`, `trend_ces`, `trend_csat`, `trend_losses`

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Identificador único del punto de datos |
| `plant_id` | INT (FK) | Referencia a la planta |
| `turno_id` | INT (FK) | Referencia al turno |
| `month` | VARCHAR(20) | Nombre del mes (ej: Ene, Feb) |
| `value` | FLOAT (NULL) | Valor alcanzado por la métrica (null = faltante) |
| `target` | FLOAT (NULL) | Valor objetivo del KPI |
| `created_at` | TIMESTAMPTZ | Fecha de registro en UTC |

---

## 3. Tablas de Factibilidad (Optimizador)

### `feasibility_stats`
Alimenta los 3 gráficos circulares de la comparativa.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Identificador único |
| `plant_id` | INT (FK) | Referencia a la planta |
| `type` | VARCHAR(20) | Tipo de dato: 'manual' o 'auto' |
| `factible` | INT | Conteo de casos factibles |
| `infactible` | INT | Conteo de casos no factibles |
| `implementada` | INT | Conteo de casos implementados |
| `created_at` | TIMESTAMPTZ | Fecha de registro en UTC |

---

## 4. Tablas de Forecast

### `forecast_trends`
| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Identificador único |
| `plant_id` | INT (FK) | Referencia a la planta |
| `month` | VARCHAR(20) | Mes del forecast |
| `forecasted` | FLOAT | Valor proyectado |
| `actual` | FLOAT | Valor real alcanzado |

---

## 5. Índices de Rendimiento Sugeridos

Para asegurar respuestas rápidas (<100ms) en el Dashboard:

```sql
-- Índice compuesto para búsquedas de tendencias por planta/turno/mes
CREATE INDEX idx_trend_lookup ON trend_mae (plant_id, turno_id, month);

-- Índice para búsquedas rápidas por nombre en tablas maestras
CREATE INDEX idx_plant_name ON plants (name);
```
