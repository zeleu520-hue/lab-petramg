import sqlite3
import pandas as pd
from datetime import date
from jinja2 import Environment, FileSystemLoader
import pdfkit
import os

DB_PATH = "LAB_PETRA.db"

# Caminho padrão onde o wkhtmltopdf é instalado no Windows
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

def gerar_pdf_ensaio(id_concreto: str) -> bytes:
    conn = sqlite3.connect(DB_PATH)
    
    query_dados = """
        SELECT 
            c.id AS id_concreto, c.data_moldagem, c.tipo_traco,
            c.proporcao_cimento, c.proporcao_areia, c.proporcao_brita,
            c.relacao_agua_cimento, c.teor_argamassa, c.slump,
            c.massa_especifica_concreto, c.consumo_cimento_m3,
            g.id AS id_granulometria, g.identificacao_amostra, g.data_ensaio,
            g.modulo_finura, g.diametro_maximo, g.massa_especifica_agregado, g.observacoes
        FROM ensaios_concreto c
        INNER JOIN ensaios_granulometria g ON c.granulometria_id = g.id
        WHERE c.id = ?
    """
    df_dados = pd.read_sql_query(query_dados, conn, params=(id_concreto,))
    
    query_rupturas = """
        SELECT idade_dias, data_ruptura, resistencia_mpa
        FROM controle_tecnologico_ruptura
        WHERE ensaio_concreto_id = ?
        ORDER BY idade_dias ASC
    """
    df_rupturas = pd.read_sql_query(query_rupturas, conn, params=(id_concreto,))
    conn.close()

    if df_dados.empty:
        raise ValueError(f"Ensaio {id_concreto} não encontrado.")

    registro = df_dados.iloc[0].to_dict()
    lista_rupturas = df_rupturas.to_dict(orient="records")

    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template_relatorio.html")
    
    html_renderizado = template.render(
        dados=registro, rupturas=lista_rupturas, data_emissao=date.today().strftime("%d/%m/%Y")
    )

    # Gera o PDF em memória usando pdfkit
    pdf_bytes = pdfkit.from_string(html_renderizado, False, configuration=config, options={"enable-local-file-access": ""})
    return pdf_bytes