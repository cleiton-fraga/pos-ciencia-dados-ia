from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text

# Base declarativa
Base = declarative_base()

class Aluno(Base):
    __tablename__ = 'aluno'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    idade = Column(Integer)

# Criar a conexão
engine = create_engine('sqlite:///escola.db', echo=True)

# Criar as tabelas no banco (caso ainda não existam)
Base.metadata.create_all(engine)

# Criar a sessão
Session = sessionmaker(bind=engine)
session = Session()

# Inserindo dados de exemplo (apenas se o banco estiver vazio)
if session.query(Aluno).count() == 0:
    session.add_all([
        Aluno(nome="Maria", idade=22),
        Aluno(nome="João", idade=25),
        Aluno(nome="Ana", idade=20)
    ])
    session.commit()

# Leitura de dados
alunos = session.query(Aluno).all()
for aluno in alunos:
    print(aluno.id, aluno.nome, aluno.idade)


# Consulta ORM equivalente ao SELECT * FROM aluno WHERE idade >= 23;
alunos = session.query(Aluno).filter(Aluno.idade >= 23).all()

for aluno in alunos:
    print(aluno.id, aluno.nome, aluno.idade)


# Usando SQL direto
result = session.execute(text("SELECT * FROM aluno WHERE idade >= 23;"))

for row in result:
    print(row.id, row.nome, row.idade)