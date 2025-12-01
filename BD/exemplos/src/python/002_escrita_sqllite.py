from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
import sqlite3

# Base declarativa
Base = declarative_base()

class Aluno(Base):
    __tablename__ = 'aluno'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    idade = Column(Integer)

conn = sqlite3.connect('escola.db')
cursor = conn.cursor()

cursor.execute("INSERT INTO Aluno (nome, idade) VALUES (?, ?)", ("Roberta", 30))
conn.commit()
conn.close()

# Criar a conexão
engine = create_engine('sqlite:///escola.db', echo=True)

# Criar a sessão
Session = sessionmaker(bind=engine)
session = Session()

alunos = session.query(Aluno).all()
for aluno in alunos:
    print(aluno.id, aluno.nome, aluno.idade)