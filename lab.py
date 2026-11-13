import streamlit as st
import pandas as pd
import numpy as np
import json
import io
import urllib.parse
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from supabase import create_client, Client

# =========================================================
# 1. CONFIGURAÇÃO E CONEXÃO SUPABASE
# =========================================================
st.set_page_config(page_title="GRANCON | LIMS Master", layout="wide", initial_sidebar_state="collapsed")

SUPABASE_URL = "https://udpotarucqkpxpockinb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVkcG90YXJ1Y3FrcHhwb2NraW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMzNDM0ODQsImV4cCI6MjEwODkxOTQ4NH0.FwQDupgQmPQ4PYCC8Hrlw3a2gmosW6eCZxdgddtQy6c" 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# 2. CONSTANTES NORMATIVAS (ABNT NBR 7211)
# =========================================================
PENEIRAS_MESTRA = [75.0, 63.0, 50.0, 37.5, 31.5, 25.0, 19.0, 12.5, 9.5, 6.3, 4.75, 2.36, 1.18, 0.6, 0.3, 0.15, 0.075]

LIMITES_NORMA = {
    "Areia": {"9.5": (100,100), "4.75": (90,100), "2.36": (75,100), "1.18": (50,90), "0.6": (25,65), "0.3": (10,35), "0.15": (2,10)},
    "Brita 0": {"19.0": (100,100), "12.5": (90,100), "9.5": (20,50), "4.75": (0,5), "2.36": (0,2)},
    "Brita 1": {"37.5": (100,100), "25.0": (90,100), "19.0": (20,50), "9.5": (0,5), "4.75": (0,2)}
}
PENEIRAS_NORMA_LANCAMENTO = ["75", "63", "50", "37.5", "31.5", "25", "19", "12.5", "9.5", "6.3", "4.75", "2.36", "1.18", "0.6", "0.3", "0.15", "0.075", "fundo"]

# =========================================================
# 3. CSS GLOBAL (DARK MODE ENTERPRISE)
# =========================================================
st.markdown("""
    <style>
    .stApp { background-color: #17191e; color: #9aa0a6; font-family: 'Inter', sans-serif; }
    header { visibility: hidden; }
    h1, h2, h3, h4 { color: #e8eaed !important; font-weight: 700 !important; }
    .destaque-verde { color: #2ea043; }
    
    .card { background-color: #20232a; padding: 24px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .parecer-tecnico { background-color: #20232a; color: #c9d1d9; padding: 25px; border-radius: 8px; border-left: 6px solid #58a6ff; font-size: 1.10rem; line-height: 1.7; }
    .texto-explicativo { color: #8b949e; font-size: 1rem; margin-bottom: 20px; }
    
    button[data-baseweb="tab"] { background-color: transparent !important; color: #8b949e !important; font-size: 1rem !important; text-transform: uppercase; font-weight: 600; border: none !important; padding-bottom: 10px !important; }
    button[aria-selected="true"] { color: #2ea043 !important; border-bottom: 3px solid #2ea043 !important; }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] { background-color: #2d333b !important; border-radius: 8px !important; border: 1px solid #444c56 !important; }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within { border-color: #58a6ff !important; }
    div[data-baseweb="input"] input { color: #c9d1d9 !important; font-weight: bold !important; font-size: 16px !important; }
    button[kind="primary"] { background-color: #2ea043 !important; color: #ffffff !important; font-weight: 600 !important; border: none !important; border-radius: 8px !important; }
    
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: 800 !important; color: #58a6ff !important; line-height: 1; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; color: #8b949e !important; text-transform: uppercase; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='margin-top: -50px; margin-bottom: 30px;'>
        <h1 style='font-size: 2.5rem; font-weight: 900; letter-spacing: 2px; margin-bottom: 0;'>
            <span style='color: #2ea043;'>GRAN</span><span style='color: #eab308;'>CON</span>
        </h1>
        <p style='color: #8b949e; font-size: 0.9rem; margin-top: -10px;'>DSA SOLUÇÕES | LIMS MASTER</p>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# 4. EXTRAÇÃO DE DADOS GLOBAL
# =========================================================
@st.cache_data(ttl=60)
def carregar_granulometria():
    res = supabase.table("ensaios_granulometria").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['data_ensaio'] = pd.to_datetime(df['data_ensaio'])
        df['modulo_finura'] = pd.to_numeric(df['modulo_finura'], errors='coerce').fillna(0)
        df['dmc_mm'] = pd.to_numeric(df['dmc_mm'], errors='coerce').fillna(0)
        df['Material_Real'] = df['tipo_agregado'].fillna("Desconhecido").apply(lambda x: str(x).strip())
    return df

@st.cache_data(ttl=60)
def carregar_concreto():
    res = supabase.table("ensaios_concreto").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['data_moldagem'] = pd.to_datetime(df['data_moldagem'])
    return df

df_gran = carregar_granulometria()
df_conc = carregar_concreto()

# =========================================================
# 5. GERADOR DE LAUDO SIMPLES
# =========================================================
def gerar_relatorio_unificado(dados_concreto, lista_dados_granulometria):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements, styles = [], getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), alignment=TA_CENTER, spaceAfter=12)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceBefore=10, spaceAfter=6)
    
    elements.append(Paragraph("LAUDO TÉCNICO INTEGRADO: CONCRETO E AGREGADOS", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    info_concreto = [
        ["Lote de Concreto:", dados_concreto.get('id_ensaio', '-'), "Data Moldagem:", dados_concreto.get('data_moldagem', '-')],
        ["Referência:", dados_concreto.get('tipo_material', '-'), "Traço:", dados_concreto.get('traco_proporcao', '-')],
        ["Fck Médio Obtido:", f"{dados_concreto.get('resistencia_media_mpa', 0)} MPa", "Slump:", f"{dados_concreto.get('abatimento_mm', 0)} mm"]
    ]
    t_conc = Table(info_concreto, colWidths=[4*cm, 4.5*cm, 3.5*cm, 4.5*cm])
    t_conc.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'), ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")), ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0"))]))
    elements.append(t_conc)
    elements.append(Spacer(1, 1*cm))
    
    if lista_dados_granulometria:
        elements.append(Paragraph("RASTREABILIDADE DE AGREGADOS VINCULADOS", subtitle_style))
        for dg in lista_dados_granulometria:
            info_g = f"<b>Material:</b> {dg.get('tipo_agregado')} | <b>Lote:</b> {dg.get('id_ensaio')} | <b>Módulo Finura:</b> {dg.get('modulo_finura')} | <b>DMC:</b> {dg.get('dmc_mm')} mm"
            elements.append(Paragraph(info_g, styles['Normal']))
            elements.append(Spacer(1, 0.3*cm))
    else:
        elements.append(Paragraph("<i>Nenhum agregado rastreável vinculado a este traço.</i>", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================================================
# 6. INICIALIZAÇÃO DE ESTADOS PARA O GÊMEO DIGITAL
# =========================================================
if 'peneiras_ativas' not in st.session_state: st.session_state.peneiras_ativas = []
if 'massas_retidas' not in st.session_state: st.session_state.massas_retidas = {}

if 'lista_periodos_adv' not in st.session_state:
    st.session_state.lista_periodos_adv = [
        {"id": 0, "ini": date(2019, 1, 1), "fim": date(2019, 12, 31)},
        {"id": 1, "ini": date(2020, 1, 1), "fim": date(2020, 12, 31)},
        {"id": 2, "ini": date(2021, 1, 1), "fim": date(2021, 12, 31)},
        {"id": 3, "ini": date(2022, 1, 1), "fim": date(2022, 12, 31)},
        {"id": 4, "ini": date(2023, 1, 1), "fim": date(2023, 12, 31)},
        {"id": 5, "ini": date(2024, 1, 1), "fim": date(2024, 12, 31)},
        {"id": 6, "ini": date(2025, 1, 1), "fim": date(2025, 12, 31)},
        {"id": 7, "ini": date(2026, 1, 1), "fim": date.today()},
    ]
if 'proximo_id_periodo' not in st.session_state: st.session_state.proximo_id_periodo = 8

# =========================================================
# 7. AS 8 ABAS DO SISTEMA
# =========================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🪨 Granulometria", "🏗️ Concreto", "📈 Auditoria Simples", 
    "🧪 Prensagem & QR", "📊 Painel Analítico", "📄 Laudos", 
    "🧠 IA Gêmeo Digital", "🎯 Performance & Radar"
])

# --- ABA 1: GRANULOMETRIA ---
with tab1:
    st.header("Lançamento de Granulometria")
    c_a, c_b, c_d = st.columns(3)
    with c_a: nome_ensaio = st.text_input("Nome da Amostra:")
    with c_b: tipo_agregado = st.selectbox("Tipo de Material:", ["Areia Especial para Concreto", "Areia Industrial Média", "Areia Industrial Fina", "Areia Industrial Fina Plus", "Brita #0", "Brita #1", "Bica Corrida"])
    with c_d: data_ensaio = st.date_input("Data do Ensaio:", format="DD/MM/YYYY")

    col_sel, col_btn = st.columns([4, 1])
    with col_sel:
        opcoes_disponiveis = [p for p in PENEIRAS_NORMA_LANCAMENTO if p not in st.session_state.peneiras_ativas]
        peneira_escolhida = st.selectbox("Adicione uma Peneira:", options=opcoes_disponiveis, format_func=lambda x: f"{x} mm" if x != "fundo" else "Fundo")
    with col_btn:
        st.write(""); st.write("")
        if st.button("➕ Adicionar", use_container_width=True, key="btn_add_pen") and peneira_escolhida:
            st.session_state.peneiras_ativas.append(peneira_escolhida)
            st.session_state.massas_retidas[peneira_escolhida] = 0.0
            st.rerun()

    st.markdown("### Massas Retidas (g)")
    if st.session_state.peneiras_ativas:
        peneiras_ordenadas = sorted(st.session_state.peneiras_ativas, key=lambda x: PENEIRAS_NORMA_LANCAMENTO.index(x))
        for pen in peneiras_ordenadas:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1: st.markdown(f"<p style='margin-top: 10px; font-weight: bold; color: #2ea043;'>{pen} mm</p>", unsafe_allow_html=True)
            with c2: st.session_state.massas_retidas[pen] = st.number_input(f"Massa {pen}", min_value=0.0, value=float(st.session_state.massas_retidas.get(pen, 0.0)), step=0.1, key=f"massa_{pen}", label_visibility="collapsed")
            with c3:
                if st.button("🗑️ Remover", key=f"del_{pen}"):
                    st.session_state.peneiras_ativas.remove(pen); del st.session_state.massas_retidas[pen]; st.rerun()
        
        massa_esp = st.number_input("Massa Específica (g/cm³)", value=2.65, step=0.01)
        if st.button("💾 Salvar Ensaio de Granulometria", type="primary", use_container_width=True) and nome_ensaio:
            pens = st.session_state.massas_retidas
            total_massa = sum(pens.values()) if sum(pens.values()) > 0 else 1
            seq_finura = ['0.15', '0.3', '0.6', '1.18', '2.36', '4.75', '9.5', '19', '37.5', '75']
            soma_acumuladas = sum([(sum([float(pens.get(p, 0)) for p in pens.keys() if p != 'fundo' and float(p) >= float(k)]) / total_massa) * 100 for k in seq_finura])
            mf_calc = soma_acumuladas / 100
            
            peneiras_reais = sorted([float(p) for p in pens.keys() if p != 'fundo'], reverse=True)
            dmc_calc = 0
            retida_acum = 0
            for p in peneiras_reais:
                retida_acum += (float(pens.get(str(p), 0)) / total_massa) * 100
                if retida_acum > 5:
                    dmc_calc = p; break
            if dmc_calc == 0 and peneiras_reais: dmc_calc = peneiras_reais[0]

            dados = { 
                "id_ensaio": f"GRAN-{datetime.now().strftime('%y%m%d%H%M%S')}", 
                "data_ensaio": str(data_ensaio), 
                "nome_ensaio": nome_ensaio, 
                "tipo_agregado": tipo_agregado, 
                "massa_total_g": total_massa, 
                "modulo_finura": round(mf_calc, 2), 
                "dmc_mm": float(dmc_calc), 
                "massa_especifica_g_cm3": massa_esp, 
                "dados_peneiramento": json.dumps(pens) 
            }
            try:
                supabase.table("ensaios_granulometria").insert(dados).execute()
                st.success(f"✅ Ensaio salvo! MF: {mf_calc:.2f} | DMC: {dmc_calc} mm")
            except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: CONCRETO ---
with tab2:
    st.header("Dosagem de Concreto e Vínculo de Agregados")
    opcoes_agregados = {f"{g['id_ensaio']} | {g['tipo_agregado']} ({g['data_ensaio'].strftime('%d/%m/%Y')})": g['id_ensaio'] for _, g in df_gran.sort_values("data_ensaio", ascending=False).head(20).iterrows()} if not df_gran.empty else {}
    agregados_selecionados = st.multiselect("Vincular ensaios de areia/brita (Rastreabilidade):", list(opcoes_agregados.keys()))
    
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1: tipo_material_conc = st.text_input("Referência:", value="AREIA PETRA")
    with c2: tipo_traco = st.selectbox("Traço:", ["Traço Rico", "Traço Médio", "Traço Pobre"])
    with c3: traco_proporcao = st.text_input("Proporção (1:Ar:Br):", placeholder="1 : 3,5 : 2,2")
    with c4: data_moldagem_conc = st.date_input("Data Moldagem:", format="DD/MM/YYYY")

    cm1, cm2, cm3, cm4, cm5 = st.columns(5)
    with cm1: cim_kg = st.number_input("Cimento (kg)", step=0.1)
    with cm2: am1_kg = st.number_input("Miúdo 1 (kg)", step=0.1)
    with cm3: am2_kg = st.number_input("Miúdo 2 (kg)", step=0.1)
    with cm4: br1_kg = st.number_input("Brita (kg)", step=0.1)
    with cm5: ag_kg = st.number_input("Água (kg)", step=0.1)
    
    c6, c7, c8, c9, c10 = st.columns(5)
    with c6: teor_argamassa = st.number_input("Teor Arg. (%)", step=0.1)
    with c7: abatimento = st.number_input("Slump (mm)", step=1.0)
    with c8: massa_esp_conc = st.number_input("Massa Espec. (kg/m³)", step=1.0)
    with c9: consumo_cim = st.number_input("Consumo Cim. (kg)", step=1.0)
    with c10: relacao_ac = st.number_input("A/C", step=0.01)

    num_cps = st.number_input("CPs (Ensaio Destrutivo)", min_value=1, max_value=12, value=6)
    cp_cols, resistencias = st.columns(6), []
    for i in range(int(num_cps)):
        with cp_cols[i % 6]: resistencias.append(st.number_input(f"CP {i+1} (MPa)", step=0.1, key=f"cp_{i}"))
    
    media_mpa = sum(resistencias) / len(resistencias) if resistencias else 0.0
    st.info(f"**Média de Ruptura:** {media_mpa:.2f} MPa")

    if st.button("💾 Salvar Traço e Gerar QR Code", type="primary", use_container_width=True) and tipo_material_conc:
        id_conc = f"CONC-{datetime.now().strftime('%y%m%d%H%M%S')}"
        dados_concreto = { 
            "id_ensaio": id_conc, "data_moldagem": str(data_moldagem_conc), "tipo_material": tipo_material_conc, 
            "tipo_traco": tipo_traco, "traco_proporcao": traco_proporcao, "teor_argamassa_perc": teor_argamassa, 
            "cimento_kg": cim_kg, "agregado_miudo_1_kg": am1_kg, "agregado_miudo_2_kg": am2_kg, "brita_1_kg": br1_kg, 
            "agua_kg": ag_kg, "massa_especifica_kg_m3": massa_esp_conc, "consumo_cimento_kg_m3": consumo_cim, 
            "relacao_a_c": relacao_ac, "abatimento_mm": abatimento, "num_cps": int(num_cps), 
            "resistencias_individuais": json.dumps(resistencias), "resistencia_media_mpa": round(media_mpa, 2),
            "agregados_vinculados": json.dumps([opcoes_agregados[sel] for sel in agregados_selecionados])
        }
        try:
            supabase.table("ensaios_concreto").upsert(dados_concreto).execute()
            st.success(f"✅ Traço Salvo! ID: {id_conc}")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(f'https://grancon-lab.com/rompimento?id={id_conc}')}&bgcolor=2ea043"
            st.image(qr_url, width=200)
        except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3, 4, 5, 6: (Mantidas Simples) ---
with tab3: st.info("Utilize a Guia '🧠 IA Gêmeo Digital' para análises avançadas.")
with tab4: st.info("Módulo em desenvolvimento.")
with tab5: st.info("Consulte a Guia '🧠 IA Gêmeo Digital' para os novos KPIs e Dashboards.")
with tab6:
    st.header("Emissão de Laudos Rápidos")
    if not df_conc.empty:
        opcoes_c = {f"{r['id_ensaio']} | {r['tipo_material']} ({r['data_moldagem'].strftime('%d/%m/%Y')})": r.to_dict() for _, r in df_conc.iterrows()}
        esc = st.selectbox("Selecione o Lote de Concreto:", list(opcoes_c.keys()))
        if st.button("🖨️ GERAR LAUDO", type="primary"):
            dados_c_alvo = opcoes_c[esc]
            vinculos = json.loads(dados_c_alvo.get('agregados_vinculados', '[]'))
            lista_agregados = df_gran[df_gran['id_ensaio'].isin(vinculos)].to_dict('records') if vinculos and not df_gran.empty else []
            st.download_button("📥 Baixar Laudo Integrado", data=gerar_relatorio_unificado(dados_c_alvo, lista_agregados), file_name=f"Laudo_{dados_c_alvo['id_ensaio']}.pdf", mime="application/pdf")

# =========================================================
# --- ABA 7: INTELIGÊNCIA AVANÇADA E DOSSIÊ TÉCNICO (GÊMEO DIGITAL & PDF) ---
# =========================================================
with tab7:
    st.markdown("<h2>🧠 Investigação Técnica: <span class='destaque-verde'>Gêmeo Digital Corporativo</span></h2>", unsafe_allow_html=True)
    
    if df_gran.empty:
        st.warning("Banco de Granulometria vazio.")
    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### ⚙️ Configuração de Períodos Amostrais")
        col_mat, col_btn_add = st.columns([3, 1])
        materiais_db_reais = sorted(list(df_gran['Material_Real'].dropna().unique()))
        
        with col_mat: mat_sel_adv = st.selectbox("Material Investigado:", materiais_db_reais, key="mat_adv")
        with col_btn_add: 
            st.write(""); st.write("")
            if st.button("➕ Adicionar Intervalo Extra", use_container_width=True):
                st.session_state.lista_periodos_adv.append({
                    "id": st.session_state.proximo_id_periodo, 
                    "ini": date(2026, 1, 1), 
                    "fim": date.today()
                })
                st.session_state.proximo_id_periodo += 1
                st.rerun()

        # REENDERIZAR OS INTERVALOS DA SESSÃO COM BOTÃO DE EXCLUIR
        ids_para_remover = []
        periodos_validados = []
        
        cols_periodos = st.columns(4)
        for i, periodo in enumerate(st.session_state.lista_periodos_adv):
            with cols_periodos[i % 4]:
                st.markdown(f"**📅 Intervalo {i+1}**")
                
                d_ini = st.date_input("Início", value=periodo['ini'], format="DD/MM/YYYY", key=f"adv_ini_{periodo['id']}")
                d_fim = st.date_input("Fim", value=periodo['fim'], format="DD/MM/YYYY", key=f"adv_fim_{periodo['id']}")
                
                chave_botao = f"del_per_{periodo['id']}"
                if st.button("🗑️ Excluir", key=chave_botao, help="Remover este intervalo da análise"):
                    ids_para_remover.append(periodo['id'])
                else:
                    periodo['ini'] = d_ini
                    periodo['fim'] = d_fim
                    nome_intervalo = f"{d_ini.strftime('%d/%m/%Y')} - {d_fim.strftime('%d/%m/%Y')}"
                    periodos_validados.append({"nome": nome_intervalo, "ini": d_ini, "fim": d_fim})

        if ids_para_remover:
            st.session_state.lista_periodos_adv = [p for p in st.session_state.lista_periodos_adv if p['id'] not in ids_para_remover]
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)

        # PROCESSAMENTO MATEMÁTICO
        def processar_grupo_adv(df_grupo, nome_grupo):
            historico = []
            if df_grupo.empty: return pd.DataFrame(), pd.DataFrame(), None
            for _, row in df_grupo.sort_values("data_ensaio").iterrows():
                pens = row['dados_peneiramento']
                if isinstance(pens, str): pens = json.loads(pens)
                massa_total = float(row['massa_total_g']) if float(row['massa_total_g']) > 0 else 1
                rotulo = f"{row['data_ensaio'].strftime('%d/%m/%Y')} | {nome_grupo}"
                linha_ret = {"Rótulo": rotulo, "Data": row['data_ensaio'], "MF": row['modulo_finura'], "DMC": row['dmc_mm'], "Grupo": nome_grupo}
                linha_pas = {"Rótulo": rotulo, "Data": row['data_ensaio'], "Grupo": nome_grupo}
                acumulado = 0
                for p in PENEIRAS_MESTRA:
                    p_str = str(p).replace(".0", "") if str(p).endswith(".0") else str(p)
                    ret = float(pens.get(p_str, 0)); perc_ret = (ret / massa_total) * 100; acumulado += perc_ret
                    linha_ret[p_str] = perc_ret; linha_pas[p_str] = max(0, 100 - acumulado)
                historico.append({"ret": linha_ret, "pas": linha_pas})
            df_ret = pd.DataFrame([h["ret"] for h in historico])
            df_pas = pd.DataFrame([h["pas"] for h in historico])
            peneiras_str = [str(p).replace(".0", "") if str(p).endswith(".0") else str(p) for p in PENEIRAS_MESTRA]
            media_ret = df_ret[peneiras_str].mean()
            resumo = {"Nome": nome_grupo, "MF_Medio": df_ret['MF'].mean(), "DMC_Medio": df_ret['DMC'].mean(), "Pico_Peneira": media_ret.idxmax(), "Pico_Retencao": media_ret.max(), "Qtd": len(df_grupo)}
            return df_ret, df_pas, resumo

        df_mat_adv = df_gran[df_gran['Material_Real'] == mat_sel_adv]
        dados_processados = []
        
        for p in periodos_validados:
            df_p = df_mat_adv[(df_mat_adv['data_ensaio'].dt.date >= p['ini']) & (df_mat_adv['data_ensaio'].dt.date <= p['fim'])]
            df_r, df_pa, res = processar_grupo_adv(df_p, p['nome'])
            if res:
                dados_processados.append({"resumo": res, "df_ret": df_r, "df_pas": df_pa, "ini": p['ini'], "fim": p['fim']})

        if not dados_processados:
            st.error("Nenhum dado encontrado para os parâmetros selecionados.")
        else:
            peneiras_str_all = [str(p).replace(".0", "") if str(p).endswith(".0") else str(p) for p in PENEIRAS_MESTRA]
            ret_full = pd.concat([d['df_ret'] for d in dados_processados])
            media_full = ret_full[peneiras_str_all].mean()
            serie_peneiras = media_full[media_full > 0.05].index.tolist()

            norma_alvo = None
            mat_lower = mat_sel_adv.lower()
            if "areia" in mat_lower or "pó" in mat_lower or "miúdo" in mat_lower: norma_alvo = "Areia"
            elif "brita 0" in mat_lower or "#0" in mat_lower: norma_alvo = "Brita 0"
            elif "brita 1" in mat_lower or "#1" in mat_lower: norma_alvo = "Brita 1"

            # =========================================================
            # ANÁLISE DE ENGENHARIA (MOTOR IA INVISÍVEL)
            # =========================================================
            def gerar_laudo_tecnico(lista_dados, material, norma, serie_p):
                q_ensaios = sum(d['resumo']['Qtd'] for d in lista_dados)
                texto = f"<b>1. AVALIAÇÃO DE CONFORMIDADE E GÊMEO DIGITAL</b><br/>"
                texto += f"O presente dossiê consolida os dados de {q_ensaios} ensaios físicos do material <b>{material}</b>. "
                texto += "Através de modelagem computacional (Gêmeo Digital), o perfil granulométrico extraído foi sobreposto aos fusos teóricos da norma <b>ABNT NBR 7211</b> para validação geométrica contínua.<br/><br/>"
                
                if len(lista_dados) < 2:
                    texto += "<b>2. DIAGNÓSTICO ESTÁTICO:</b> A análise baseia-se num único intervalo. O material apresenta-se dentro das características médias de processamento, recomendando-se a ampliação da amostragem temporal para aferir tendências e desgastes mecânicos ao longo do tempo.<br/>"
                    return texto
                
                p_base = lista_dados[0]
                p_alvo = lista_dados[-1]
                delta_mf = p_alvo['resumo']['MF_Medio'] - p_base['resumo']['MF_Medio']
                ret_base = p_base['df_ret'][serie_p].mean()
                ret_alvo = p_alvo['df_ret'][serie_p].mean()
                diff_ret = ret_alvo - ret_base
                gap_peneira = diff_ret.abs().idxmax()
                val_gap = diff_ret[gap_peneira]
                
                texto += "<b>2. ANÁLISE DE VARIÂNCIA EVOLUTIVA</b><br/>"
                texto += f"Comparando o período histórico base ({p_base['resumo']['Nome']}) com a amostragem mais recente ({p_alvo['resumo']['Nome']}), "
                
                if delta_mf > 0.15:
                    texto += f"o algoritmo detectou um <b><font color='#ff7b72'>ENGROSSAMENTO ESTRUTURAL</font></b> crítico da amostra (ΔMF = {delta_mf:+.2f}). "
                    texto += f"A distorção concentra-se especificamente na malha de <b>{gap_peneira} mm</b>, que sofreu um acréscimo de retenção de {val_gap:+.1f}%.<br/><br/>"
                    texto += "<b>3. INVESTIGAÇÃO DE CAUSA RAIZ (ROOT CAUSE) E PLANO DE AÇÃO</b><br/>"
                    texto += "• <b>Planta de Britagem:</b> Possível desgaste avançado dos revestimentos/mandíbulas do britador ou abertura acidental do CSS (Closed-Side Setting).<br/>"
                    texto += "• <b>Peneiramento Vibratório:</b> Risco de ruptura iminente da tela de classificação correspondente à fração graúda.<br/>"
                    texto += "• <b>Ação Recomendada:</b> Agendar inspeção mecânica no estágio de cominuição primária/secundária na próxima parada de manutenção."
                elif delta_mf < -0.15:
                    texto += f"o algoritmo detectou um <b><font color='#ff7b72'>AFINAMENTO ESTRUTURAL</font></b> severo da amostra (ΔMF = {delta_mf:+.2f}). "
                    texto += f"O desvio principal foi mapeado na malha de <b>{gap_peneira} mm</b> com variação de {val_gap:+.1f}%.<br/><br/>"
                    texto += "<b>3. INVESTIGAÇÃO DE CAUSA RAIZ (ROOT CAUSE) E PLANO DE AÇÃO</b><br/>"
                    texto += "• <b>Lavra e Geologia:</b> Migração da frente de desmonte para maciço rochoso mais friável, alterado, ou carga de explosivo acima do necessário (geração excessiva de finos).<br/>"
                    texto += "• <b>Planta de Britagem:</b> Operação do britador com câmara afogada ou CSS excessivamente fechado.<br/>"
                    texto += "• <b>Peneiramento:</b> Cegamento parcial das malhas inferiores, impedindo o escoamento eficiente.<br/>"
                    texto += "• <b>Ação Recomendada:</b> Realizar limpeza/desobstrução das malhas de peneiramento e revisar o plano de fogo/lavra."
                else:
                    texto += f"verificou-se <b><font color='#2ea043'>ESTABILIDADE MORFOMÉTRICA</font></b> de alta confiabilidade (Variação de finura nula ou ínfima: ΔMF = {delta_mf:+.2f}).<br/><br/>"
                    texto += "<b>3. DIAGNÓSTICO OPERACIONAL E MECÂNICO</b><br/>"
                    texto += "• O Gêmeo Digital confirma que os processos de britagem, desmonte e peneiramento mantêm a constância do produto.<br/>"
                    texto += "• Não há evidências analíticas de desgaste prematuro de revestimentos na linha temporal analisada."
                return texto

            texto_dossie = gerar_laudo_tecnico(dados_processados, mat_sel_adv, norma_alvo, serie_peneiras)

            st.markdown("## 🧠 Laudo Técnico Especialista")
            st.markdown(f"<div class='parecer-tecnico'>{texto_dossie}</div>", unsafe_allow_html=True)
            
            # TABELA COMPARATIVA GERAL
            st.markdown("## 📋 Matriz Comparativa (Gêmeo Digital)")
            tabela_final = []
            colunas_df = ["Malha (mm)", "Norma Mín (%)", "Norma Máx (%)"] + [d['resumo']['Nome'] for d in dados_processados] + ["Status Final"]
            
            for p in serie_peneiras:
                linha = {"Malha (mm)": p}
                n_min, n_max = "-", "-"
                if norma_alvo and norma_alvo in LIMITES_NORMA and p in LIMITES_NORMA[norma_alvo]:
                    n_min = LIMITES_NORMA[norma_alvo][p][0]
                    n_max = LIMITES_NORMA[norma_alvo][p][1]
                
                linha["Norma Mín (%)"] = n_min
                linha["Norma Máx (%)"] = n_max
                val_atual = 0
                for d in dados_processados:
                    val = d['df_pas'][p].mean()
                    linha[d['resumo']['Nome']] = f"{val:.1f}"
                    val_atual = val
                
                status = "Sem Norma"
                if n_min != "-" and n_max != "-":
                    if n_min <= val_atual <= n_max: status = "✅ Conforme"
                    elif val_atual < n_min: status = "🚨 Falha (Abaixo)"
                    else: status = "🚨 Falha (Acima)"
                linha["Status Final"] = status
                tabela_final.append(linha)

            st.dataframe(pd.DataFrame(tabela_final), use_container_width=True, hide_index=True)

            # GRÁFICOS WEB
            col_curva, col_bar = st.columns([1.5, 1])
            cores_p = px.colors.qualitative.Set1
            
            with col_curva:
                st.markdown("<div class='card'><h3>📐 Envelope Granulométrico Contínuo</h3></div>", unsafe_allow_html=True)
                fig_cur = go.Figure()
                if norma_alvo and norma_alvo in LIMITES_NORMA:
                    p_n = [p for p in serie_peneiras if p in LIMITES_NORMA[norma_alvo]]
                    n_min = [LIMITES_NORMA[norma_alvo][p][0] for p in p_n]
                    n_max = [LIMITES_NORMA[norma_alvo][p][1] for p in p_n]
                    fig_cur.add_trace(go.Scatter(x=p_n, y=n_max, mode='lines', line=dict(color='#2ea043', dash='dash'), name='Teto Norma'))
                    fig_cur.add_trace(go.Scatter(x=p_n, y=n_min, mode='lines', fill='tonexty', fillcolor='rgba(46, 160, 67, 0.1)', line=dict(color='#2ea043', dash='dash'), name='Piso Norma'))

                for idx, d in enumerate(dados_processados):
                    fig_cur.add_trace(go.Scatter(x=serie_peneiras, y=d['df_pas'][serie_peneiras].mean().values, mode='lines+markers', line=dict(color=cores_p[idx % len(cores_p)], width=3), name=d['resumo']['Nome']))
                fig_cur.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(title="Peneiras (mm)", autorange="reversed", type="category"), yaxis=dict(title="% Passante Acumulada", range=[0, 105]), height=400, font=dict(color='#8b949e'), margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified")
                st.plotly_chart(fig_cur, use_container_width=True)

            with col_bar:
                st.markdown("<div class='card'><h3>📊 Retenção por Malha (%)</h3></div>", unsafe_allow_html=True)
                fig_bar = go.Figure()
                for idx, d in enumerate(dados_processados):
                    fig_bar.add_trace(go.Bar(x=[f"{p}mm" for p in serie_peneiras], y=d['df_ret'][serie_peneiras].mean().values, name=d['resumo']['Nome'], marker_color=cores_p[idx % len(cores_p)]))
                fig_bar.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Peneiras (mm)", yaxis_title="% Massa Retida", height=400, font=dict(color='#8b949e'), margin=dict(l=0, r=0, t=10, b=0), legend=dict(x=0.01, y=0.99))
                st.plotly_chart(fig_bar, use_container_width=True)

            # =========================================================
            # GÊMEOS DIGITAIS INDIVIDUAIS (RAIO-X) NA WEB
            # =========================================================
            st.markdown("---")
            st.markdown("### 🩻 Gêmeos Digitais por Período (Raio-X)")
            st.markdown("<p style='color: #8b949e;'>Representação da pilha de peneiras individual para cada intervalo, destacando o percentual retido e os limites dimensionais.</p>", unsafe_allow_html=True)
            
            num_periods = len(dados_processados)
            cols_twins = st.columns(num_periods if num_periods > 0 else 1)
            
            for i, d in enumerate(dados_processados):
                ret_mean = d['df_ret'][serie_peneiras].mean()
                active_s = ret_mean[ret_mean > 0.0].index.tolist()
                d_max_val = max([float(x) for x in active_s]) if active_s else 0.0
                d_min_val = min([float(x) for x in active_s]) if active_s else 0.0
                
                with cols_twins[i]:
                    st.markdown(f"<div class='card' style='padding: 10px; margin-bottom: 0;'>", unsafe_allow_html=True)
                    st.markdown(f"<h4 style='text-align: center; color: #58a6ff; margin-bottom: 2px; font-size: 1.0rem;'>{d['resumo']['Nome']}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; font-size: 0.85rem; color: #8b949e; margin-top: 0;'>Dmáx: <b>{d_max_val} mm</b> | Dmín: <b>{d_min_val} mm</b></p>", unsafe_allow_html=True)
                    
                    fig_twin = px.bar(
                        x=ret_mean.values, 
                        y=[str(s) for s in serie_peneiras], 
                        orientation='h',
                        text=[f"{v:.1f}%" if v > 0.1 else "" for v in ret_mean.values]
                    )
                    fig_twin.update_traces(marker_color='#3b82f6', textposition='outside')
                    fig_twin.update_layout(
                        height=400, margin=dict(l=0, r=0, t=0, b=0),
                        xaxis_title="% Retida", yaxis_title="Malha (mm)",
                        yaxis=dict(autorange="reversed", type="category"),
                        xaxis=dict(range=[0, max(ret_mean.values)*1.2 if len(ret_mean)>0 else 100]),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#8b949e')
                    )
                    st.plotly_chart(fig_twin, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            # =========================================================
            # MOTOR DE GERAÇÃO PDF EXECUTIVO (GÊMEO DIGITAL, KPIs E ANÁLISE)
            # =========================================================
            def gerar_pdf_academico():
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
                els, sty = [], getSampleStyleSheet()
                
                # Estilos PDF
                t_st = ParagraphStyle('Title', parent=sty['Heading1'], fontSize=16, textColor=colors.HexColor("#0f172a"), alignment=TA_CENTER, spaceAfter=15, fontName='Helvetica-Bold')
                sub_st = ParagraphStyle('SubTitle', parent=sty['Normal'], fontSize=10, textColor=colors.HexColor("#64748b"), alignment=TA_CENTER, spaceAfter=20)
                h_st = ParagraphStyle('Header', parent=sty['Heading2'], fontSize=11, textColor=colors.HexColor("#1e293b"), spaceBefore=15, spaceAfter=10, fontName='Helvetica-Bold')
                p_st = ParagraphStyle('BodyText', parent=sty['Normal'], fontSize=9, textColor=colors.HexColor("#334155"), leading=13, spaceAfter=10, alignment=TA_JUSTIFY)
                
                # CABEÇALHO
                els.append(Paragraph("LAUDO EXECUTIVO DE AUDITORIA GRANULOMÉTRICA", t_st))
                els.append(Paragraph(f"<b>Gêmeo Digital:</b> {mat_sel_adv.upper()} | <b>Base Normativa:</b> ABNT NBR 7211 | <b>Data de Emissão:</b> {date.today().strftime('%d/%m/%Y')}", sub_st))
                
                # CALCULANDO KPIs GLOBAIS PARA OS CARTÕES DO PDF
                mf_global = ret_full['MF'].mean()
                if not ret_full['DMC'].empty:
                    dmc_global = ret_full['DMC'].mode()[0] if len(ret_full['DMC'].mode()) > 0 else ret_full['DMC'].mean()
                else: dmc_global = 0.0
                vol_global = sum(d['resumo']['Qtd'] for d in dados_processados)
                
                # CARTÕES KPI (Tabela colorida no topo)
                kpi_box_style = ParagraphStyle('kpi_box', alignment=TA_CENTER, textColor=colors.white, fontSize=9)
                kpi_val_style = ParagraphStyle('kpi_val', alignment=TA_CENTER, textColor=colors.white, fontSize=16, fontName='Helvetica-Bold')
                
                c1 = [Paragraph("MÓDULO DE FINURA (MÉDIO)", kpi_box_style), Paragraph(f"{mf_global:.2f}", kpi_val_style)]
                c2 = [Paragraph("DIÂMETRO MÁX. (DMC PREDOMINANTE)", kpi_box_style), Paragraph(f"{dmc_global:.1f} mm", kpi_val_style)]
                c3 = [Paragraph("VOLUME DE ENSAIOS PROCESSADOS", kpi_box_style), Paragraph(f"{vol_global} testes", kpi_val_style)]
                
                t_kpi = Table([ [c1, c2, c3] ], colWidths=[5.8*cm, 5.8*cm, 5.8*cm])
                t_kpi.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,0), colors.HexColor("#1e293b")),
                    ('BACKGROUND', (1,0), (1,0), colors.HexColor("#0f172a")),
                    ('BACKGROUND', (2,0), (2,0), colors.HexColor("#334155")),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,-1), 10),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ]))
                els.append(t_kpi)
                els.append(Spacer(1, 0.5*cm))
                
                # TEXTO DA IA / DIAGNÓSTICO
                texto_limpo = texto_dossie.replace('<b>', '<font name="Helvetica-Bold">').replace('</b>', '</font>').replace('<br/>', '<br/> ')
                els.append(Paragraph(texto_limpo, p_st))
                els.append(Spacer(1, 0.5*cm))
                
                # TABELA DE DESEMPENHO ABNT
                els.append(Paragraph("<b>4. QUADRO COMPARATIVO NBR 7211</b>", h_st))
                t_dados = [colunas_df]
                for row in tabela_final:
                    t_dados.append([row[c] for c in colunas_df])
                
                largura_total = 18*cm
                larguras = [2.5*cm, 2.5*cm, 2.5*cm]
                larg_periodo = (largura_total - 7.5*cm - 3*cm) / len(dados_processados) if dados_processados else 1*cm
                for _ in dados_processados: larguras.append(larg_periodo)
                larguras.append(3*cm)
                
                t_abnt = Table(t_dados, colWidths=larguras)
                t_abnt.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8FAFC"))
                ]))
                els.append(t_abnt)
                els.append(Spacer(1, 1*cm))
                
                # GRÁFICOS DO GÊMEO DIGITAL (GERADOS PELO MATPLOTLIB)
                els.append(Paragraph("<b>5. DASHBOARD EVOLUTIVO</b>", h_st))
                
                ret_pdf_full = pd.concat([d['df_ret'] for d in dados_processados]).sort_values("Data")
                
                plt.style.use('bmh')
                fig_a = plt.figure(figsize=(8, 7.5))
                fig_a.patch.set_facecolor('#ffffff')
                
                ax1 = fig_a.add_subplot(211)
                ax2 = fig_a.add_subplot(212)
                
                if norma_alvo and norma_alvo in LIMITES_NORMA:
                    p_n = [p for p in serie_peneiras if p in LIMITES_NORMA[norma_alvo]]
                    n_mi = [LIMITES_NORMA[norma_alvo][p][0] for p in p_n]
                    n_ma = [LIMITES_NORMA[norma_alvo][p][1] for p in p_n]
                    ax1.fill_between(p_n, n_mi, n_ma, color='#84cc16', alpha=0.15, label='Fuso Teórico ABNT NBR 7211')
                
                for d in dados_processados:
                    ax1.plot(serie_peneiras, d['df_pas'][serie_peneiras].mean().values, marker='o', linewidth=2, label=d['resumo']['Nome'])
                
                ax1.set_title('Envelope Granulométrico Contínuo (% Passante)', fontweight='bold', fontsize=9, loc='left', color='#1e293b')
                ax1.set_xlabel('Malha da Peneira (mm)', fontsize=8)
                ax1.set_ylabel('% Passante', fontsize=8)
                ax1.set_ylim([0, 105])
                ax1.invert_xaxis()
                ax1.grid(True, linestyle='--', alpha=0.6)
                ax1.legend(fontsize=7, loc='lower left')
                
                if not ret_pdf_full.empty:
                    ax2.plot(ret_pdf_full['Data'], ret_pdf_full['MF'], color='#3b82f6', marker='.', linewidth=1.5, label="Variação Módulo de Finura")
                    ax2.axhline(y=mf_global, color='#ef4444', linestyle='--', linewidth=1, label=f"Média Histórica Global ({mf_global:.2f})")
                    ax2.set_title('Cronologia Analítica de Desvios (Módulo de Finura)', fontweight='bold', fontsize=9, loc='left', color='#1e293b')
                    ax2.set_ylabel('MF (Adimensional)', fontsize=8)
                    ax2.grid(True, linestyle='--', alpha=0.6)
                    ax2.legend(fontsize=7, loc='upper left')
                    fig_a.autofmt_xdate(rotation=30)
                
                plt.tight_layout()
                img_buf_a = io.BytesIO()
                fig_a.savefig(img_buf_a, format='png', dpi=250, bbox_inches='tight')
                img_buf_a.seek(0)
                plt.close(fig_a)
                
                els.append(Image(img_buf_a, width=17*cm, height=16*cm))
                
                # RAIO-X INDIVIDUAL (NOVO) NO PDF
                els.append(Spacer(1, 0.5*cm))
                els.append(Paragraph("<b>6. RAIO-X GRANULOMÉTRICO (GÊMEOS DIGITAIS INDIVIDUAIS)</b>", h_st))
                els.append(Paragraph("Representação em cascata (simulando a pilha de peneiramento) com a retenção individualizada por intervalo de tempo, evidenciando o diâmetro máximo e mínimo efetivos.", p_st))
                
                fig_x = plt.figure(figsize=(8, 4))
                fig_x.patch.set_facecolor('#ffffff')
                
                num_plots = len(dados_processados)
                axes_x = fig_x.subplots(1, num_plots, sharey=True)
                if num_plots == 1: axes_x = [axes_x]
                
                y_pos = np.arange(len(serie_peneiras))
                
                for ax, d in zip(axes_x, dados_processados):
                    ret_m = d['df_ret'][serie_peneiras].mean()
                    act_s = ret_m[ret_m > 0.0].index.tolist()
                    d_max = max([float(x) for x in act_s]) if act_s else 0.0
                    d_min = min([float(x) for x in act_s]) if act_s else 0.0
                    
                    ax.barh(y_pos, ret_m.values, color='#3b82f6', edgecolor='black', alpha=0.8)
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels([str(s) for s in serie_peneiras], fontsize=8)
                    
                    titulo = f"{d['resumo']['Nome']}\nDmáx: {d_max} | Dmín: {d_min}"
                    ax.set_title(titulo, fontsize=8, fontweight='bold', color='#1e293b')
                    ax.set_xlabel('% Retida', fontsize=7)
                    ax.tick_params(axis='x', labelsize=7)
                    ax.grid(axis='x', linestyle='--', alpha=0.5)
                    
                    for i, v in enumerate(ret_m.values):
                        if v > 1.0:
                            ax.text(v + 0.5, i, f"{v:.1f}%", va='center', fontsize=7, color='#0f172a')
                
                axes_x[0].invert_yaxis()
                
                plt.tight_layout()
                img_buf_x = io.BytesIO()
                fig_x.savefig(img_buf_x, format='png', dpi=250, bbox_inches='tight')
                img_buf_x.seek(0)
                plt.close(fig_x)
                
                els.append(Image(img_buf_x, width=17*cm, height=8*cm))

                # ASSINATURA TÉCNICA
                els.append(Spacer(1, 1*cm))
                sig_style = ParagraphStyle('Signature', parent=sty['Normal'], alignment=TA_CENTER, fontSize=9)
                els.append(Paragraph("____________________________________________________", sig_style))
                els.append(Paragraph("<b>Davi da Silva Apolinário</b><br/>Encarregado de Fogo / LIMS Master & Developer<br/>CREA-MG 433115", sig_style))
                
                doc.build(els)
                buffer.seek(0)
                return buffer

            st.markdown("---")
            if st.button("🖨️ EMITIR LAUDO EXECUTIVO (PDF)", type="primary", use_container_width=True):
                with st.spinner("O algoritmo estrutural está compilando diagnósticos operacionais, renderizando o Gêmeo Digital e as normativas da ABNT. Aguarde..."):
                    nome_arquivo = f"Laudo_DigitalTwin_{mat_sel_adv.replace(' ', '_')}.pdf"
                    st.download_button(
                        label="📥 Descarregar Laudo Técnico e Plano de Ação", 
                        data=gerar_pdf_academico(), 
                        file_name=nome_arquivo, 
                        mime="application/pdf"
                    )

# =========================================================
# ABA 8: RADAR DE PERFORMANCE & CONCRETO 4D (STITCH UI)
# =========================================================
with tab8:
    st.markdown("### GranCon Enterprise (Mockup Stitch UI)")
    
    col_inp, col_sim = st.columns([1, 1.5])
    
    with col_inp:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### ⚗️ Traço e Moldagem (Clima & FEA)")
        cimento = st.slider("CIMENTO (KG/M³)", 200, 500, 350)
        agua = st.slider("ÁGUA (L/M³)", 100, 250, 180)
        st.markdown(f"<div style='background:#161b22; padding:10px; border-radius:8px; display:flex; justify-content:space-between; margin: 15px 0;'><span>Relação A/C Preditiva</span> <b style='color:#58a6ff;'>{(agua/cimento):.2f}</b></div>", unsafe_allow_html=True)
        slump = st.slider("ABATIMENTO / SLUMP", 40, 220, 120, format="%d mm")
        
        c_w1, c_w2 = st.columns(2)
        c_w1.markdown("<div style='background:#161b22; padding:10px; border-radius:8px; text-align:center;'><span style='color:#d29922;'>🌡️ Temp. Ambiente</span><br><b>28.4 °C</b></div>", unsafe_allow_html=True)
        c_w2.markdown("<div style='background:#161b22; padding:10px; border-radius:8px; text-align:center;'><span style='color:#58a6ff;'>💨 Umidade Rel.</span><br><b>64%</b></div>", unsafe_allow_html=True)
        
        st.write("")
        st.button("☁️ ENVIAR CONCRETO PARA A NUVEM", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_sim:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        c_t1, c_t2 = st.columns([2, 1])
        c_t1.markdown("#### 🔄 Simulação FEA 4D Cura")
        c_t2.markdown("<div style='text-align:right;'><span class='metric-label'>T_max Preditiva</span><br><span class='metric-value' style='color:#ff7b72;'>68.2 °C</span></div>", unsafe_allow_html=True)
        
        # Simulação de um Cilindro 3D Térmico via Plotly Surface
        z = np.linspace(0, 1, 50)
        theta = np.linspace(0, 2*np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x = np.cos(theta_grid)
        y = np.sin(theta_grid)
        temp = 20 + 50 * np.exp(-((z_grid - 0.5)**2) / 0.1) 
        
        fig_cyl = go.Figure(data=[go.Surface(x=x, y=y, z=z_grid, surfacecolor=temp, colorscale='Turbo', showscale=False)])
        fig_cyl.update_layout(
            scene=dict(
                xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                camera=dict(eye=dict(x=1.5, y=1.5, z=0.5))
            ),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, b=0, t=0), height=350
        )
        st.plotly_chart(fig_cyl, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='card' style='max-width: 800px; margin: 0 auto;'>", unsafe_allow_html=True)
    st.markdown("#### 🎯 Radar de Performance")
    
    categories = ['Resistência', 'Trabalhabilidade', 'Custo', 'Durabilidade', 'Coesão']
    fig_radar = go.Figure()

    fig_radar.add_trace(go.Scatterpolar(
        r=[8.5, 7.0, 6.5, 9.0, 8.0],
        theta=categories,
        fill='toself',
        fillcolor='rgba(46, 160, 67, 0.2)',
        line=dict(color='#2ea043', width=3),
        name='Traço Atual'
    ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], gridcolor='#30363d', linecolor='rgba(0,0,0,0)', tickfont=dict(color='#8b949e')),
            angularaxis=dict(gridcolor='#30363d', linecolor='rgba(0,0,0,0)', tickfont=dict(color='#c9d1d9', size=14)),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=450,
        margin=dict(t=40, b=40, l=40, r=40)
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
 
