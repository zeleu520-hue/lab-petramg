import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import io
import re
from datetime import datetime
import matplotlib
matplotlib.use('Agg') # Evita avisos do matplotlib rodando em servidores web
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from supabase import create_client, Client

# =========================================================
# 1. CONFIGURAÇÃO DA PÁGINA E SUPABASE
# =========================================================
st.set_page_config(page_title="GRANCON | LIMS Master", layout="wide", initial_sidebar_state="collapsed")

# ATENÇÃO: Insira a sua chave real abaixo!
SUPABASE_URL = "https://udpotarucqkpxpockinb.supabase.co"
SUPABASE_KEY = ""eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVkcG90YXJ1Y3FrcHhwb2NraW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMzNDM0ODQsImV4cCI6MjEwODkxOTQ4NH0.FwQDupgQmPQ4PYCC8Hrlw3a2gmosW6eCZxdgddtQy6c" " 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# 2. MEGA INJEÇÃO DE CSS (TRANSFORMA O STREAMLIT NO LIMS MASTER)
# =========================================================
st.markdown("""
    <style>
    .stApp { background-color: #1a1a24; }
    header { visibility: hidden; }
    .stMarkdown, .stText, p, label { color: #e2e8f0 !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #94a3b8 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase;
        font-weight: 600;
        border: none !important;
        padding-bottom: 10px !important;
    }
    button[aria-selected="true"] {
        color: #84cc16 !important;
        border-bottom: 3px solid #84cc16 !important;
    }
    
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        background-color: #1f2937 !important;
        border: 1px solid #3f3f46 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: #84cc16 !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    
    div[data-baseweb="popover"] ul, ul[role="listbox"] {
        background-color: #0f172a !important;
        border: 1px solid #3f3f46 !important;
    }
    ul[role="listbox"] li { color: #ffffff !important; font-size: 15px !important; }
    ul[role="listbox"] li:hover { background-color: #0284c7 !important; color: #ffffff !important; }
    
    button[kind="primary"] {
        background-color: #84cc16 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border: none !important;
        border-radius: 6px !important;
    }
    button[kind="primary"]:hover { background-color: #65a30d !important; }
    
    button[kind="secondary"] {
        background-color: #272733 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4b5563 !important;
        border-radius: 6px !important;
    }
    button[kind="secondary"]:hover {
        border-color: #84cc16 !important;
        color: #84cc16 !important;
    }
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
# 3. MOTOR DE GERAÇÃO DE PDF
# =========================================================
def gerar_pdf_moderno(dados_ensaio):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), alignment=1, spaceAfter=12)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=10, alignment=4, spaceAfter=8, leading=14)

    elements.append(Paragraph("LAUDO TÉCNICO DE CARACTERIZAÇÃO DE AGREGADOS", title_style))
    elements.append(Spacer(1, 0.5*cm))

    nome_amostra = dados_ensaio.get('nome_ensaio', 'N/A').split('|')[0].strip()
    info_data = [
        ["Empresa:", "PETRA AGREGADOS", "Data do Ensaio:", dados_ensaio.get('data_ensaio', '')],
        ["Amostra:", nome_amostra, "Responsável Técnico:", "Davi da Silva Apolinário"],
        ["Método Normativo:", "ABNT NBR NM 248:2003 / NBR 7211", "CREA-MG:", "433115"]
    ]
    t_info = Table(info_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 4.5*cm])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#2D3748")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0"))
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 0.5*cm))

    peneiras_dict = json.loads(dados_ensaio.get('dados_peneiramento', '{}'))
    peneiras = list(peneiras_dict.keys())
    massas = [float(v) for v in peneiras_dict.values()]
    massa_total = sum(massas) if sum(massas) > 0 else 1
    
    retidas = [(m / massa_total) * 100 for m in massas]
    acumuladas = []
    acumulado_atual = 0
    for r in retidas:
        acumulado_atual += r
        acumuladas.append(acumulado_atual)

    elements.append(Paragraph("1. Resultados Analíticos", subtitle_style))
    data = [['Peneiras (mm)', 'Massa Média (g)', '% Retida Simples', '% Retida Acumulada']]
    for i in range(len(peneiras)):
        data.append([peneiras[i], f"{massas[i]:.2f}", f"{retidas[i]:.2f}", f"{acumuladas[i]:.2f}"])
    
    data.append(['Massa Total', f"{massa_total:.2f}", '100.00', '-'])
    t_data = Table(data, colWidths=[4*cm, 4*cm, 4.5*cm, 4.5*cm])
    t_data.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#EDF2F7")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#E2E8F0")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#A0AEC0"))
    ]))
    elements.append(t_data)
    elements.append(Spacer(1, 0.5*cm))

    plt.figure(figsize=(5, 3.5))
    plt.bar(peneiras, retidas, color='skyblue', edgecolor='black')
    plt.xlabel('Peneiras (mm)')
    plt.ylabel('% Retida')
    plt.title('Histograma da Distribuição', fontsize=10)
    hist_img = io.BytesIO()
    plt.savefig(hist_img, format='png', bbox_inches='tight', dpi=150)
    hist_img.seek(0)
    plt.close()

    plt.figure(figsize=(5, 3.5))
    plt.plot(peneiras, acumuladas, marker='o', linestyle='-', color='red', linewidth=2)
    plt.xlabel('Peneiras (mm)')
    plt.ylabel('% Retida Acumulada')
    plt.title('Curva Granulométrica', fontsize=10)
    plt.ylim(0, 105)
    line_img = io.BytesIO()
    plt.savefig(line_img, format='png', bbox_inches='tight', dpi=150)
    line_img.seek(0)
    plt.close()

    elements.append(Paragraph("2. Representação Gráfica", subtitle_style))
    graph_table = Table([[Image(hist_img, width=7.5*cm, height=5*cm), Image(line_img, width=7.5*cm, height=5*cm)]])
    graph_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    elements.append(graph_table)
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph("3. Avaliação Técnica e Comentários", subtitle_style))
    mf = dados_ensaio.get('modulo_finura', 0)
    dmc = dados_ensaio.get('dmc_mm', 0)
    tipo = dados_ensaio.get('tipo_agregado', 'Material')
    
    comentario = f"A amostra analisada ({tipo}) apresentou Módulo de Finura de {mf} e Dimensão Máxima Característica (DMC) de {dmc} mm. A curva granulométrica obtida permite a avaliação do enquadramento do material nas zonas de utilização estabelecidas pela norma ABNT NBR 7211. A distribuição contínua das partículas otimiza o empacotamento do agregado, fator essencial para a trabalhabilidade e resistência mecânica de matrizes cimentícias."
    elements.append(Paragraph(comentario, body_style))
    elements.append(Spacer(1, 2*cm))

    sig_style = ParagraphStyle('Signature', parent=styles['Normal'], alignment=1, fontSize=10)
    elements.append(Paragraph("____________________________________________________", sig_style))
    elements.append(Paragraph("<b>Davi da Silva Apolinário</b><br/>Encarregado de Fogo / Responsável Técnico<br/>CREA-MG 433115", sig_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================================================
# 4. INICIALIZAÇÃO DE ESTADOS E ABAS
# =========================================================
PENEIRAS_NORMA = ["75", "63", "50", "37.5", "31.5", "25", "19", "12.5", "9.5", "6.3", "4.75", "2.36", "1.18", "0.6", "0.3", "0.15", "0.075", "fundo"]

if 'peneiras_ativas' not in st.session_state:
    st.session_state.peneiras_ativas = []
if 'massas_retidas' not in st.session_state:
    st.session_state.massas_retidas = {}

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🪨 Granulometria", 
    "🏗️ Concreto", 
    "🧪 Corpos de Prova", 
    "📊 Painel Analítico", 
    "📄 Emissão de Laudos"
])

# --- ABA 1: GRANULOMETRIA ---
with tab1:
    st.header("Lançamento de Granulometria")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a: nome_ensaio = st.text_input("Nome da Amostra:")
    with col_b: tipo_agregado = st.selectbox("Tipo de Material:", ["Areia de Rio Média", "Areia Especial para Concreto", "Brita #0", "Brita #1", "Bica Corrida"])
    with col_c: data_ensaio = st.date_input("Data do Ensaio:")

    st.markdown("---")
    st.markdown("### Seleção Dinâmica de Peneiras")
    
    col_sel, col_btn = st.columns([4, 1])
    with col_sel:
        opcoes_disponiveis = [p for p in PENEIRAS_NORMA if p not in st.session_state.peneiras_ativas]
        peneira_escolhida = st.selectbox("Adicione uma Peneira (Norma ABNT):", options=opcoes_disponiveis, format_func=lambda x: f"{x} mm" if x != "fundo" else "Fundo")
    with col_btn:
        st.write(""); st.write("")
        if st.button("➕ Adicionar", use_container_width=True):
            if peneira_escolhida:
                st.session_state.peneiras_ativas.append(peneira_escolhida)
                st.session_state.massas_retidas[peneira_escolhida] = 0.0
                st.rerun()

    st.markdown("---")
    st.markdown("### Massas Retidas (g)")

    if not st.session_state.peneiras_ativas:
        st.info("Nenhuma peneira adicionada. Selecione as peneiras acima para montar o ensaio.")
    else:
        peneiras_ordenadas = sorted(st.session_state.peneiras_ativas, key=lambda x: PENEIRAS_NORMA.index(x))
        for pen in peneiras_ordenadas:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                label = f"{pen} mm" if pen != "fundo" else "Fundo"
                st.markdown(f"<p style='margin-top: 10px; font-weight: bold; color: #84cc16;'>{label}</p>", unsafe_allow_html=True)
            with c2:
                st.session_state.massas_retidas[pen] = st.number_input(f"Massa para {pen}", min_value=0.0, value=float(st.session_state.massas_retidas.get(pen, 0.0)), step=0.1, key=f"massa_{pen}", label_visibility="collapsed")
            with c3:
                if st.button("🗑️ Remover", key=f"del_{pen}"):
                    st.session_state.peneiras_ativas.remove(pen)
                    del st.session_state.massas_retidas[pen]
                    st.rerun()

        st.markdown("---")
        massa_esp = st.number_input("Massa Específica (g/cm³)", min_value=0.00, value=2.65, step=0.01)

        if st.button("💾 Salvar Ensaio de Granulometria", type="primary", use_container_width=True):
            if nome_ensaio and st.session_state.massas_retidas:
                massa_total = sum(st.session_state.massas_retidas.values())
                dados = {
                    "id_ensaio": f"MANUAL-{datetime.now().strftime('%y%m%d%H%M%S')}",
                    "data_ensaio": str(data_ensaio),
                    "nome_ensaio": nome_ensaio,
                    "tipo_agregado": tipo_agregado,
                    "massa_total_g": massa_total,
                    "modulo_finura": 0.0, 
                    "dmc_mm": 0.0,        
                    "massa_especifica_g_cm3": massa_esp,
                    "dados_peneiramento": json.dumps(st.session_state.massas_retidas)
                }
                try:
                    supabase.table("ensaios_granulometria").insert(dados).execute()
                    st.success("✅ Ensaio salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha o nome da amostra e adicione massas nas peneiras.")

# --- ABA 2: CONCRETO ---
with tab2:
    st.header("Dosagem e Controle Tecnológico de Concreto")
    st.markdown("#### 1. Identificação da Mistura")
    col1, col2, col3, col4 = st.columns(4)
    with col1: tipo_material_conc = st.text_input("Material / Referência:", value="AREIA PETRA")
    with col2: tipo_traco = st.selectbox("Tipo de Traço:", ["Traço Rico", "Traço Médio", "Traço Pobre"])
    with col3: traco_proporcao = st.text_input("Traço em Massa (1:Ar:Br):", placeholder="Ex: 1 : 3,5 : 2,250")
    with col4: data_moldagem_conc = st.date_input("Data de Moldagem:")

    st.divider()
    st.markdown("#### 2. Massas dos Materiais (kg)")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: cim_kg = st.number_input("Cimento (kg)", min_value=0.0, step=0.1, format="%.2f")
    with c2: agr_m1_kg = st.number_input("Agr. Miúdo 1 (kg)", min_value=0.0, step=0.1, format="%.2f")
    with c3: agr_m2_kg = st.number_input("Agr. Miúdo 2 (kg)", min_value=0.0, step=0.1, format="%.2f")
    with c4: brita1_kg = st.number_input("Brita 1 (kg)", min_value=0.0, step=0.1, format="%.2f")
    with c5: agua_kg = st.number_input("Água (kg)", min_value=0.0, step=0.1, format="%.2f")

    st.divider()
    st.markdown("#### 3. Propriedades e Consumo (por m³)")
    c6, c7, c8, c9, c10 = st.columns(5)
    with c6: teor_argamassa = st.number_input("Teor Argamassa (%)", min_value=0.0, step=0.1, format="%.2f")
    with c7: abatimento = st.number_input("Abatimento (mm)", min_value=0.0, step=1.0, format="%.2f")
    with c8: massa_esp_conc = st.number_input("Massa Espec. (kg/m³)", min_value=0.0, step=1.0, format="%.2f")
    with c9: consumo_cim = st.number_input("Consumo Cim. (kg/m³)", min_value=0.0, step=1.0, format="%.2f")
    with c10: relacao_ac = st.number_input("Relação Água/Cimento", min_value=0.00, step=0.01, format="%.2f")

    st.divider()
    st.markdown("#### 4. Resistência à Compressão aos 28 dias (MPa)")
    num_cps = st.number_input("Número de Corpos-de-Prova", min_value=1, max_value=12, value=6, step=1)
    
    cp_cols = st.columns(6)
    resistencias = []
    for i in range(int(num_cps)):
        with cp_cols[i % 6]:
            res = st.number_input(f"CP {i+1} (MPa)", min_value=0.0, step=0.1, key=f"cp_{i}")
            resistencias.append(res)
    
    media_mpa = sum(resistencias) / len(resistencias) if resistencias else 0.0
    st.info(f"**Resistência Média Calculada:** {media_mpa:.2f} MPa")

    st.write("")
    if st.button("💾 Salvar Ensaio de Concreto", type="primary", use_container_width=True):
        if tipo_material_conc and traco_proporcao:
            dados_concreto = {
                "id_ensaio": f"CONC-{datetime.now().strftime('%y%m%d%H%M%S')}",
                "data_moldagem": str(data_moldagem_conc),
                "tipo_material": tipo_material_conc,
                "tipo_traco": tipo_traco,
                "traco_proporcao": traco_proporcao,
                "teor_argamassa_perc": teor_argamassa,
                "cimento_kg": cim_kg,
                "agregado_miudo_1_kg": agr_m1_kg,
                "agregado_miudo_2_kg": agr_m2_kg,
                "brita_1_kg": brita1_kg,
                "agua_kg": agua_kg,
                "massa_especifica_kg_m3": massa_esp_conc,
                "consumo_cimento_kg_m3": consumo_cim,
                "relacao_a_c": relacao_ac,
                "abatimento_mm": abatimento,
                "num_cps": int(num_cps),
                "resistencias_individuais": json.dumps(resistencias),
                "resistencia_media_mpa": round(media_mpa, 2)
            }
            try:
                supabase.table("ensaios_concreto").upsert(dados_concreto).execute()
                st.success(f"✅ Traço '{tipo_traco}' salvo com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
        else:
            st.warning("Preencha a Referência do Material e a Proporção do Traço.")

# --- ABA 3: CORPOS DE PROVA ---
with tab3:
    st.header("Controle de Corpos de Prova (Prensa)")
    st.info("Módulo de prensagem em desenvolvimento...")

# --- ABA 4: PAINEL ANALÍTICO (FRONT-END HTML BLINDADO) ---
with tab4:
    html_dashboard = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
        <style>
            body {{ background-color: #1a1a24; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }}
            .card {{ background-color: #272733; border: 1px solid #3f3f46; border-radius: 8px; padding: 20px; }}
            .text-neon-green {{ color: #84cc16; }}
            .text-neon-yellow {{ color: #eab308; }}
            .bg-neon-green {{ background-color: #84cc16; }}
            .diagnostic-box {{ background: linear-gradient(145deg, #1e293b, #0f172a); border-left: 4px solid #84cc16; }}
            .input-dark, .select-dark {{ background-color: #1f2937; border: 1px solid #4b5563; color: white; border-radius: 4px; padding: 4px; }}
            .tab-btn.active {{ border-bottom: 3px solid #84cc16; color: #84cc16; font-weight: bold; }}
        </style>
    </head>
    <body class="p-6">
        <div class="flex border-b border-gray-700 mb-6 gap-8 px-4">
            <button onclick="switchTab('granulometria')" id="btn-granulometria" class="tab-btn active pb-2 text-lg uppercase tracking-wide">
                <i class="fa-solid fa-layer-group mr-2"></i> Granulometria
            </button>
            <button onclick="switchTab('concreto')" id="btn-concreto" class="tab-btn pb-2 text-lg text-gray-400 uppercase tracking-wide">
                <i class="fa-solid fa-cube mr-2"></i> Concreto
            </button>
        </div>

        <div class="flex justify-between items-center mb-6">
            <div class="flex gap-4 items-end card py-3 px-6 w-full">
                <div>
                    <label class="block text-xs text-gray-400 mb-1">Início</label>
                    <input type="date" id="data-inicio" value="2019-01-01" class="select-dark">
                </div>
                <div>
                    <label class="block text-xs text-gray-400 mb-1">Fim</label>
                    <input type="date" id="data-fim" value="2026-12-31" class="select-dark">
                </div>
                <div>
                    <label class="block text-xs text-gray-400 mb-1">Filtro de Material</label>
                    <select id="filtro-rocha" class="select-dark">
                        <option value="Todos">Todos</option>
                        <option value="Areia Especial para Concreto">Areia Especial para Concreto</option>
                        <option value="Areia de Rio Média">Areia de Rio Média</option>
                        <option value="Brita #1">Brita #1</option>
                        <option value="Brita #0">Brita #0</option>
                        <option value="Bica Corrida">Bica Corrida</option>
                    </select>
                </div>
                <button onclick="carregarDadosDoSupabase()" class="bg-neon-green text-black font-bold px-4 py-2 rounded hover:bg-lime-400">Buscar Dados <span id="status-db"></span></button>
            </div>
        </div>

        <!-- ABA HTML GRANULOMETRIA -->
        <div id="tab-granulometria">
            <div class="grid grid-cols-4 gap-4 mb-6">
                <div class="card border-l-4 border-neon-green"><p class="text-xs text-gray-400 font-bold">Último Lote</p><p id="kpi-g-nome" class="text-lg font-black text-white mt-1">-</p></div>
                <div class="card"><p class="text-xs text-gray-400 font-bold">Material Predominante</p><p id="kpi-g-mat" class="text-lg font-black text-white mt-1">-</p></div>
                <div class="card"><p class="text-xs text-gray-400 font-bold">Módulo de Finura</p><p id="kpi-g-mf" class="text-2xl font-black text-white mt-1">-</p></div>
                <div class="card"><p class="text-xs text-gray-400 font-bold">DMC</p><p id="kpi-g-dmc" class="text-2xl font-black text-white mt-1">- <span class="text-sm">mm</span></p></div>
            </div>

            <div class="grid grid-cols-2 gap-6">
                <div class="card"><h3 class="text-sm font-bold mb-4">Curva NBR 7211</h3><div class="h-64"><canvas id="chartCurvaNbr"></canvas></div></div>
                <div class="card diagnostic-box p-6"><h4 class="font-bold mb-4 text-white text-lg"><i class="fa-solid fa-file-signature text-neon-green mr-2"></i> Diagnóstico Normativo</h4>
                <p id="diag-finura" class="text-sm text-gray-300">Aguardando busca de dados...</p></div>
            </div>
        </div>

        <!-- ABA HTML CONCRETO -->
        <div id="tab-concreto" class="hidden">
            <div class="grid grid-cols-6 gap-4 mb-6">
                <div class="card border-l-4 border-neon-yellow"><p class="text-xs text-gray-400 font-bold">Lote Base</p><p id="kpi-c-traco" class="text-sm font-black text-white mt-1">-</p></div>
                <div class="card"><p class="text-xs text-gray-400 font-bold">Slump (mm)</p><p id="kpi-c-slump" class="text-2xl font-black text-neon-green mt-1">-</p></div>
                <div class="card"><p class="text-xs text-gray-400 font-bold">Rel A/C</p><p id="kpi-c-ac" class="text-2xl font-black text-white mt-1">-</p></div>
                <div class="card"><p class="text-xs text-gray-400 font-bold">Num CPs</p><p id="kpi-c-cps" class="text-2xl font-black text-white mt-1">-</p></div>
                <div class="card"><p class="text-xs text-gray-400 font-bold">Material</p><p id="kpi-c-rocha" class="text-sm font-black text-white mt-1">-</p></div>
                <div class="card"><p class="text-xs text-gray-400 font-bold">Cons. Cimento</p><p id="kpi-c-consumo" class="text-2xl font-black text-white mt-1">-</p></div>
            </div>
            <div class="grid grid-cols-2 gap-6">
                <div class="card"><h3 class="text-sm font-bold mb-4">Evolução Fck (MPa)</h3><div class="h-64"><canvas id="chartFck"></canvas></div></div>
                <div class="card"><h3 class="text-sm font-bold mb-4">Proporção Mix</h3><div class="h-64"><canvas id="chartMix"></canvas></div></div>
            </div>
        </div>

        <script>
            // Recebe chaves do Python dinamicamente
            const supabaseUrl = "{SUPABASE_URL}";
            const supabaseKey = "{SUPABASE_KEY}";
            const supabase = window.supabase.createClient(supabaseUrl, supabaseKey);
            
            function switchTab(tab) {{
                document.getElementById('tab-granulometria').classList.add('hidden');
                document.getElementById('tab-concreto').classList.add('hidden');
                document.getElementById('btn-granulometria').classList.remove('active', 'text-gray-400');
                document.getElementById('btn-concreto').classList.remove('active', 'text-gray-400');
                
                if(tab === 'granulometria') {{
                    document.getElementById('tab-granulometria').classList.remove('hidden');
                    document.getElementById('btn-granulometria').classList.add('active');
                    document.getElementById('btn-concreto').classList.add('text-gray-400');
                }} else {{
                    document.getElementById('tab-concreto').classList.remove('hidden');
                    document.getElementById('btn-concreto').classList.add('active');
                    document.getElementById('btn-granulometria').classList.add('text-gray-400');
                }}
            }}

            Chart.defaults.color = '#94a3b8';
            let chartGran = new Chart(document.getElementById('chartCurvaNbr').getContext('2d'), {{
                type: 'line',
                data: {{ labels: ['1.18', '2.36', '4.75', '6.3', '9.5', '12.5', '19', '25'], datasets: [
                    {{ label: 'Amostra DB (Acumulada %)', data: [0,0,0,0,0,0,0,0], borderColor: '#84cc16', tension: 0.4 }}
                ]}}, options: {{ responsive: true, maintainAspectRatio: false }}
            }});
            
            let chartFck = new Chart(document.getElementById('chartFck').getContext('2d'), {{
                type: 'bar', data: {{ labels: [], datasets: [{{ label: 'Fck (MPa)', data: [], backgroundColor: '#84cc16' }}, {{ type: 'line', label: 'Projeto', data: [], borderColor: '#eab308' }}]}}, options: {{ responsive: true, maintainAspectRatio: false }}
            }});

            let chartMix = new Chart(document.getElementById('chartMix').getContext('2d'), {{
                type: 'doughnut', data: {{ labels: ['Cimento', 'Areia', 'Brita', 'Água'], datasets: [{{ data: [0,0,0,0], backgroundColor: ['#eab308', '#f59e0b', '#84cc16', '#3b82f6'], borderWidth: 0 }}] }}, options: {{ responsive: true, maintainAspectRatio: false }}
            }});

            async function carregarDadosDoSupabase() {{
                try {{
                    document.getElementById('status-db').innerHTML = "(Buscando...)";
                    const dI = document.getElementById('data-inicio').value;
                    const dF = document.getElementById('data-fim').value;
                    const mat = document.getElementById('filtro-rocha').value;

                    // GRANULOMETRIA
                    let qG = supabase.from('ensaios_granulometria').select('*').gte('data_ensaio', dI).lte('data_ensaio', dF);
                    if(mat !== 'Todos') qG = qG.eq('tipo_agregado', mat);
                    const {{ data: dbGran, error: errGran }} = await qG;

                    if(dbGran && dbGran.length > 0) {{
                        const u = dbGran[dbGran.length - 1];
                        document.getElementById('kpi-g-nome').innerText = u.nome_ensaio ? u.nome_ensaio.split('|')[0] : '-';
                        document.getElementById('kpi-g-mat').innerText = u.tipo_agregado || '-';
                        document.getElementById('kpi-g-mf').innerText = u.modulo_finura || '0';
                        document.getElementById('kpi-g-dmc').innerText = u.dmc_mm || '0';
                        document.getElementById('diag-finura').innerHTML = `<b>Módulo de Finura calculado:</b> ${{u.modulo_finura}}. A amostra apresenta DMC de ${{u.dmc_mm}}mm.`;

                        let pens = u.dados_peneiramento;
                        if(typeof pens === 'string') pens = JSON.parse(pens);
                        pens = pens || {{}};

                        let total = u.massa_total_g || 1;
                        let seq = ['75', '63', '50', '37.5', '31.5', '25', '19', '12.5', '9.5', '6.3', '4.75', '2.36', '1.18', '0.6', '0.3', '0.15', '0.075', 'fundo'];
                        let chavesGrafico = ['1.18', '2.36', '4.75', '6.3', '9.5', '12.5', '19', '25'];
                        let acumulado = 0; let mapaAcum = {{}};
                        
                        for(let k of seq) {{
                            let m = parseFloat(pens[k] || 0);
                            acumulado += (m/total)*100;
                            mapaAcum[k] = acumulado;
                        }}
                        
                        chartGran.data.datasets[0].data = chavesGrafico.map(k => mapaAcum[k] || 0);
                        chartGran.update();
                    }} else {{
                        document.getElementById('kpi-g-nome').innerText = "Sem dados";
                        document.getElementById('kpi-g-mat').innerText = "-";
                        document.getElementById('kpi-g-mf').innerText = "-";
                        document.getElementById('kpi-g-dmc').innerText = "-";
                        document.getElementById('diag-finura').innerText = "Nenhum resultado de granulometria para este filtro.";
                        chartGran.data.datasets[0].data = [0,0,0,0,0,0,0,0];
                        chartGran.update();
                    }}

                    // CONCRETO
                    let qC = supabase.from('ensaios_concreto').select('*').gte('data_moldagem', dI).lte('data_moldagem', dF);
                    if(mat !== 'Todos') qC = qC.eq('tipo_material', mat);
                    const {{ data: dbConc, error: errConc }} = await qC;

                    if(dbConc && dbConc.length > 0) {{
                        const uc = dbConc[dbConc.length - 1];
                        document.getElementById('kpi-c-traco').innerText = uc.tipo_traco;
                        document.getElementById('kpi-c-slump').innerText = uc.abatimento_mm || 0;
                        document.getElementById('kpi-c-ac').innerText = uc.relacao_a_c || '-';
                        document.getElementById('kpi-c-cps').innerText = uc.num_cps || '0';
                        document.getElementById('kpi-c-rocha').innerText = uc.tipo_material || '-';
                        document.getElementById('kpi-c-consumo').innerText = uc.consumo_cimento_kg_m3 || '0';
                        
                        chartMix.data.datasets[0].data = [uc.cimento_kg||0, ((uc.agregado_miudo_1_kg||0)+(uc.agregado_miudo_2_kg||0)), uc.brita_1_kg||0, uc.agua_kg||0];
                        chartMix.update();

                        chartFck.data.labels = dbConc.map(x => x.data_moldagem);
                        chartFck.data.datasets[0].data = dbConc.map(x => x.resistencia_media_mpa || 0);
                        chartFck.data.datasets[1].data = dbConc.map(x => (x.tipo_traco && x.tipo_traco.includes("Rico")) ? 30 : 25);
                        chartFck.update();
                    }} else {{
                        document.getElementById('kpi-c-traco').innerText = "Sem dados";
                        document.getElementById('kpi-c-slump').innerText = "-";
                        document.getElementById('kpi-c-ac').innerText = "-";
                        document.getElementById('kpi-c-cps').innerText = "-";
                        document.getElementById('kpi-c-rocha').innerText = "-";
                        document.getElementById('kpi-c-consumo').innerText = "-";
                        chartMix.data.datasets[0].data = [0,0,0,0];
                        chartMix.update();
                        chartFck.data.labels = []; chartFck.data.datasets[0].data = []; chartFck.data.datasets[1].data = [];
                        chartFck.update();
                    }}

                    document.getElementById('status-db').innerHTML = "(OK)";
                }} catch (e) {{ 
                    document.getElementById('status-db').innerHTML = "(Erro ao conectar - verifique o periodo)"; 
                    console.error("Erro interno no Painel:", e); 
                }}
            }}
            window.onload = carregarDadosDoSupabase;
        </script>
    </body>
    </html>
    """
    components.html(html_dashboard, height=900, scrolling=True)

# --- ABA 5: LAUDOS ---
with tab5:
    st.header("Emissão de Laudos Técnicos (PDF)")
    try:
        response = supabase.table("ensaios_granulometria").select("id_ensaio, nome_ensaio, data_ensaio").execute()
        ensaios_db = response.data
        if ensaios_db:
            opcoes_laudo = {f"{e['id_ensaio']} | {e['nome_ensaio']} ({e['data_ensaio']})": e['id_ensaio'] for e in ensaios_db}
            ensaio_selecionado = st.selectbox("Selecione o Ensaio para Gerar o Laudo:", list(opcoes_laudo.keys()))
            if st.button("🖨️ GERAR LAUDO PDF", type="primary"):
                id_alvo = opcoes_laudo[ensaio_selecionado]
                dados_completos = supabase.table("ensaios_granulometria").select("*").eq("id_ensaio", id_alvo).execute().data[0]
                st.download_button(label="📥 Clique Aqui Para Baixar Seu PDF", data=gerar_pdf_moderno(dados_completos), file_name=f"Laudo_{id_alvo}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.warning("Nenhum ensaio encontrado no banco.")
    except Exception as e:
        st.error(f"Erro ao carregar ensaios: {e}")
