import psycopg2
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar configuración desde .env
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "bmo_dashboard"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

def seed_bmo_data():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("🌱 Iniciando siembra de datos BMO...")

        # 1. Insertar Plantas (Chile y Brasil)
        plants = [
            ('Santa Fé', 'Chile', 'America/Santiago'),
            ('Guaiba 1', 'Brasil', 'America/Sao_Paulo'),
            ('Laja', 'Chile', 'America/Santiago')
        ]
        
        plant_ids = []
        for name, country, tz in plants:
            cur.execute(
                "INSERT INTO plants (name, country, timezone) VALUES (%s, %s, %s) RETURNING id",
                (name, country, tz)
            )
            plant_ids.append(cur.fetchone()[0])
        print(f"✅ {len(plants)} plantas creadas.")

        # 2. Insertar Turnos por Planta (AM/PM con horarios)
        turnos_data = [
            ('Turno AM', '06:00:00', '14:00:00'),
            ('Turno PM', '14:00:00', '22:00:00')
        ]

        turno_ids_map = {} # {plant_id: [ids]}
        for pid in plant_ids:
            turno_ids_map[pid] = []
            for name, start, end in turnos_data:
                cur.execute(
                    "INSERT INTO turnos (plant_id, name, start_time, end_time) VALUES (%s, %s, %s, %s) RETURNING id",
                    (pid, name, start, end)
                )
                turno_ids_map[pid].append(cur.fetchone()[0])
        print("✅ Turnos operativos asignados a cada planta.")

        # 3. Generar Tendencias Históricas (12 meses)
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        trend_tables = ["trend_mae", "trend_adherence", "trend_adoption", "trend_ces", "trend_csat", "trend_losses"]
        
        for table in trend_tables:
            print(f"📊 Generando datos para {table}...")
            for pid in plant_ids:
                for tid in turno_ids_map[pid]:
                    for m in months:
                        # Política de Resiliencia: 10% de probabilidad de valor nulo (sin dato)
                        value = random.uniform(60.0, 95.0) if random.random() > 0.1 else None
                        target = 85.0
                        
                        cur.execute(
                            f"INSERT INTO {table} (plant_id, turno_id, month, value, target) VALUES (%s, %s, %s, %s, %s)",
                            (pid, tid, m, value, target)
                        )
        
        conn.commit()
        print("\n✨ Todos los datos de prueba han sido inyectados correctamente.")
        cur.close()

    except Exception as error:
        print(f"❌ Error al sembrar datos: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    seed_bmo_data()
