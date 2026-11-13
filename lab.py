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
# 3. CSS GLOBAL
# =========================================================
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
    header { visibility: hidden; }
    h1, h2, h3, h4 { color: #f8fafc !important; font-weight: 800 !important; }
    .destaque-verde { color: #84cc16; }
    .card { background-color: #1e293b; padding: 25px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px; border-top: 4px solid #84cc16; }
    .parecer-tecnico { background-color: #1e293b; color: #e2e8f0; padding: 25px; border-radius: 8px; border-left: 6px solid #3b82f6; font-size: 1.10rem; line-height: 1.7; }
    
    button[data-baseweb="tab"] { background-color: transparent !important; color: #94a3b8 !important; font-size: 1rem !important; text-transform: uppercase; font-weight: 600; border: none !important; padding-bottom: 10px !important; }
    button[aria-selected="true"] { color: #84cc16 !important; border-bottom: 3px solid #84cc16 !important; }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] { background-color: #1f2937 !important; border: 1px solid #3f3f46 !important; border-radius: 6px !important; }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within { border-color: #84cc16 !important; }
    div[data-baseweb="input"] input { color: #ffffff !important; font-weight: bold !important; font-size: 16px !important; }
    button[kind="primary"] { background-color: #84cc16 !important; color: #000000 !important; font-weight: 900 !important; border: none !important; border-radius: 6px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='margin-top: -50px; margin-bottom: 30px;'>
        <h1 style='font-size: 2.5rem; font-weight: 900; letter-spacing: 2px; margin-bottom: 0;'>
            <span style='color: #84cc16;'>GRAN</span><span style='color: #eab308;'>CON</span>
        </h1>
        <p style='color: #94a3b8; font-size: 0.9rem; margin-top: -10px;'>DSA SOLUÇÕES | LIMS MASTER</p>
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
# 5. GERADOR DE LAUDO SIMPLES (ABAS 1 a 6)
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
# 7. AS 7 ABAS DO SISTEMA
# =========================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🪨 Granulometria", "🏗️ Concreto", "📈 Auditoria Simples", 
    "🧪 Prensagem & QR", "📊 Painel Analítico", "📄 Laudos", 
    "🧠 Inteligência (Gêmeo Digital)"
])

# --- ABA 1: GRANULOMETRIA ---
with tab1:
    st.header("Lançamento de Granulometria")
    c_a, c_b, c_c, c_d = st.columns(4)
    with c_a: nome_ensaio = st.text_input("Nome da Amostra:")
    with c_b: tipo_agregado = st.selectbox("Tipo de Material:", ["Areia Especial para Concreto", "Areia Industrial Média", "Areia Industrial Fina", "Areia Industrial Fina Plus", "Brita #0", "Brita #1", "Bica Corrida"])
    with c_c: cliente_dest = st.text_input("Cliente/Destino:", placeholder="Ex: Construtora X")
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
            with c1: st.markdown(f"<p style='margin-top: 10px; font-weight: bold; color: #84cc16;'>{pen} mm</p>", unsafe_allow_html=True)
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

            dados = { "id_ensaio": f"GRAN-{datetime.now().strftime('%y%m%d%H%M%S')}", "data_ensaio": str(data_ensaio), "nome_ensaio": nome_ensaio, "tipo_agregado": tipo_agregado, "cliente_destino": cliente_dest, "massa_total_g": total_massa, "modulo_finura": round(mf_calc, 2), "dmc_mm": float(dmc_calc), "massa_especifica_g_cm3": massa_esp, "dados_peneiramento": json.dumps(pens) }
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
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(f'https://grancon-lab.com/rompimento?id={id_conc}')}&bgcolor=84cc16"
            st.image(qr_url, width=200)
        except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3, 4, 5, 6: (Mantidas Simples) ---
with tab3: st.info("Utilize a Guia '🧠 Inteligência (Gêmeo Digital)' para análises avançadas.")
with tab4: st.info("Módulo em desenvolvimento.")
with tab5: st.info("Consulte a Guia '🧠 Inteligência (Gêmeo Digital)' para os novos KPIs e Dashboards.")
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
                
                if st.button("🗑️ Excluir", key=f"del_per_{periodo['id']}", help="Remover este intervalo da análise"):
                    ids_para_remover.append(periodo['id'])
                else:
                    periodo['ini'] = d_ini
                    periodo['fim'] = d_fim
                    nome_intervalo = f"{d_ini.strftime('%d/%m/%Y')} - {d_fim.strftime('%d/%m/%Y')}"
                    periodos_validados.append({"nome": nome_intervalo, "ini": d_ini, "fim": d_fim})

        if ids_para_rem
