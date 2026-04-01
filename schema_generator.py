import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Configuración de conexión (Ajustar en el .env)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "bmo_dashboard"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

def generate_schema():
    conn = None
    try:
        print(f"Conectando a PostgreSQL en {DB_CONFIG['host']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Tablas Maestras
        print("Creando tablas maestras (plants, turnos)...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS plants (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                country VARCHAR(100),
                timezone VARCHAR(50) DEFAULT 'UTC',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS turnos (
                id SERIAL PRIMARY KEY,
                plant_id INT REFERENCES plants(id) ON DELETE CASCADE,
                name VARCHAR(50) NOT NULL,
                start_time TIME,
                end_time TIME,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Tablas de Tendencias Independientes (Aislamiento de Fallos)
        trend_tables = [
            "trend_mae", "trend_adherence", "trend_adoption", 
            "trend_ces", "trend_csat", "trend_losses"
        ]

        for table in trend_tables:
            print(f"Creando tabla de tendencia: {table}...")
            query = f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id SERIAL PRIMARY KEY,
                    plant_id INT REFERENCES plants(id),
                    turno_id INT REFERENCES turnos(id),
                    month VARCHAR(20) NOT NULL,
                    value FLOAT,
                    target FLOAT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_{table}_lookup ON {table} (plant_id, turno_id, month);
            """
            cur.execute(query)

        # 3. Tablas de Factibilidad y Forecast
        print("Creando tablas de optimizador y forecast...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feasibility_stats (
                id SERIAL PRIMARY KEY,
                plant_id INT REFERENCES plants(id),
                type VARCHAR(20),
                factible INT DEFAULT 0,
                infactible INT DEFAULT 0,
                implementada INT DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS forecast_trends (
                id SERIAL PRIMARY KEY,
                plant_id INT REFERENCES plants(id),
                month VARCHAR(20),
                forecasted FLOAT,
                actual FLOAT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("\n✅ Esquema BMO generado exitosamente con soporte multi-timezone.")
        cur.close()

    except Exception as error:
        print(f"\n❌ Error al generar el esquema: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    generate_schema()
