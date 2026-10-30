import sqlite3
import uuid

# Conectar à base de dados
conn = sqlite3.connect('LAB_PETRA.db')
cursor = conn.cursor()

# Gerar um ID único no Python
novo_id = str(uuid.uuid4())

# Inserir o registo
cursor.execute('''
    INSERT INTO ensaios_granulometria (id, identificacao_amostra, data_ensaio, modulo_finura)
    VALUES (?, ?, ?, ?)
''', (novo_id, 'Areia Petra', '2026-10-30', 2.50))

conn.commit()
conn.close()