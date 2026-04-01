import psycopg2
import os
import random
from dotenv import load_dotenv

# Cargar configuración (soporta .env localmente y variables de entorno en Railway)
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "bmo_dashboard"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

def init_database():
    conn = None
    try:
        print(f"🚀 Iniciando conexión a PostgreSQL en {DB_CONFIG['host']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # --- 1. CREACIÓN DEL ESQUEMA ---
        print("🛠️ Creando tablas si no existen...")
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

        trend_tables = [
            "trend_mae", "trend_adherence", "trend_adoption", 
            "trend_ces", "trend_csat", "trend_losses"
        ]

        for table in trend_tables:
            cur.execute(f"""
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
            """)

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
        
        # --- 2. SIEMBRA DE DATOS (Solo si no hay datos) ---
        cur.execute("SELECT COUNT(*) FROM plants")
        if cur.fetchone()[0] == 0:
            print("🌱 Sembrando datos iniciales...")
            
            # Plantas
            plants_data = [
                ('Santa Fé', 'Chile', 'America/Santiago'),
                ('Guaiba 1', 'Brasil', 'America/Sao_Paulo'),
                ('Laja', 'Chile', 'America/Santiago')
            ]
            plant_ids = []
            for name, country, tz in plants_data:
                cur.execute(
                    "INSERT INTO plants (name, country, timezone) VALUES (%s, %s, %s) RETURNING id",
                    (name, country, tz)
                )
                plant_ids.append(cur.fetchone()[0])

            # Turnos
            turnos_data = [('Turno AM', '06:00:00', '14:00:00'), ('Turno PM', '14:00:00', '22:00:00')]
            turno_ids_map = {}
            for pid in plant_ids:
                turno_ids_map[pid] = []
                for name, start, end in turnos_data:
                    cur.execute(
                        "INSERT INTO turnos (plant_id, name, start_time, end_time) VALUES (%s, %s, %s, %s) RETURNING id",
                        (pid, name, start, end)
                    )
                    turno_ids_map[pid].append(cur.fetchone()[0])

            # Tendencias
            months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            for table in trend_tables:
                for pid in plant_ids:
                    for tid in turno_ids_map[pid]:
                        for m in months:
                            val = random.uniform(60.0, 95.0) if random.random() > 0.1 else None
                            cur.execute(
                                f"INSERT INTO {table} (plant_id, turno_id, month, value, target) VALUES (%s, %s, %s, %s, %s)",
                                (pid, tid, m, val, 85.0)
                            )
            print("✅ Datos de prueba inyectados.")
        else:
            print("ℹ️ La base de datos ya contiene datos. Saltando siembra.")

        conn.commit()
        print("\n✨ Proceso de inicialización completado con éxito.")
        cur.close()

    except Exception as error:
        print(f"❌ Error al inicializar la base de datos: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    init_database()
