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

# --- ESTILIZAÇÃO CSS CUSTOMIZADA (TEMA HARDCORE / MONSTRO) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0c0c0c;
        color: #e0e0e0;
    }
    [data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #222222;
    }
    .stButton>button {
        background: linear-gradient(135deg, #b70909 0%, #e5383b 100%);
        color: white;
        font-weight: 800;
        letter-spacing: 0.5px;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        box-shadow: 0 4px 10px rgba(183, 9, 9, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #e5383b 100%, #ff4d4d 0%);
        box-shadow: 0 0 15px rgba(229, 56, 59, 0.8);
        transform: translateY(-2px);
    }
    [data-testid="stDownloadButton"]>button {
        background: linear-gradient(135deg, #132a13 0%, #31572c 100%);
        color: #ffffff;
        font-weight: 800;
        border: 1px solid #4f772d;
        border-radius: 6px;
    }
    [data-testid="stDownloadButton"]>button:hover {
        background: linear-gradient(135deg, #31572c 0%, #4f772d 100%);
        box-shadow: 0 0 12px rgba(79, 119, 45, 0.6);
    }
    [data-testid="stMetric"] {
        background-color: #171717;
        border: 1px solid #282828;
        border-left: 4px solid #e5383b;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    [data-testid="stMetricLabel"] {
        color: #999999 !important;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    [data-testid="stMetricValue"] {
        color: #ff4d4d !important;
        font-weight: 900;
        font-size: 1.6rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #0c0c0c;
        padding-bottom: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #171717;
        border: 1px solid #282828;
        border-radius: 6px 6px 0px 0px;
        color: #b0b0b0;
        font-weight: 700;
        padding: 10px 24px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e5383b !important;
        color: white !important;
        border-color: #e5383b !important;
        box-shadow: 0 -2px 10px rgba(229, 56, 59, 0.5);
    }
    .streamlit-expanderHeader {
        background-color: #171717 !important;
        border: 1px solid #282828;
        border-radius: 6px;
        color: #ffffff !important;
        font-weight: 700;
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
        "Frango (peito grelhado/cozido) (100g)", "Peito de peru defumado (100g)", "Peixe branco (tilápia, linguado, merluza) (100g)", "Salmão grelhado/assado (100g)",
        "Atum em água (lata 80g drenado)", "Carne vermelha magra (patinho, alcatra, maminha) (100g)", "Ovos inteiros cozidos (2 unidades grandes)",
        "Clara de ovo pasteurizada (equivalente a 4 claras)", "Queijo cottage (100g)", "Iogurte grego natural desnatado (1 pote 100-150g)",
        "Whey protein isolado/concentrado (1 dose/scoop)", "Camarão cozido (100g)", "Lentilha cozida (1 xícara ~180g)", "Grão de bico cozido (1 xícara ~160g)",
        "Tofu firme (100g)", "Carne de porco magra (lombo assado/grelhado) (100g)", "Ricota fresca (50g)", "Proteína de soja texturizada hidratada (100g)"
    ],
    "Carboidratos": [
        "Arroz integral cozido (1 xícara ~150g)", "Batata-doce cozida/assada (1 média ~150g)", "Quinoa cozida (1 xícara ~180g)",
        "Aveia em flocos (4 colheres de sopa ~40g)", "Pão integral (100% integral) (2 fatias)", "Massa integral cozida (1 xícara ~140g)",
        "Batata inglesa cozida/assada (1 média ~150g)", "Inhame cozido (1 médio ~150g)", "Mandioca (aipim/macaxeira) cozida (1 pedaço médio ~150g)",
        "Frutas variadas (1 porção média)", "Banana prata/nanica (1 unidade média)", "Maçã (Gala, Fuji) (1 unidade média)",
        "Mamão formosa (1 fatia média)", "Melancia (1 fatia grande)", "Pasta de amendoim integral sem açúcar (1 colher de sopa ~15g)",
        "Cuscuz nordestino cozido (1/2 xícara ~100g)", "Milho verde cozido (1 espiga média)", "Tapioca (goma hidratada) (3 colheres de sopa)",
        "Feijão (carioca, preto, fradinho) cozido (1 concha média ~100g)", "Arroz branco cozido (1 xícara ~150g)"
    ],
    "Gorduras": [
        "Abacate (1/2 unidade pequena)", "Castanha do Pará (2-3 unidades)", "Castanha de caju (10-15 unidades)", "Amêndoas (10-15 unidades)",
        "Nozes (4-5 metades)", "Azeite de oliva extra virgem (1 colher de sopa ~10ml)", "Sementes de linhaça (1-2 colheres de sopa)",
        "Sementes de chia (1-2 colheres de sopa)", "Gema de ovo (incluída nos ovos inteiros)", "Manteiga de amendoim/castanhas (1 colher de sopa)",
        "Queijo amarelo (1 fatia grossa ~30g)", "Chocolate amargo (70% cacau ou mais) (2-3 quadradinhos ~20-30g)"
    ],
    "Vegetais": [
        "Brócolis (1 xícara)", "Espinafre (1 xícara)", "Abóbora cabotiá/moranga (1 xícara)", "Couve-flor (1 xícara)", "Pepino (1 unidade média)",
        "Tomate (1 unidade média)", "Alface (à vontade)", "Rúcula (à vontade)", "Cenoura (1 unidade média)", "Beterraba (1/2 unidade média)",
        "Berinjela (1 xícara)", "Abobrinha (1 unidade média)", "Pimentão (1/2 unidade média)"
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
    
    if foco_treino == "Personalizado (Montar meu próprio)":
        split_escolhido = f"Split Personalizado ({dias_treino} dias)"
        grupos_por_dia = custom_split or {}
    elif foco_treino == "Full Body Superior (Apenas Superiores)":
        split_escolhido = f"Full Body Superior ({dias_treino} dias)"
        grupos_por_dia = {}
        for d in range(1, dias_treino + 1):
            if d % 2 != 0:
                grupos_por_dia[d] = ["Peito", "Costas", "Ombros", "Bíceps", "Tríceps"]
            else:
                grupos_por_dia[d] = ["Costas", "Peito", "Ombros", "Tríceps", "Bíceps"]
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
            grupos_por_dia = {1: ["Peito", "Tríceps"], 2: ["Costas", "Bíceps"], 3: ["Pernas (Quadríceps)"], 4: ["Ombros", "Abdômen"], 5: ["Peito (Superior/Deload)"], 6: ["Costas (Largura/Deload)"], 7: ["Pernas (Posterior/Glúteos)", "Bíceps", "Tríceps"]}

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

                num_exercicios = 2
                if len(grupos_do_dia_normalizados) == 1:
                    num_exercicios = random.randint(3, 4) if experiencia != "Avançado" else random.randint(4, 5)
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
def gerar_dieta_completa(macros, dieta_tipo_selecionado, user_data):
    refeicoes_plano = {
        "Café da manhã": [], "Lanche da manhã": [], "Almoço": [],
        "Lanche da tarde": [], "Jantar": [], "Ceia": [],
    }
    perc_cal_refeicao = {
        "Café da manhã": 0.20, "Lanche da manhã": 0.10, "Almoço": 0.30,
        "Lanche da tarde": 0.15, "Jantar": 0.20, "Ceia": 0.05,
    }
    if user_data["meta"] == "Emagrecimento" or dieta_tipo_selecionado == "Emagrecimento (Hipocalórica)":
        perc_cal_refeicao["Ceia"] = 0.00
        perc_cal_refeicao["Lanche da manhã"] = 0.05
        perc_cal_refeicao["Lanche da tarde"] = 0.10
        perc_cal_refeicao["Almoço"] = 0.35
    elif user_data["meta"] == "Crescimento" or dieta_tipo_selecionado == "Crescimento (Hipercalórica)":
        perc_cal_refeicao["Lanche da manhã"] = 0.15
        perc_cal_refeicao["Lanche da tarde"] = 0.15
        perc_cal_refeicao["Ceia"] = 0.10

    dist_macros_ref = {"P": 0.30, "C": 0.40, "F": 0.30}
    if dieta_tipo_selecionado == "Cetogênica":
        dist_macros_ref = {"P": 0.20, "C": 0.05, "F": 0.75}
    elif dieta_tipo_selecionado == "Low Carb":
        dist_macros_ref = {"P": 0.30, "C": 0.20, "F": 0.50}
    elif user_data["meta"] == "Crescimento" or dieta_tipo_selecionado == "Crescimento (Hipercalórica)":
        dist_macros_ref = {"P": 0.30, "C": 0.50, "F": 0.20}
    elif user_data["meta"] == "Emagrecimento" or dieta_tipo_selecionado == "Emagrecimento (Hipocalórica)":
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
            sugestoes_itens.append(f"{int(g_p_ref)}g Proteína (ex: {op_p[0]} ou {op_p[1]})")
        
        if g_c_ref > 5 and ALIMENTOS["Carboidratos"]:
            valid_carbs = ALIMENTOS["Carboidratos"]
            if dieta_tipo_selecionado == "Cetogênica":
                valid_carbs = [a for a in ALIMENTOS["Gorduras"] if "castanha" in a or "semente" in a or "abacate" in a or "coco" in a] + \
                              [v for v in ALIMENTOS["Vegetais"] if any(k in v for k in ["folhas", "brócolis", "couve-flor", "abobrinha", "pepino"])]
            if not valid_carbs:
                valid_carbs = ["Vegetais de baixo amido"]
            op_c = random.sample(valid_carbs, min(2, len(valid_carbs))) if valid_carbs else []
            if op_c:
                sugestoes_itens.append(f"{int(g_c_ref)}g Carboidratos (ex: {op_c[0]}{f' ou {op_c[1]}' if len(op_c)>1 else ''})")
        
        if g_f_ref > 3 and ALIMENTOS["Gorduras"]:
            op_f = random.sample(ALIMENTOS["Gorduras"], min(2, len(ALIMENTOS["Gorduras"])))
            sugestoes_itens.append(f"{int(g_f_ref)}g Gorduras (ex: {op_f[0]} ou {op_f[1]})")
            
        if refeicao in ["Almoço", "Jantar"] and ALIMENTOS["Vegetais"]:
            op_v = random.sample(ALIMENTOS["Vegetais"], min(2, len(ALIMENTOS["Vegetais"])))
            sugestoes_itens.append(f"Vegetais (ex: {op_v[0]}, {op_v[1]} - à vontade ou porções indicadas)")

        if sugestoes_itens:
            refeicoes_plano[refeicao].append(f"~{int(cal_ref)} kcal: " + "; ".join(sugestoes_itens))
        else:
            refeicoes_plano[refeicao].append(f"~{int(cal_ref)} kcal: Ajustar com base nos macros ou refeição leve.")

    if user_data["dias_treino"] > 0:
        refeicoes_plano["Lanche da tarde"].append(f"<i>Sugestão Pré-Treino:</i> {random.choice(ALIMENTOS['Carboidratos'])} + {random.choice(ALIMENTOS['Proteínas'])}")
        refeicoes_plano["Jantar"].append(f"<i>Sugestão Pós-Treino:</i> Refeição completa com {random.choice(ALIMENTOS['Proteínas'])} e {random.choice(ALIMENTOS['Carboidratos'])}")

    return refeicoes_plano

def gerar_pdf(treino, dieta_plano, macros, user_data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=18, alignment=1, spaceAfter=20, leading=22)
    heading_style = ParagraphStyle("HeadingStyle", parent=styles["h2"], fontSize=14, spaceAfter=10, spaceBefore=12, leading=18)
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6)
    user_info_style = ParagraphStyle("UserInfoStyle", parent=styles["Normal"], fontSize=9, leading=12, spaceAfter=10)
    table_header_style = ParagraphStyle("TableHeaderStyle", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold", alignment=0)
    table_cell_style = ParagraphStyle("TableCellStyle", parent=styles["Normal"], fontSize=10, alignment=0)

    story = []
    story.append(Paragraph("<b>PLANO COMPLETO DE TREINO E DIETA</b>", title_style))

    user_info_text = f"""
        <b>Nome:</b> {user_data.get('nome', 'N/A')}<br/>
        <b>Idade:</b> {user_data['idade']} anos | <b>Altura:</b> {user_data['altura']} cm | <b>Peso:</b> {user_data['peso']} kg<br/>
        <b>Gênero:</b> {user_data['genero']} | <b>Nível:</b> {user_data['experiencia']} | <b>Meta:</b> {user_data['meta']}<br/>
        <b>Foco:</b> {user_data.get('foco_treino', 'Padrão')} | <b>Dias de Treino:</b> {user_data['dias_treino']}/semana <br/>
        <b>Dieta:</b> {user_data['dieta_selecionada']}<br/>
        <b>Data da Geração:</b> {datetime.now().strftime('%d/%m/%Y')}
    """
    story.append(Paragraph(user_info_text, user_info_style))

    story.append(Paragraph("<b>MACROS DIÁRIOS ESTIMADOS</b>", heading_style))
    macros_data_pdf = [
        [Paragraph("<b>Nutriente</b>", table_header_style), Paragraph("<b>Quantidade</b>", table_header_style)],
        [Paragraph("Calorias:", table_cell_style), Paragraph(f"{macros['calorias']} kcal", table_cell_style)],
        [Paragraph("Proteínas:", table_cell_style), Paragraph(f"{macros['proteinas']} g", table_cell_style)],
        [Paragraph("Carboidratos:", table_cell_style), Paragraph(f"{macros['carboidratos']} g", table_cell_style)],
        [Paragraph("Gorduras:", table_cell_style), Paragraph(f"{macros['gorduras']} g", table_cell_style)],
    ]
    macros_table = Table(macros_data_pdf, colWidths=[width * 0.3, width * 0.5])
    macros_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, (0, 0, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), (0.8, 0.8, 0.8)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(macros_table)
    story.append(Paragraph("<br/>", body_style))

    story.append(Paragraph("<b>PLANO DE TREINO SEMANAL</b>", heading_style))
    for dia, exercicios in treino.items():
        story.append(Paragraph(f"<b>{dia.upper()}</b>", ParagraphStyle("DiaTreino", parent=body_style, fontName="Helvetica-Bold", spaceBefore=6)))
        if not exercicios:
            story.append(Paragraph("• Descanso ou dia livre.", body_style))
        else:
            for grupo_chave_ex, exercicio_desc in exercicios.items():
                story.append(Paragraph(f"• <b>{grupo_chave_ex.replace(' - Ex. ', ' Exercício ')}:</b> {exercicio_desc}", body_style))
        story.append(Paragraph("<br/>", body_style))

    story.append(Paragraph("<b>PLANO ALIMENTAR DIÁRIO (SUGESTÕES)</b>", heading_style))
    for refeicao, itens in dieta_plano.items():
        story.append(Paragraph(f"<b>{refeicao.upper()}</b>", ParagraphStyle("RefeicaoTitulo", parent=body_style, fontName="Helvetica-Bold", spaceBefore=6)))
        if not itens or "Refeição opcional" in itens[0]:
            story.append(Paragraph("• Nenhuma sugestão específica ou refeição opcional.", body_style))
        else:
            for item_desc in itens:
                item_desc_plain = item_desc.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "").replace("<small>", "").replace("</small>", "")
                story.append(Paragraph(f"• {item_desc_plain}", body_style))
        story.append(Paragraph("<br/>", body_style))

    def draw_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(width - 30, 30, f"Página {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=50, leftMargin=50, rightMargin=50)
    doc.build(story, onFirstPage=draw_page_number, onLaterPages=draw_page_number)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf

if "plano_gerado" not in st.session_state:
    st.session_state.plano_gerado = False
if "user_data_dict" not in st.session_state:
    st.session_state.user_data_dict = {}
if "macros" not in st.session_state:
    st.session_state.macros = {}
if "treino" not in st.session_state:
    st.session_state.treino = {}
if "split_info" not in st.session_state:
    st.session_state.split_info = ""
if "dieta_plano" not in st.session_state:
    st.session_state.dieta_plano = {}

st.title("💀 Treinador IA — Modo Monstro")

with st.sidebar:
    st.header("📋 Dados do Atleta")
    
    nome = st.text_input("Nome:", placeholder="Ex: Mestre Tephinho")
    genero = st.radio("Gênero:", ["Masculino", "Feminino"], index=0, horizontal=True)
    peso = st.number_input("Peso (kg):", min_value=30.0, max_value=250.0, value=70.0, step=0.5)
    altura = st.number_input("Altura (cm):", min_value=100.0, max_value=250.0, value=175.0, step=0.5)
    idade = st.number_input("Idade:", min_value=14, max_value=99, value=25, step=1)
    
    st.write("---")
    meta = st.selectbox("🎯 Meta Principal:", META_OPCOES, index=0)
    experiencia = st.selectbox("🏋️ Nível de Experiência:", EXPERIENCIA_OPCOES, index=1)
    
    foco_treino = st.selectbox(
        "🎯 Foco do Treino:", 
        ["Padrão (Equilibrado)", "Full Body Superior (Apenas Superiores)", "Personalizado (Montar meu próprio)"], 
        index=0
    )
    
    dias_treino = st.slider("📅 Dias de treino por semana:", 1, 7, 4)
    
    custom_split = {}
    custom_exercises = {}
    
    if foco_treino == "Personalizado (Montar meu próprio)":
        st.markdown("#### 🛠️ Monte seu Microciclo:")
        opcoes_musculos = ["Peito", "Costas", "Pernas", "Ombros", "Tríceps", "Bíceps", "Abdômen"]
        
        for d in range(1, dias_treino + 1):
            with st.expander(f"📅 Configurar Dia {d}", expanded=False):
                musculos_dia = st.multiselect(f"Músculos (Dia {d}):", opcoes_musculos, key=f"custom_day_{d}")
                custom_split[d] = musculos_dia
                
                exercicios_do_dia = []
                if musculos_dia:
                    st.caption("Escolha os exercícios (ou deixe em branco para a IA gerar).")
                    for m in musculos_dia:
                        todos_ex = EXERCICIOS[m]["Básico"] + EXERCICIOS[m]["Intermediário"] + EXERCICIOS[m]["Avançado"]
                        todos_ex = list(dict.fromkeys(todos_ex)) 
                        
                        escolhidos = st.multiselect(f"Exercícios de {m}:", todos_ex, key=f"custom_ex_{d}_{m}")
                        if escolhidos:
                            exercicios_do_dia.extend([(m, ex) for ex in escolhidos])
                
                custom_exercises[d] = exercicios_do_dia

    st.write("---")
    atividade = st.selectbox("🚶 Nível de Atividade Diária:", list(NIVEIS_ATIVIDADE_MULTIPLICADORES.keys()), index=2)
    dieta_selecionada_usuario = st.selectbox("🥗 Tipo de Dieta Preferencial:", DIETA_OPCOES, index=0, key="dieta_tipo_selectbox")
    
    st.write("---")
    submitted = st.button("🔥 GERAR PLANO MONSTRO", use_container_width=True)

if submitted:
    with st.spinner("💀 Processando protocolos e calculando carga... Aguarde!"):
        st.session_state.user_data_dict = {
            "nome": nome if nome else "Atleta",
            "genero": genero, "peso": float(peso), "altura": float(altura), "idade": int(idade),
            "meta": meta, "experiencia": experiencia, "foco_treino": foco_treino, 
            "custom_split": custom_split, "custom_exercises": custom_exercises,
            "atividade": atividade, "dias_treino": int(dias_treino), "dieta_selecionada": dieta_selecionada_usuario,
        }
        st.session_state.macros = calcular_macros(float(peso), float(altura), int(idade), genero, meta, experiencia, atividade, dieta_selecionada_usuario)
        st.session_state.treino, st.session_state.split_info = gerar_treino_completo(int(dias_treino), experiencia, meta, foco_treino, custom_split, custom_exercises)
        st.session_state.dieta_plano = gerar_dieta_completa(st.session_state.macros, dieta_selecionada_usuario, st.session_state.user_data_dict)
        st.session_state.plano_gerado = True

tab_gerador, tab_salvos = st.tabs(["🚀 Gerador de Treino", "📁 Meus Planos Salvos"])

with tab_gerador:
    if st.session_state.plano_gerado:
        user_data_dict = st.session_state.user_data_dict
        macros = st.session_state.macros
        treino = st.session_state.treino
        split_info = st.session_state.split_info
        dieta_plano = st.session_state.dieta_plano

        st.success(f"💀 Protocolo Monstro para **{user_data_dict['nome']}** gerado com sucesso!")
        st.balloons()

        st.subheader("📊 Resumo dos Macros & Alvo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔥 Calorias Diárias", f"{macros['calorias']} kcal")
            st.metric("🥩 Proteínas", f"{macros['proteinas']} g")
        with col2:
            st.metric("🍚 Carboidratos", f"{macros['carboidratos']} g")
            st.metric("🥑 Gorduras", f"{macros['gorduras']} g")
        with col3:
            st.metric("🗓️ Dias de Treino", f"{user_data_dict['dias_treino']} / semana")
            st.metric("🏆 Experiência", user_data_dict['experiencia'])

        st.markdown(f"**🎯 Meta:** {user_data_dict['meta']} | **Foco:** {user_data_dict['foco_treino']} | **🥗 Dieta:** {user_data_dict['dieta_selecionada']}")
        st.markdown(f"**🏋️‍♂️ Split:** {split_info} | **🚶 Atividade:** {user_data_dict['atividade']}")

        tab_treino, tab_dieta, tab_download = st.tabs(["🏋️ Plano de Treino Detalhado", "🍽️ Plano Alimentar Sugerido", "📥 Download do Plano"])

        with tab_treino:
            st.header("📅 Seu Plano de Treino Semanal")
            for dia, exercicios_dia in treino.items():
                foco_dia_str = ", ".join(set(ex.split(" - ")[0] for ex in exercicios_dia.keys())) if exercicios_dia else "Descanso / OFF"
                with st.expander(f"**{dia.upper()}** — Foco: {foco_dia_str}"):
                    if not exercicios_dia:
                        st.write("Dia de descanso ou recuperação.")
                    else:
                        for grupo_chave_ex, exercicio_desc in exercicios_dia.items():
                            nome_exercicio = exercicio_desc.split(" (")[0]
                            query = urllib.parse.quote(f"como executar {nome_exercicio} musculação")
                            yt_link = f"https://www.youtube.com/results?search_query={query}"
                            
                            st.markdown(f"💪 **{grupo_chave_ex.replace(' - Ex. ', ' Exercício ')}:** {exercicio_desc} | [🎥 Ver Vídeo no YouTube]({yt_link})")
        
        with tab_dieta:
            st.header("🥗 Plano Alimentar e Suplementação")
            for refeicao, itens_refeicao in dieta_plano.items():
                with st.expander(f"**{refeicao.upper()}**"):
                    if not itens_refeicao or "Refeição opcional" in itens_refeicao[0]:
                        st.write("Nenhuma sugestão específica ou refeição opcional.")
                    else:
                        for item_desc in itens_refeicao:
                            st.markdown(f" • {item_desc}")
        
        with tab_download:
            st.header("📥 Baixar Ficha em PDF")
            pdf_bytes = gerar_pdf(treino, dieta_plano, macros, user_data_dict)
            st.download_button(
                label="⬇️ Baixar Protocolo em PDF",
                data=pdf_bytes,
                file_name=f"protocolo_monstro_{user_data_dict['nome'].replace(' ', '_').lower()}.pdf",
                mime="application/pdf",
                key="download_pdf_button"
            )

        st.markdown("---")
        st.subheader("💾 Salvar Ficha no Aplicativo")
        col_nome, col_btn = st.columns([3, 1])
        with col_nome:
            nome_plano_input = st.text_input("Nome da Ficha (ex: Push Pull Legs - Fase 1):", key="nome_plano_input")
        with col_btn:
            st.write("") 
            st.write("")
            if st.button("💾 Salvar Protocolo"):
                if nome_plano_input.strip() == "":
                    st.warning("Insira um nome para o plano antes de salvar.")
                else:
                    treinos_bd = carregar_treinos_salvos()
                    treinos_bd[nome_plano_input] = {
                        "data": datetime.now().strftime('%d/%m/%Y às %H:%M'),
                        "user_data": st.session_state.user_data_dict,
                        "macros": st.session_state.macros,
                        "treino": st.session_state.treino,
                        "split": st.session_state.split_info,
                        "dieta": st.session_state.dieta_plano
                    }
                    salvar_treinos_arquivo(treinos_bd)
                    st.success(f"Protocolo '{nome_plano_input}' salvo com sucesso!")

    else:
        st.info("👈 Preencha seus dados na barra lateral e clique em **GERAR PLANO MONSTRO** para começar!")
        st.markdown("### 💀 Eleve seus treinos ao próximo nível com Inteligência Artificial!")

with tab_salvos:
    st.header("📁 Protocolos Salvos")
    treinos_salvos = carregar_treinos_salvos()
    
    if not treinos_salvos:
        st.info("Nenhum protocolo salvo no momento. Gere um treino na aba ao lado e salve-o!")
    else:
        for nome_plano, dados_plano in treinos_salvos.items():
            with st.expander(f"📌 {nome_plano} (Criado em: {dados_plano.get('data', 'Data desconhecida')})"):
                usr = dados_plano['user_data']
                st.markdown(f"**Meta:** {usr['meta']} | **Foco:** {usr.get('foco_treino', 'Padrão')} | **Dias:** {usr['dias_treino']} | **Nível:** {usr['experiencia']}")
                st.write("---")
                
                cm1, cm2, cm3, cm4 = st.columns(4)
                cm1.metric("Calorias", f"{dados_plano['macros']['calorias']} kcal")
                cm2.metric("Proteínas", f"{dados_plano['macros']['proteinas']} g")
                cm3.metric("Carboidratos", f"{dados_plano['macros']['carboidratos']} g")
                cm4.metric("Gorduras", f"{dados_plano['macros']['gorduras']} g")
                
                st.write("---")
                st.markdown("**🏋️‍♂️ Detalhes do Treino Semanal:**")
                for dia, exercicios in dados_plano['treino'].items():
                    if exercicios:
                        foco_str = ", ".join(set(ex.split(" - ")[0] for ex in exercicios.keys()))
                        st.markdown(f"**{dia}** ({foco_str})")
                        for grupo_chave_ex, exercicio_desc in exercicios.items():
                            nome_exercicio = exercicio_desc.split(" (")[0]
                            query = urllib.parse.quote(f"como executar {nome_exercicio} musculação")
                            yt_link = f"https://www.youtube.com/results?search_query={query}"
                            
                            st.markdown(f"- **{grupo_chave_ex.replace(' - Ex. ', ' Exercício ')}:** {exercicio_desc} | [🎥 Ver Vídeo]({yt_link})")
                        st.write("")
                    else:
                        st.markdown(f"**{dia}**: Descanso / OFF")
                        st.write("")
                
                # Plano Alimentar integrado como um segundo plano salvo
                st.write("---")
                st.markdown("**🥗 Plano Alimentar (Dieta) Salvo:**")
                for refeicao, itens_refeicao in dados_plano.get('dieta', {}).items():
                    with st.expander(f"🍽️ {refeicao.upper()}"):
                        if not itens_refeicao or "Refeição opcional" in itens_refeicao[0]:
                            st.write("Nenhuma sugestão específica ou refeição opcional.")
                        else:
                            for item_desc in itens_refeicao:
                                st.markdown(f" • {item_desc}")
                
                st.write("---")
                if st.button(f"🗑️ Excluir '{nome_plano}'", key=f"del_{nome_plano}"):
                    del treinos_salvos[nome_plano]
                    salvar_treinos_arquivo(treinos_salvos)
                    st.rerun()