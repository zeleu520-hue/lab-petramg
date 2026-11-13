import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from supabase import create_client, Client

# =========================================================
# CONFIGURAÇÃO GERAL
# =========================================================
st.set_page_config(page_title="GranCon Enterprise", layout="wide", initial_sidebar_state="collapsed")

SUPABASE_URL = "https://udpotarucqkpxpockinb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVkcG90YXJ1Y3FrcHhwb2NraW5iIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMzNDM0ODQsImV4cCI6MjEwODkxOTQ4NH0.FwQDupgQmPQ4PYCC8Hrlw3a2gmosW6eCZxdgddtQy6c" 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# ESTILIZAÇÃO CSS (BASEADA NO PROTÓTIPO STITCH)
# =========================================================
st.markdown("""
    <style>
    /* Fundo Escuro Global */
    .stApp { background-color: #17191e; color: #9aa0a6; font-family: 'Inter', sans-serif; }
    
    /* Títulos */
    h1, h2, h3 { color: #e8eaed !important; font-weight: 700 !important; }
    
    /* Cartões (Cards) */
    .stitch-card {
        background-color: #20232a;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    /* Botões e Inputs */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #2d333b !important;
        border-radius: 8px !important;
        border: 1px solid #444c56 !important;
    }
    input, .stSelectbox div { color: #c9d1d9 !important; font-weight: 500 !important; }
    
    button[kind="primary"] {
        background-color: #2ea043 !important; /* Verde Stitch */
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        border: none !important;
    }
    
    /* Métricas Especiais */
    .metric-value { font-size: 2.5rem; font-weight: 800; color: #58a6ff; line-height: 1; }
    .metric-label { font-size: 0.85rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Navegação Inferior Mock */
    .bottom-nav {
        position: fixed; bottom: 0; left: 0; right: 0;
        background-color: #161b22; border-top: 1px solid #30363d;
        display: flex; justify-content: space-around; padding: 15px 0; z-index: 999;
    }
    .nav-item { color: #8b949e; text-align: center; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
    .nav-item.active { color: #2ea043; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2>GranCon Enterprise</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Granulometria & Blend", "🧊 Concreto 4D", "🎯 Radar de Performance"])

# =========================================================
# ABA 1: GRANULOMETRIA & BLEND
# =========================================================
with tab1:
    st.markdown("### Gêmeo Digital do Agregado")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div class='stitch-card'>", unsafe_allow_html=True)
        st.markdown("<p class='metric-label'>Composição do Blend</p>", unsafe_allow_html=True)
        # Simulação do gráfico de donut para substituir a imagem da pilha de areia
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Brita 1', 'Brita 0', 'Areia'], 
            values=[42.5, 18.2, 39.3], 
            hole=.6,
            marker_colors=['#8b949e', '#58a6ff', '#d29922']
        )])
        fig_donut.update_layout(
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=250, margin=dict(t=10, b=10, l=10, r=10),
            annotations=[dict(text='100%', x=0.5, y=0.5, font_size=20, showarrow=False, font_color='white')]
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
        c_a, c_b, c_c = st.columns(3)
        c_a.markdown("<p style='color:#8b949e; font-size:0.8rem;'>Brita 1<br><b style='color:white;font-size:1.1rem;'>42.5%</b></p>", unsafe_allow_html=True)
        c_b.markdown("<p style='color:#58a6ff; font-size:0.8rem;'>Brita 0<br><b style='color:white;font-size:1.1rem;'>18.2%</b></p>", unsafe_allow_html=True)
        c_c.markdown("<p style='color:#d29922; font-size:0.8rem;'>Areia<br><b style='color:white;font-size:1.1rem;'>39.3%</b></p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='stitch-card'>", unsafe_allow_html=True)
        st.markdown("<p class='metric-label'>📈 Curva Granulométrica</p>", unsafe_allow_html=True)
        
        # Simulação da curva contínua com envelope
        x_malhas = [0.15, 0.3, 0.6, 1.18, 2.36, 4.75, 9.5, 12.5, 19.0]
        y_passante = [2, 10, 25, 45, 65, 85, 95, 100, 100]
        y_max = [10, 35, 65, 90, 100, 100, 100, 100, 100]
        y_min = [2, 10, 25, 50, 75, 90, 100, 100, 100]

        fig_curva = go.Figure()
        # Envelope Inferior/Superior
        fig_curva.add_trace(go.Scatter(x=x_malhas, y=y_max, line=dict(color='rgba(255,255,255,0)'), showlegend=False))
        fig_curva.add_trace(go.Scatter(x=x_malhas, y=y_min, fill='tonexty', fillcolor='rgba(88, 166, 255, 0.1)', line=dict(color='rgba(255,255,255,0)'), name='Envelope Normal'))
        # Curva Real
        fig_curva.add_trace(go.Scatter(x=x_malhas, y=y_passante, mode='lines+markers', line=dict(color='#58a6ff', width=4), marker=dict(size=8, color='white'), name='Mistura Real'))
        
        fig_curva.update_layout(
            xaxis_type="log", xaxis_title="Malha (mm) log", yaxis_title="% Passante",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#8b949e'),
            height=300, margin=dict(t=10, b=10, l=10, r=10), showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='#30363d'), yaxis=dict(showgrid=True, gridcolor='#30363d')
        )
        st.plotly_chart(fig_curva, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ABA 2: CONCRETO 4D
# =========================================================
with tab2:
    st.markdown("### Concreto & Clima")
    st.markdown("<p style='color:#8b949e;'>Modelagem Preditiva Termo-Mecânica</p>", unsafe_allow_html=True)
    
    col_inp, col_sim = st.columns([1, 1.5])
    
    with col_inp:
        st.markdown("<div class='stitch-card'>", unsafe_allow_html=True)
        st.markdown("#### ⚗️ Traço e Moldagem")
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
        st.markdown("<div class='stitch-card'>", unsafe_allow_html=True)
        c_t1, c_t2 = st.columns([2, 1])
        c_t1.markdown("#### 🔄 Simulação FEA 4D Cura")
        c_t2.markdown("<div style='text-align:right;'><span class='metric-label'>T_max Preditiva</span><br><span class='metric-value' style='color:#ff7b72;'>68.2 °C</span></div>", unsafe_allow_html=True)
        
        # Simulação de um Cilindro 3D Térmico via Plotly Surface
        z = np.linspace(0, 1, 50)
        theta = np.linspace(0, 2*np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x = np.cos(theta_grid)
        y = np.sin(theta_grid)
        # Gradiente de temperatura simulado
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

# =========================================================
# ABA 3: RADAR DE PERFORMANCE
# =========================================================
with tab3:
    st.markdown("<div class='stitch-card' style='max-width: 800px; margin: 0 auto;'>", unsafe_allow_html=True)
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
    
