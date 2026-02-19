from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

# Load environment variables from .env file
load_dotenv()

def get_engine():
    #URL_MYSQL = os.getenv("URL_MYSQL")

    return create_engine(
        "test",
        pool_pre_ping=True,
    )


def validate_connection(engine):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            version = conn.execute(text("SELECT VERSION()")).scalar()
            current_db = conn.execute(text("SELECT DATABASE()")).scalar()
        print("✅ Conexão OK")
        print("MySQL version:", version)
        print("Database:", current_db)
        return True
    except SQLAlchemyError as e:
        print("❌ Falha na conexão com o MySQL/Aiven")
        print("Erro:", str(e))
        return False


def execute_sql(engine, sql_script: str):
    try:
        with engine.begin() as conn:
            for stmt in sql_script.split(";"):
                s = stmt.strip()
                if s:
                    conn.execute(text(s))
        print("✅ Script executado com sucesso.")
    except SQLAlchemyError as e:
        print("❌ Erro ao executar script SQL")
        print("Erro:", e)


if __name__ == "__main__":
    print("Iniciando teste de conexão...")
    engine = get_engine()
    validate_connection(engine)
