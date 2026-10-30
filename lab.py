import streamlit as st
import sqlite3
import pandas as pd
import uuid
from datetime import date
import plotly.express as px
from relatorio_pdf import gerar_pdf_ensaio

# Configuração da página
st.set_page_config(
    page_title="LIMS Concreto & Agregados",
    page_icon="🏗️",
    layout="wide"
)

DB_PATH = "LAB_PETRA.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

st.title("🏗️ Sistema de Controle Tecnológico - Laboratório")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Ensaio de Granulometria",
    "2. Traço de Concreto",
    "3. Ruptura de Corpos de Prova",
    "4. Dashboard & Rastreabilidade"
])

# -----------------------------------------------------------------------------
# ABA 1: GRANULOMETRIA (AGREGADO MIÚDO)
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Cadastro de Ensaio Granulométrico")
    with st.form("form_granulometria", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            amostra = st.text_input("Identificação da Amostra", placeholder="Ex: Areia Petra, Blend 70/30, Areia Especial")
            data_ensaio = st.date_input("Data do Ensaio", value=date.today())
            modulo_finura = st.number_input("Módulo de Finura (MF)", min_value=0.0, max_value=5.0, step=0.01, format="%.2f")
        
        with col2:
            d_max = st.number_input("Diâmetro Máximo Característico (mm)", min_value=0.0, max_value=50.0, step=0.1, format="%.2f")
            massa_esp = st.number_input("Massa Específica do Agregado (kg/dm³)", min_value=0.0, max_value=5.0, step=0.01, format="%.2f")
            obs = st.text_area("Observações Adicionais", placeholder="Origem da britagem, teor de finos, etc.")

        submit_gran = st.form_submit_button("Salvar Granulometria")

        if submit_gran:
            if not amostra.strip():
                st.error("Informe a identificação da amostra.")
            else:
                novo_id = f"GRAN-{str(uuid.uuid4())[:8].upper()}"
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ensaios_granulometria (
                        id, identificacao_amostra, data_ensaio, modulo_finura, 
                        diametro_maximo, massa_especifica_agregado, observacoes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (novo_id, amostra, str(data_ensaio), modulo_finura, d_max, massa_esp, obs))
                conn.commit()
                conn.close()
                st.success(f"Ensaio registrado com sucesso! Número de Série: **{novo_id}**")

# -----------------------------------------------------------------------------
# ABA 2: ENSAIO DE CONCRETO (ESTADO FRESCO)
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Dosagem e Ensaio do Concreto")
    
    # Busca os ensaios de granulometria existentes para vincular
    conn = get_connection()
    df_gran = pd.read_sql_query("SELECT id, identificacao_amostra, data_ensaio FROM ensaios_granulometria ORDER BY created_at DESC", conn)
    conn.close()

    if df_gran.empty:
        st.warning("Nenhum ensaio de granulometria cadastrado. Cadastre o agregado na Aba 1 antes de lançar o traço.")
    else:
        opcoes_gran = {
            f"{row['id']} - {row['identificacao_amostra']} ({row['data_ensaio']})": row['id']
            for _, row in df_gran.iterrows()
        }

        with st.form("form_concreto", clear_on_submit=True):
            gran_selecionada = st.selectbox(
                "Vincular ao Ensaio de Granulometria (Número de Série da Areia):",
                options=list(opcoes_gran.keys())
            )
            gran_id_fk = opcoes_gran[gran_selecionada]

            c1, c2, c3 = st.columns(3)
            with c1:
                tipo_traco = st.text_input("Identificação do Traço", placeholder="Ex: 1:3,5 Rico / 1:5,0 Médio")
                data_mold = st.date_input("Data de Moldagem", value=date.today())
                slump = st.number_input("Abatimento / Slump (mm)", min_value=0.0, max_value=300.0, step=5.0)

            with c2:
                prop_areia = st.number_input("Proporção Areia (em massa, relativo a 1 de cimento)", min_value=0.0, step=0.05, format="%.3f")
                prop_brita = st.number_input("Proporção Brita (em massa, relativo a 1 de cimento)", min_value=0.0, step=0.05, format="%.3f")
                rel_ac = st.number_input("Relação Água/Cimento (a/c)", min_value=0.1, max_value=1.5, step=0.01, format="%.2f")

            with c3:
                teor_argamassa = st.number_input("Teor de Argamassa (%)", min_value=0.0, max_value=100.0, step=0.5, format="%.2f")
                massa_esp_conc = st.number_input("Massa Específica do Concreto (kg/m³)", min_value=1500.0, max_value=3000.0, step=1.0)
                consumo_cimento = st.number_input("Consumo de Cimento (kg/m³)", min_value=0.0, max_value=1000.0, step=1.0)

            submit_conc = st.form_submit_button("Salvar Traço de Concreto")

            if submit_conc:
                id_concreto = f"CONC-{str(uuid.uuid4())[:8].upper()}"
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ensaios_concreto (
                        id, granulometria_id, data_moldagem, tipo_traco,
                        proporcao_cimento, proporcao_areia, proporcao_brita,
                        relacao_agua_cimento, teor_argamassa, slump,
                        massa_especifica_concreto, consumo_cimento_m3
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    id_concreto, gran_id_fk, str(data_mold), tipo_traco,
                    1.0, prop_areia, prop_brita, rel_ac, teor_argamassa,
                    slump, massa_esp_conc, consumo_cimento
                ))
                conn.commit()
                conn.close()
                st.success(f"Traço registrado com sucesso! ID do Traço: **{id_concreto}** vinculado a **{gran_id_fk}**.")

# -----------------------------------------------------------------------------
# ABA 3: RUPTURA DE CORPOS DE PROVA (PRENSA)
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Registo de Controlo Tecnológico (Ruptura à Compressão)")

    conn = get_connection()
    df_concreto = pd.read_sql_query("""
        SELECT c.id, c.tipo_traco, c.data_moldagem, g.identificacao_amostra
        FROM ensaios_concreto c
        INNER JOIN ensaios_granulometria g ON c.granulometria_id = g.id
        ORDER BY c.created_at DESC
    """, conn)
    conn.close()

    if df_concreto.empty:
        st.warning("Nenhum traço de betão registado. Registe um traço na Aba 2 antes de lançar ensaios de ruptura.")
    else:
        opcoes_concreto = {
            f"{row['id']} - {row['tipo_traco']} ({row['identificacao_amostra']} - Moldado em {row['data_moldagem']})": row['id']
            for _, row in df_concreto.iterrows()
        }

        with st.form("form_ruptura", clear_on_submit=True):
            concreto_sel = st.selectbox(
                "Selecione o Lote / Traço de Betão:",
                options=list(opcoes_concreto.keys())
            )
            id_concreto_fk = opcoes_concreto[concreto_sel]

            c1, c2, c3 = st.columns(3)
            with c1:
                idade_dias = st.selectbox("Idade do Provete (dias)", options=[3, 7, 14, 28, 63, 90], index=3)
            with c2:
                data_ruptura = st.date_input("Data da Ruptura", value=date.today())
            with c3:
                resistencia_mpa = st.number_input("Resistência Obtida (MPa)", min_value=0.0, max_value=120.0, step=0.1, format="%.2f")

            submit_rup = st.form_submit_button("Gravar Ruptura")

            if submit_rup:
                if resistencia_mpa <= 0:
                    st.error("A resistência mecânica tem de ser superior a zero.")
                else:
                    novo_id_rup = f"RUP-{str(uuid.uuid4())[:8].upper()}"
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO controle_tecnologico_ruptura (
                            id, ensaio_concreto_id, idade_dias, data_ruptura, resistencia_mpa
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (novo_id_rup, id_concreto_fk, idade_dias, str(data_ruptura), resistencia_mpa))
                    conn.commit()
                    conn.close()
                    st.success(f"Ruptura registada com sucesso! ({resistencia_mpa:.2f} MPa aos {idade_dias} dias)")

        st.markdown("#### Histórico de Rupturas Registadas")
        conn = get_connection()
        df_historico_rup = pd.read_sql_query("""
            SELECT r.id, c.tipo_traco, r.idade_dias, r.data_ruptura, r.resistencia_mpa, r.created_at
            FROM controle_tecnologico_ruptura r
            INNER JOIN ensaios_concreto c ON r.ensaio_concreto_id = c.id
            ORDER BY r.created_at DESC
        """, conn)
        conn.close()

        if not df_historico_rup.empty:
            st.dataframe(df_historico_rup, use_container_width=True)