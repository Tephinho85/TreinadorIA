import json
import os
import random
import urllib.parse
from datetime import datetime
from io import BytesIO

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Treinador IA - Modo Monstro",
    page_icon="💀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA (PREMIUM HARDCORE) ---
st.markdown("""
    <style>
    /* Fundo geral escuro e elegante */
    .stApp {
        background-color: #080808;
        color: #d1d1d1;
    }
    
    /* Sidebar refinada */
    [data-testid="stSidebar"] {
        background-color: #0f0f0f;
        border-right: 1px solid #260000;
    }
    
    /* Botões de Ação Principais */
    .stButton>button {
        background: linear-gradient(135deg, #8b0000 0%, #dc143c 100%);
        color: white;
        font-weight: 800;
        letter-spacing: 1px;
        border: 1px solid #ff3333;
        border-radius: 4px;
        padding: 0.6rem 1.5rem;
        box-shadow: 0 4px 15px rgba(220, 20, 60, 0.2);
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #dc143c 0%, #ff3333 100%);
        box-shadow: 0 0 20px rgba(220, 20, 60, 0.6);
        transform: translateY(-2px);
        border-color: #ff6666;
    }
    
    /* Botão de Download PDF */
    [data-testid="stDownloadButton"]>button {
        background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
        color: #ff4d4d;
        font-weight: 800;
        border: 1px solid #4d0000;
        border-radius: 4px;
    }
    [data-testid="stDownloadButton"]>button:hover {
        background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
        border-color: #ff4d4d;
        color: white;
    }
    
    /* Cartões de Métricas */
    [data-testid="stMetric"] {
        background-color: #121212;
        border: 1px solid #2a0000;
        border-left: 4px solid #dc143c;
        padding: 15px 20px;
        border-radius: 6px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }
    [data-testid="stMetricLabel"] {
        color: #888888 !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 900;
        font-size: 1.8rem;
    }
    
    /* Abas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: transparent;
        padding-bottom: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        border-bottom: 2px solid #333333;
        color: #777777;
        font-weight: 700;
        padding: 12px 20px;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: #dc143c !important;
        border-bottom: 2px solid #dc143c !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #121212 !important;
        border: 1px solid #222222;
        border-radius: 4px;
        color: #dddddd !important;
        font-weight: 600;
    }
    
    /* Caixas de Alerta/Info */
    .stAlert {
        background-color: #121212;
        border: 1px solid #2a2a2a;
        color: #cccccc;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES E DADOS ---
META_OPCOES = ["Crescimento", "Emagrecimento", "Manutenção do Peso"]
EXPERIENCIA_OPCOES = ["Básico", "Intermediário", "Avançado"]
DIETA_OPCOES = [
    "Equilibrada (padrão)",
    "Crescimento (Hipercalórica)",
    "Emagrecimento (Hipocalórica)",
    "Cetogênica",
    "Low Carb",
]

NIVEIS_ATIVIDADE_MULTIPLICADORES = {
    "Sedentário (escritório, pouco movimento)": 1.2,
    "Levemente ativo (caminhadas leves, trabalho com algum movimento)": 1.375,
    "Moderadamente ativo (trabalho físico leve, exercícios 2-3x/sem)": 1.55,
    "Muito ativo (trabalho físico pesado, exercícios 4-5x/sem)": 1.725,
    "Extremamente ativo (atleta, trabalho físico intenso + treinos diários)": 1.9,
}

ARQUIVO_TREINOS = "treinos_salvos.json"

EXERCICIOS = {
    "Peito": {
        "Básico": ["Supino reto com barra (4x8-12)", "Supino com halteres (3x10-12)", "Flexão de braço (3x12-15)", "Crucifixo (3x12-15)", "Supino inclinado com barra (3x8-12)"],
        "Intermediário": ["Supino inclinado com halteres (4x8-12)", "Crucifixo inclinado (3x10-12)", "Peck deck (3x12-15)", "Supino declinado (3x8-12)", "Crossover (3x12-15)", "Supino com pegada fechada (3x10-12)"],
        "Avançado": ["Supino declinado com halteres (4x6-10)", "Crossover com variação de alturas (4x10-12)", "Supino com pegada fechada (4x8-10)", "Pullover com halteres (3x10-12)", "Supino com bandas elásticas (3x6-8)", "Dips com peso (3x8-12)", "Supino spoto (3x5-8)"],
    },
    "Costas": {
        "Básico": ["Remada curvada (4x8-12)", "Puxada alta (3x10-12)", "Pull-down (3x12-15)", "Remada sentado (3x10-12)", "Hiperextensão (3x12-15)"],
        "Intermediário": ["Barra fixa (4x6-10)", "Remada cavalinho (3x8-12)", "Pull-over (3x10-12)", "Remada unilateral com halteres (3x10-12 cada lado)", "Puxada frontal (3x10-12)", "Deadlift (Levantamento Terra) (3x8-10)"],
        "Avançado": ["Remada unilateral com barra T ou haltere pesado (4x8-10 cada lado)", "Puxada frontal com pegada pronada (4x8-10)", "Deadlift (Levantamento Terra) (4x5-8)", "Pull-up com peso (3x6-8)", "Remada T-bar (3x8-10)", "Pulldown com corda atrás da cabeça (3x10-12)", "Remada invertida com peso (3x10-12)"],
    },
    "Pernas": {
        "Básico": ["Agachamento livre (4x8-12)", "Leg press (3x10-12)", "Cadeira extensora (3x12-15)", "Mesa flexora (3x10-12)", "Panturrilha em pé (3x15-20)"],
        "Intermediário": ["Agachamento frontal (4x8-10)", "Avanço com halteres (3x10-12 cada perna)", "Stiff (Levantamento Terra Romeno) (3x8-12)", "Leg press unilateral (3x10-12 cada perna)", "Cadeira flexora (3x10-12)", "Panturrilha sentado (3x15-20)", "Elevação pélvica (Hip Thrust) (3x10-15)"],
        "Avançado": ["Agachamento sumô com barra (4x6-10)", "Levantamento Terra Romeno (RDL) (4x8-10)", "Panturrilha no leg press (4x15-20)", "Bulgarian split squat (Agachamento Búlgaro) (3x8-10 cada perna)", "Hack squat (3x8-10)", "Good morning (3x8-10)", "Extensão de perna unilateral (3x10-12 cada perna)", "Flexora nórdica (Nordic Hamstring Curl) (3x falha)"],
    },
    "Ombros": {
        "Básico": ["Desenvolvimento com halteres (4x8-12)", "Elevação lateral (3x10-12)", "Remada alta com barra ou halteres (3x10-12)", "Elevação frontal com halteres (3x10-12)", "Crucifixo inverso com halteres (3x12-15)"],
        "Intermediário": ["Desenvolvimento militar com barra (em pé) (4x8-10)", "Elevação lateral inclinada no banco (3x10-12)", "Elevação frontal com barra (3x8-12)", "Crucifixo inverso na máquina (Peck Deck Invertido) (3x10-12)", "Arnold press (3x8-10)", "Face pull (3x12-15)", "Encolhimento com halteres (Shrugs) (3x10-15)"],
        "Avançado": ["Arnold press sentado (4x6-10)", "Elevação posterior com halteres no banco inclinado (4x10-12)", "Face pull com corda na polia alta (4x12-15)", "Desenvolvimento com barra por trás da nuca (cuidado com a mobilidade) (3x6-8)", "Elevação lateral com rotação (Lu Raises) (3x10-12)", "Push Press (3x5-8)", "Encolhimento com barra por trás (Behind-the-Back Shrugs) (3x10-12)"],
    },
    "Tríceps": {
        "Básico": ["Tríceps pulley com barra reta (4x10-12)", "Tríceps testa com barra EZ ou halteres (3x8-12)", "Mergulho no banco (3x10-15)", "Extensão de tríceps com haltere acima da cabeça (duas mãos) (3x10-12)", "Tríceps kickback (coice) (3x12-15 por braço)"],
        "Intermediário": ["Tríceps pulley com corda (4x10-12)", "Tríceps francês com barra EZ (deitado ou sentado) (3x8-10)", "Mergulho entre bancos com peso (3x8-12)", "Extensão unilateral com haltere acima da cabeça (3x10-12 cada braço)", "Tríceps no cabo com pegada inversa (3x10-12)", "Paralelas (Dips) com foco no tríceps (3x até a falha ou com peso)"],
        "Avançado": ["Supino fechado (Close-Grip Bench Press) (4x6-10)", "Extensão unilateral com corda na polia alta (Overhead Cable Extension) (4x10-12 por braço)", "Tríceps no cabo com variação de pegadas (barra V, corda, unilateral) (4x8-12)", "Tríceps testa com barra W (3x6-8)", "Mergulho em paralelas com peso adicional (Weighted Dips) (3x6-8)", "JM Press (3x5-8)", "Floor Press com pegada fechada (3x8-10)"],
    },
    "Bíceps": {
        "Básico": ["Rosca direta com barra reta ou EZ (4x8-12)", "Rosca martelo com halteres (3x10-12)", "Rosca concentrada com haltere (3x10-12 por braço)", "Rosca Scott com barra W ou halteres (3x10-12)", "Rosca inversa com barra (3x10-12)"],
        "Intermediário": ["Rosca alternada com halteres (sentado ou em pé) (4x8-10 cada braço)", "Rosca 21 com barra (3x21)", "Rosca Scott com barra EZ (pegada fechada e aberta) (3x8-10)", "Rosca spider com barra ou halteres (3x10-12)", "Rosca com cabo na polia baixa (com barra ou corda) (3x10-12)", "Rosca no banco inclinado com halteres (3x8-10)"],
        "Avançado": ["Rosca spider com barra W (4x8-10)", "Rosca inversa com barra grossa (Fat Gripz) (4x8-10)", "Rosca com cabo na polia alta (simulando dupla bíceps) (4x8-12)", "Rosca concentrada com halteres (com pico de contração) (3x10-12 cada braço)", "Rosca Zottman (3x10-12)", "Rosca com bandas elásticas (para variação de tensão) (3x12-15)", "Chin-ups com pegada supinada (foco no bíceps) (3x até a falha)"],
    },
    "Abdômen": {
        "Básico": ["Abdominal crunch ( Supra) (3x15-20)", "Prancha frontal (Plank) (3x30-60 seg)", "Elevação de pernas deitado (Infra) (3x12-15)", "Russian twist (Giro Russo) sem peso (3x15 cada lado)", "Abdominal bicicleta no chão (3x15-20 cada lado)"],
        "Intermediário": ["Prancha lateral (Side Plank) (3x30-45 seg cada lado)", "Elevação de pernas suspenso na barra (Hanging Leg Raise) (3x10-12)", "Abdominal com peso no peito (Weighted Crunch) (3x12-15)", "Woodchopper com cabo ou halter (Lenhador) (3x10-12 cada lado)", "Abdominal na roda (Ab Wheel Rollout) - joelhos no chão (3x8-12)", "Dragon flag (negativas ou com assistência) (3x6-8)"],
        "Avançado": ["Dragon flag completo (4x6-8)", "Hanging Windshield Wipers (Limpador de Para-brisa Suspenso) (3x8-10 cada lado)", "Abdominal com cabo na polia alta (Cable Crunch) (4x12-15)", "Prancha com movimento (ex: tocar ombros, estender braços) (3x45-60 seg)", "Abdominal canivete (V-ups) (3x12-15)", "Toes-to-bar (Pés na Barra) (3x8-10)", "Abdominal na roda (Ab Wheel Rollout) - em pé (3x6-10)"],
    },
}

ALIMENTOS = {
    "Proteínas": [
        "Frango (peito grelhado/cozido)", "Peito de peru defumado", "Peixe branco", "Salmão grelhado",
        "Atum em água", "Carne vermelha magra", "Ovos inteiros",
        "Clara de ovo", "Queijo cottage", "Iogurte grego natural",
        "Whey protein", "Camarão cozido", "Lentilha cozida", "Grão de bico",
        "Tofu firme", "Carne de porco magra", "Ricota fresca", "Proteína de soja"
    ],
    "Carboidratos": [
        "Arroz integral", "Batata-doce", "Quinoa cozida",
        "Aveia em flocos", "Pão integral", "Massa integral",
        "Batata inglesa", "Inhame cozido", "Mandioca cozida",
        "Frutas variadas", "Banana prata", "Maçã",
        "Mamão formosa", "Melancia", "Pasta de amendoim integral",
        "Cuscuz nordestino", "Milho verde", "Tapioca",
        "Feijão", "Arroz branco"
    ],
    "Gorduras": [
        "Abacate", "Castanha do Pará", "Castanha de caju", "Amêndoas",
        "Nozes", "Azeite de oliva extra virgem", "Sementes de linhaça",
        "Sementes de chia", "Gema de ovo", "Manteiga de amendoim",
        "Queijo amarelo", "Chocolate amargo (70%+)"
    ],
    "Vegetais": [
        "Brócolis", "Espinafre", "Abóbora cabotiá", "Couve-flor", "Pepino",
        "Tomate", "Alface", "Rúcula", "Cenoura", "Beterraba",
        "Berinjela", "Abobrinha", "Pimentão"
    ],
}

# --- FUNÇÕES DE SALVAMENTO DE ARQUIVOS (JSON) ---
def carregar_treinos_salvos():
    if os.path.exists(ARQUIVO_TREINOS):
        try:
            with open(ARQUIVO_TREINOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_treinos_arquivo(treinos):
    with open(ARQUIVO_TREINOS, "w", encoding="utf-8") as f:
        json.dump(treinos, f, ensure_ascii=False, indent=4)

# --- FUNÇÕES AUXILIARES COM CACHE ---
@st.cache_data
def calcular_tmb(peso, altura, idade, genero):
    if genero == "Masculino":
        return (10 * peso) + (6.25 * altura) - (5 * idade) + 5
    else:
        return (10 * peso) + (6.25 * altura) - (5 * idade) - 161

@st.cache_data
def calcular_macros(peso, altura, idade, genero, meta, experiencia, atividade, dieta_selecionada):
    tmb = calcular_tmb(peso, altura, idade, genero)
    multiplicador_atividade = NIVEIS_ATIVIDADE_MULTIPLICADORES.get(atividade, 1.55)
    calorias = tmb * multiplicador_atividade

    if meta == "Crescimento":
        calorias += 300 if experiencia == "Básico" else (400 if experiencia == "Intermediário" else 500)
    elif meta == "Emagrecimento":
        calorias -= 300 if experiencia == "Básico" else (400 if experiencia == "Intermediário" else 500)

    if dieta_selecionada == "Crescimento (Hipercalórica)":
        calorias = max(calorias, tmb * multiplicador_atividade + 350)
    elif dieta_selecionada == "Emagrecimento (Hipocalórica)":
        calorias = min(calorias, tmb * multiplicador_atividade - 350)
        if calorias < tmb * 0.8:
            calorias = tmb * 0.8

    proteinas_g_kg = 1.8
    if meta == "Crescimento":
        proteinas_g_kg = 2.0 if experiencia != "Avançado" else 2.2
    elif meta == "Emagrecimento":
        proteinas_g_kg = 2.2 if experiencia != "Avançado" else 2.4

    if dieta_selecionada == "Cetogênica":
        proteinas_g_kg = max(1.6, min(proteinas_g_kg, 2.0))
    elif dieta_selecionada == "Low Carb":
        proteinas_g_kg = max(proteinas_g_kg, 2.0)

    proteinas_total_g = peso * proteinas_g_kg
    calorias_proteinas = proteinas_total_g * 4
    calorias_restantes_para_carb_gord = calorias - calorias_proteinas

    gorduras_min_g_kg = 0.6
    carboidratos_total_g = 0
    gorduras_total_g = 0

    if dieta_selecionada == "Cetogênica":
        carboidratos_total_g = random.randint(20, 40)
        calorias_carboidratos = carboidratos_total_g * 4
        calorias_gorduras = calorias_restantes_para_carb_gord - calorias_carboidratos
        gorduras_total_g = calorias_gorduras / 9
        if gorduras_total_g < peso * gorduras_min_g_kg:
            gorduras_total_g = peso * gorduras_min_g_kg
    elif dieta_selecionada == "Low Carb":
        carboidratos_total_g = min(max(50, (calorias_restantes_para_carb_gord * random.uniform(0.20, 0.30)) / 4), 150)
        calorias_carboidratos = carboidratos_total_g * 4
        calorias_gorduras = calorias_restantes_para_carb_gord - calorias_carboidratos
        gorduras_total_g = calorias_gorduras / 9
    else:
        perc_carb_restante = 0.50
        if meta == "Crescimento" or dieta_selecionada == "Crescimento (Hipercalórica)":
            perc_carb_restante = random.uniform(0.55, 0.65)
        elif meta == "Emagrecimento" or dieta_selecionada == "Emagrecimento (Hipocalórica)":
            perc_carb_restante = random.uniform(0.40, 0.50)

        calorias_carboidratos = calorias_restantes_para_carb_gord * perc_carb_restante
        carboidratos_total_g = calorias_carboidratos / 4
        calorias_gorduras = calorias_restantes_para_carb_gord - calorias_carboidratos
        gorduras_total_g = calorias_gorduras / 9

    if gorduras_total_g < peso * gorduras_min_g_kg:
        gorduras_total_g = peso * gorduras_min_g_kg
        calorias_gorduras = gorduras_total_g * 9
        calorias_carboidratos = calorias_restantes_para_carb_gord - calorias_gorduras
        carboidratos_total_g = max(0, calorias_carboidratos / 4)

    if carboidratos_total_g < 0:
        carboidratos_total_g = 0

    calorias_recalculadas = (proteinas_total_g * 4) + (carboidratos_total_g * 4) + (gorduras_total_g * 9)

    return {
        "calorias": int(calorias_recalculadas),
        "proteinas": int(proteinas_total_g),
        "carboidratos": int(carboidratos_total_g),
        "gorduras": int(gorduras_total_g),
    }

@st.cache_data
def gerar_treino_completo(dias_treino, experiencia, meta, foco_treino, custom_split=None, custom_exercises=None):
    treino = {}
    
    # 1. Personalizado
    if foco_treino == "Personalizado (Montar meu próprio)":
        split_escolhido = f"Split Personalizado ({dias_treino} dias)"
        grupos_por_dia = custom_split or {}
        
    # 2. Full Body Superior
    elif foco_treino == "Full Body Superior (Apenas Superiores)":
        split_escolhido = f"Full Body Superior ({dias_treino} dias)"
        grupos_por_dia = {}
        for d in range(1, dias_treino + 1):
            if d % 2 != 0:
                grupos_por_dia[d] = ["Peito", "Costas", "Ombros", "Bíceps", "Tríceps"]
            else:
                grupos_por_dia[d] = ["Costas", "Peito", "Ombros", "Tríceps", "Bíceps"]

    # 3. NOVO: Híbrido (Fullbody + Foco Personalizado)
    elif foco_treino == "Híbrido (Fullbody + Personalizado)":
        split_escolhido = f"Híbrido Fullbody/Foco ({dias_treino} dias)"
        grupos_por_dia = {}
        grupos_fullbody = ["Peito", "Costas", "Pernas", "Ombros", "Bíceps", "Tríceps"]
        
        for d in range(1, dias_treino + 1):
            # Se o usuário escolheu algo para o dia D, aplicamos. Senão, vai Fullbody.
            if custom_split and str(d) in custom_split and len(custom_split[str(d)]) > 0:
                grupos_por_dia[d] = custom_split[str(d)]
            else:
                grupos_por_dia[d] = grupos_fullbody
                
    # 4. Padrão IA
    else:
        if dias_treino == 1:
            split_escolhido = "Full Body A"
            grupos_por_dia = {1: ["Peito", "Costas", "Pernas", "Ombros"]}
        elif dias_treino == 2:
            split_escolhido = "Upper/Lower A/B"
            grupos_por_dia = {1: ["Peito", "Ombros", "Tríceps"], 2: ["Pernas", "Costas", "Bíceps"]}
        elif dias_treino == 3:
            opcao_3d = random.choice(["PPL", "FullBodyx3"])
            if opcao_3d == "PPL":
                split_escolhido = "Push/Pull/Legs (PPL)"
                grupos_por_dia = {1: ["Peito", "Ombros", "Tríceps"], 2: ["Costas", "Bíceps", "Abdômen"], 3: ["Pernas"]}
            else:
                split_escolhido = "Full Body 3x (A/B/C)"
                grupos_por_dia = {1: ["Peito", "Costas", "Pernas"], 2: ["Ombros", "Bíceps", "Tríceps", "Abdômen"], 3: ["Peito", "Costas", "Pernas"]}
        elif dias_treino == 4:
            opcao_4d = random.choice(["UpperLower", "BroSplit"])
            if opcao_4d == "UpperLower":
                split_escolhido = "Upper/Lower 2x (A/B)"
                grupos_por_dia = {1: ["Peito", "Ombros", "Tríceps"], 2: ["Pernas", "Abdômen"], 3: ["Costas", "Bíceps", "Ombros"], 4: ["Pernas"]}
            else:
                split_escolhido = "Bro Split Adaptado 4 dias"
                grupos_por_dia = {1: ["Peito", "Tríceps"], 2: ["Costas", "Bíceps"], 3: ["Pernas", "Abdômen"], 4: ["Ombros", "Abdômen"]}
        elif dias_treino == 5:
            split_escolhido = "Bro Split 5 dias (Clássico)"
            grupos_por_dia = {1: ["Peito"], 2: ["Costas"], 3: ["Pernas"], 4: ["Ombros", "Abdômen"], 5: ["Bíceps", "Tríceps"]}
        elif dias_treino == 6:
            split_escolhido = "Push/Pull/Legs 2x (PPL PPL)"
            grupos_por_dia = {1: ["Peito", "Ombros", "Tríceps"], 2: ["Costas", "Bíceps"], 3: ["Pernas", "Abdômen"], 4: ["Peito", "Ombros", "Tríceps"], 5: ["Costas", "Bíceps"], 6: ["Pernas"]}
        else:
            split_escolhido = "Alta Frequência/Ênfase (Avançado)"
            grupos_por_dia = {1: ["Peito", "Tríceps"], 2: ["Costas", "Bíceps"], 3: ["Pernas"], 4: ["Ombros", "Abdômen"], 5: ["Peito"], 6: ["Costas"], 7: ["Pernas", "Bíceps", "Tríceps"]}

    # Geração dos Exercícios baseados no mapa
    for dia_num in range(1, dias_treino + 1):
        nome_dia = f"Dia {dia_num}"
        treino[nome_dia] = {}
        
        grupos_do_dia_atuais = grupos_por_dia.get(dia_num, [])
        if not grupos_do_dia_atuais and custom_split and str(dia_num) in custom_split:
            grupos_do_dia_atuais = custom_split[str(dia_num)]

        grupos_do_dia_normalizados = [g.split(" (")[0].strip() for g in grupos_do_dia_atuais]
        
        ex_manuais_dia = custom_exercises.get(dia_num, []) if custom_exercises else []
        if not ex_manuais_dia and custom_exercises and str(dia_num) in custom_exercises:
            ex_manuais_dia = custom_exercises[str(dia_num)]
            
        ex_manuais_por_grupo = {}
        for grupo, ex in ex_manuais_dia:
            if grupo not in ex_manuais_por_grupo:
                ex_manuais_por_grupo[grupo] = []
            ex_manuais_por_grupo[grupo].append(ex)

        for i_grupo, grupo_muscular_original in enumerate(grupos_do_dia_atuais):
            grupo_muscular_normalizado = grupos_do_dia_normalizados[i_grupo]
            if grupo_muscular_normalizado not in EXERCICIOS:
                continue

            if foco_treino == "Personalizado (Montar meu próprio)" and grupo_muscular_normalizado in ex_manuais_por_grupo:
                exercicios_selecionados = ex_manuais_por_grupo[grupo_muscular_normalizado]
            else:
                exercicios_disponiveis = EXERCICIOS[grupo_muscular_normalizado].get(experiencia, EXERCICIOS[grupo_muscular_normalizado]["Básico"])
                if not exercicios_disponiveis:
                    continue

                # Distribuição Inteligente de Volume
                num_exercicios = 2
                if len(grupos_do_dia_normalizados) == 1:
                    num_exercicios = random.randint(4, 5) if experiencia == "Avançado" else random.randint(3, 4)
                elif len(grupos_do_dia_normalizados) == 2:
                    num_exercicios = random.randint(2, 3) if experiencia != "Avançado" else 3
                elif len(grupos_do_dia_normalizados) >= 3:
                    if grupo_muscular_normalizado in ["Peito", "Costas", "Pernas"]:
                        num_exercicios = random.randint(1, 2)
                    else:
                        num_exercicios = 1

                exercicios_selecionados = random.sample(
                    exercicios_disponiveis,
                    min(num_exercicios, len(exercicios_disponiveis)),
                )

            for i_ex, exercicio in enumerate(exercicios_selecionados):
                chave_exercicio = f"{grupo_muscular_original} - Ex. {i_ex+1}"
                count_temp = 1
                base_chave_temp = chave_exercicio
                while chave_exercicio in treino[nome_dia]:
                    chave_exercicio = f"{base_chave_temp} ({count_temp})"
                    count_temp += 1
                treino[nome_dia][chave_exercicio] = exercicio
                
    return treino, split_escolhido

@st.cache_data
def gerar_dieta_completa(macros, dieta_tipo_selecionado, meta):
    refeicoes_plano = {
        "Café da manhã": [], "Lanche da manhã": [], "Almoço": [],
        "Lanche da tarde": [], "Jantar": [], "Ceia": [],
    }
    perc_cal_refeicao = {
        "Café da manhã": 0.20, "Lanche da manhã": 0.10, "Almoço": 0.30,
        "Lanche da tarde": 0.15, "Jantar": 0.20, "Ceia": 0.05,
    }
    if meta == "Emagrecimento" or dieta_tipo_selecionado == "Emagrecimento (Hipocalórica)":
        perc_cal_refeicao["Ceia"] = 0.00
        perc_cal_refeicao["Lanche da manhã"] = 0.05
        perc_cal_refeicao["Lanche da tarde"] = 0.10
        perc_cal_refeicao["Almoço"] = 0.35
    elif meta == "Crescimento" or dieta_tipo_selecionado == "Crescimento (Hipercalórica)":
        perc_cal_refeicao["Lanche da manhã"] = 0.15
        perc_cal_refeicao["Lanche da tarde"] = 0.15
        perc_cal_refeicao["Ceia"] = 0.10

    dist_macros_ref = {"P": 0.30, "C": 0.40, "F": 0.30}
    if dieta_tipo_selecionado == "Cetogênica":
        dist_macros_ref = {"P": 0.20, "C": 0.05, "F": 0.75}
    elif dieta_tipo_selecionado == "Low Carb":
        dist_macros_ref = {"P": 0.30, "C": 0.20, "F": 0.50}
    elif meta == "Crescimento" or dieta_tipo_selecionado == "Crescimento (Hipercalórica)":
        dist_macros_ref = {"P": 0.30, "C": 0.50, "F": 0.20}
    elif meta == "Emagrecimento" or dieta_tipo_selecionado == "Emagrecimento (Hipocalórica)":
        dist_macros_ref = {"P": 0.35, "C": 0.30, "F": 0.35}

    for refeicao, perc_cal_total_ref in perc_cal_refeicao.items():
        if perc_cal_total_ref == 0:
            refeicoes_plano[refeicao].append("Refeição opcional ou jejum neste plano.")
            continue

        cal_ref = macros["calorias"] * perc_cal_total_ref
        g_p_ref = (cal_ref * dist_macros_ref["P"]) / 4
        g_c_ref = (cal_ref * dist_macros_ref["C"]) / 4
        g_f_ref = (cal_ref * dist_macros_ref["F"]) / 9
        sugestoes_itens = []

        if g_p_ref > 5 and ALIMENTOS["Proteínas"]:
            op_p = random.sample(ALIMENTOS["Proteínas"], min(2, len(ALIMENTOS["Proteínas"])))
            sugestoes_itens.append(f"{int(g_p_ref)}g Proteína (ex: {op_p[0]})")
        
        if g_c_ref > 5 and ALIMENTOS["Carboidratos"]:
            valid_carbs = ALIMENTOS["Carboidratos"]
            if dieta_tipo_selecionado == "Cetogênica":
                valid_carbs = [a for a in ALIMENTOS["Gorduras"] if "castanha" in a or "semente" in a or "abacate" in a] + \
                              [v for v in ALIMENTOS["Vegetais"] if any(k in v for k in ["folhas", "brócolis", "couve-flor"])]
            if not valid_carbs:
                valid_carbs = ["Vegetais de baixo amido"]
            op_c = random.sample(valid_carbs, min(1, len(valid_carbs))) if valid_carbs else []
            if op_c:
                sugestoes_itens.append(f"{int(g_c_ref)}g Carbo (ex: {op_c[0]})")
        
        if g_f_ref > 3 and ALIMENTOS["Gorduras"]:
            op_f = random.sample(ALIMENTOS["Gorduras"], min(1, len(ALIMENTOS["Gorduras"])))
            sugestoes_itens.append(f"{int(g_f_ref)}g Gordura (ex: {op_f[0]})")
            
        if refeicao in ["Almoço", "Jantar"] and ALIMENTOS["Vegetais"]:
            op_v = random.sample(ALIMENTOS["Vegetais"], min(2, len(ALIMENTOS["Vegetais"])))
            sugestoes_itens.append(f"Vegetais à vontade (ex: {op_v[0]}, {op_v[1]})")

        if sugestoes_itens:
            refeicoes_plano[refeicao].append(f"~{int(cal_ref)} kcal: " + " + ".join(sugestoes_itens))
        else:
            refeicoes_plano[refeicao].append(f"~{int(cal_ref)} kcal: Ajustar com base nos macros.")

    return refeicoes_plano

def gerar_pdf(treino, dieta_plano, macros, user_data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=18, alignment=1, spaceAfter=20)
    heading_style = ParagraphStyle("HeadingStyle", parent=styles["h2"], fontSize=14, spaceAfter=10, spaceBefore=12)
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6)
    
    story = []
    story.append(Paragraph("<b>PLANO DE TREINO E DIETA - MODO MONSTRO</b>", title_style))

    user_info_text = f"""
        <b>Nome:</b> {user_data.get('nome', 'N/A')}<br/>
        <b>Físico:</b> {user_data['peso']} kg | {user_data['altura']} cm | {user_data['idade']} anos<br/>
        <b>Meta:</b> {user_data['meta']} | <b>Nível:</b> {user_data['experiencia']}<br/>
        <b>Foco:</b> {user_data.get('foco_treino', 'Padrão')} ({user_data['dias_treino']} dias/sem)<br/>
        <b>Dieta:</b> {user_data['dieta_selecionada']}
    """
    story.append(Paragraph(user_info_text, body_style))
    story.append(Paragraph("<br/>", body_style))

    # Tabela Macros
    story.append(Paragraph("<b>MACROS DIÁRIOS</b>", heading_style))
    macros_data = [
        ["Calorias", f"{macros['calorias']} kcal"],
        ["Proteínas", f"{macros['proteinas']} g"],
        ["Carboidratos", f"{macros['carboidratos']} g"],
        ["Gorduras", f"{macros['gorduras']} g"]
    ]
    t_macros = Table(macros_data, colWidths=[width*0.3, width*0.4])
    t_macros.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, (0, 0, 0)),
        ("BACKGROUND", (0, 0), (0, -1), (0.9, 0.9, 0.9)),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_macros)
    story.append(Paragraph("<br/>", body_style))

    # Treino
    story.append(Paragraph("<b>PROTOCOLOS DE TREINO</b>", heading_style))
    for dia, exercicios in treino.items():
        story.append(Paragraph(f"<b>{dia.upper()}</b>", ParagraphStyle("Dia", parent=body_style, fontName="Helvetica-Bold")))
        if not exercicios:
            story.append(Paragraph("• Descanso ativo ou off.", body_style))
        for grupo, ex in exercicios.items():
            grupo_clean = grupo.split(" - ")[0]
            story.append(Paragraph(f"• <b>[{grupo_clean}]</b> {ex}", body_style))
        story.append(Paragraph("<br/>", body_style))

    # Dieta
    story.append(Paragraph("<b>PLANO ALIMENTAR</b>", heading_style))
    for ref, itens in dieta_plano.items():
        story.append(Paragraph(f"<b>{ref.upper()}</b>", ParagraphStyle("Ref", parent=body_style, fontName="Helvetica-Bold")))
        for item in itens:
            story.append(Paragraph(f"• {item}", body_style))
        story.append(Paragraph("<br/>", body_style))

    doc = SimpleDocTemplate(buffer, pagesize=A4)
    doc.build(story)
    
    buffer.seek(0)
    return buffer

# --- MAIN APP LAYOUT ---
def main():
    # SIDEBAR: Perfil do Usuário
    with st.sidebar:
        st.header("👤 Perfil do Atleta")
        nome = st.text_input("Nome/Apelido", placeholder="Ex: Cbum")
        
        col_side1, col_side2 = st.columns(2)
        with col_side1:
            peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=75.0, step=0.5)
            idade = st.number_input("Idade", min_value=12, max_value=100, value=25)
        with col_side2:
            altura = st.number_input("Altura (cm)", min_value=100, max_value=250, value=175)
            genero = st.selectbox("Gênero", ["Masculino", "Feminino"])

        atividade = st.selectbox("Nível de Atividade (Dia a Dia)", list(NIVEIS_ATIVIDADE_MULTIPLICADORES.keys()))
        
        st.markdown("---")
        st.caption("Sistema de Periodização Modo Monstro v2.0")

    # MAIN AREA
    st.title("💀 Treinador IA - Modo Monstro")
    st.markdown("Gere protocolos de treino e dietas baseados em ciência e hipertrofia.")

    # ABAS (Tabs) para manter o visual limpo
    tab_config, tab_plano, tab_hist = st.tabs(["⚙️ Configurar Protocolo", "🔥 Seu Plano", "📁 Arsenal (Salvos)"])

    with tab_config:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Objetivos")
            meta = st.selectbox("Qual a sua meta principal?", META_OPCOES)
            experiencia = st.selectbox("Nível de Experiência no Treino", EXPERIENCIA_OPCOES)
            dieta = st.selectbox("Estratégia Nutricional", DIETA_OPCOES)

        with col2:
            st.subheader("Frequência & Divisão")
            dias_treino = st.number_input("Dias de treino na semana", min_value=1, max_value=7, value=5)
            foco_treino = st.selectbox(
                "Estrutura do Treino", 
                [
                    "Padrão (IA decide a melhor divisão)", 
                    "Full Body Superior (Apenas Superiores)", 
                    "Híbrido (Fullbody + Personalizado)",
                    "Personalizado (Montar meu próprio)"
                ]
            )

        custom_split = {}
        
        # INTERFACE DA NOVA LÓGICA HÍBRIDA
        if foco_treino in ["Híbrido (Fullbody + Personalizado)", "Personalizado (Montar meu próprio)"]:
            st.markdown("---")
            st.markdown(f"### 🧬 Setup {foco_treino.split(' ')[0]}")
            
            if "Híbrido" in foco_treino:
                st.info("💡 **Dica:** Deixe o dia vazio para gerar um treino **Fullbody**. Se quiser focar em algo (ex: Pernas), selecione o músculo.")
            else:
                st.info("💡 Escolha exatamente os músculos que quer treinar em cada dia.")
            
            lista_musculos = list(EXERCICIOS.keys())
            
            # Gerando os selects em um grid elegante (até 4 por linha)
            cols_dias = st.columns(min(dias_treino, 4))
            for i in range(1, dias_treino + 1):
                col_idx = (i - 1) % len(cols_dias)
                with cols_dias[col_idx]:
                    selecao = st.multiselect(
                        f"Dia {i}", 
                        options=lista_musculos,
                        placeholder="Fullbody" if "Híbrido" in foco_treino else "Selecione...",
                        key=f"split_dia_{i}"
                    )
                    if selecao:
                        custom_split[str(i)] = selecao

        st.markdown("<br>", unsafe_allow_html=True)
        btn_gerar = st.button("GERAR PROTOCOLO DE ALTA PERFORMANCE", use_container_width=True)

    if btn_gerar:
        with st.spinner('Forjando o protocolo no fogo...'):
            user_data = {
                "nome": nome, "idade": idade, "altura": altura, "peso": peso, 
                "genero": genero, "experiencia": experiencia, "meta": meta, 
                "foco_treino": foco_treino, "dias_treino": dias_treino, 
                "dieta_selecionada": dieta
            }
            
            # Cálculos
            macros = calcular_macros(peso, altura, idade, genero, meta, experiencia, atividade, dieta)
            treino, nome_split = gerar_treino_completo(dias_treino, experiencia, meta, foco_treino, custom_split)
            dieta_plano = gerar_dieta_completa(macros, dieta, meta)
            
            # Guardando na Sessão para transitar entre as abas
            st.session_state['treino_atual'] = treino
            st.session_state['dieta_atual'] = dieta_plano
            st.session_state['macros_atual'] = macros
            st.session_state['user_data'] = user_data
            st.session_state['nome_split'] = nome_split
            
            # Salvamento automático no histórico
            treinos_existentes = carregar_treinos_salvos()
            id_treino = f"Treino_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            treinos_existentes[id_treino] = {
                "data": datetime.now().strftime('%d/%m/%Y %H:%M'),
                "split": nome_split,
                "meta": meta,
                "treino": treino
            }
            salvar_treinos_arquivo(treinos_existentes)
            
            st.success("🔥 Protocolo gerado com sucesso! Vá para a aba 'Seu Plano' para visualizar.")

    # ABA: SEU PLANO (Exibição dos Resultados)
    with tab_plano:
        if 'treino_atual' in st.session_state:
            macros = st.session_state['macros_atual']
            
            st.markdown("### 📊 Macros Diários Alvo")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🔥 Calorias", f"{macros['calorias']} kcal")
            c2.metric("🥩 Proteínas", f"{macros['proteinas']}g")
            c3.metric("🍚 Carboidratos", f"{macros['carboidratos']}g")
            c4.metric("🥑 Gorduras", f"{macros['gorduras']}g")
            
            st.markdown("---")
            col_treino, col_dieta = st.columns([1.2, 1])
            
            with col_treino:
                st.markdown(f"### 🏋️ Rotina: {st.session_state['nome_split']}")
                for dia, exercicios in st.session_state['treino_atual'].items():
                    with st.expander(f"💪 {dia}", expanded=True):
                        if not exercicios:
                            st.write("Descanso / Recovery")
                        for chave, ex in exercicios.items():
                            grupo = chave.split(" - ")[0]
                            st.markdown(f"- **{grupo}:** {ex}")
            
            with col_dieta:
                st.markdown("### 🍽️ Refeições Sugeridas")
                for ref, itens in st.session_state['dieta_atual'].items():
                    with st.expander(f"🍴 {ref}", expanded=False):
                        for item in itens:
                            st.markdown(f"- {item}")
                            
            st.markdown("---")
            
            # Geração do PDF para Download
            pdf_buffer = gerar_pdf(
                st.session_state['treino_atual'], 
                st.session_state['dieta_atual'], 
                st.session_state['macros_atual'], 
                st.session_state['user_data']
            )
            
            st.download_button(
                label="📥 DOWNLOAD PLANO COMPLETO (PDF)",
                data=pdf_buffer,
                file_name=f"Plano_Monstro_{st.session_state['user_data'].get('nome', 'Atleta')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("Configure e gere seu protocolo na aba 'Configurar Protocolo' primeiro.")

    # ABA: HISTÓRICO
    with tab_hist:
        treinos_salvos = carregar_treinos_salvos()
        if not treinos_salvos:
            st.write("Nenhum treino no arsenal ainda.")
        else:
            st.markdown("### 📁 Arsenal de Treinos")
            for t_id, dados in reversed(list(treinos_salvos.items())):
                with st.expander(f"🗓️ {dados['data']} - {dados.get('split', 'Treino')} ({dados.get('meta', '')})"):
                    st.json(dados['treino'])

if __name__ == "__main__":
    main()