from datetime import datetime
from io import BytesIO
import random

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Treinador IA de Bodybuilding",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    "Extremamente ativo (atleta, trabalho físico intenso + treinos diários)": (
        1.9
    ),
}

EXERCICIOS = {
    "Peito": {
        "Básico": [
            "Supino reto com barra (4x8-12)",
            "Supino com halteres (3x10-12)",
            "Flexão de braço (3x12-15)",
            "Crucifixo (3x12-15)",
            "Supino inclinado com barra (3x8-12)",
        ],
        "Intermediário": [
            "Supino inclinado com halteres (4x8-12)",
            "Crucifixo inclinado (3x10-12)",
            "Peck deck (3x12-15)",
            "Supino declinado (3x8-12)",
            "Crossover (3x12-15)",
            "Supino com pegada fechada (3x10-12)",
        ],
        "Avançado": [
            "Supino declinado com halteres (4x6-10)",
            "Crossover com variação de alturas (4x10-12)",
            "Supino com pegada fechada (4x8-10)",
            "Pullover com halteres (3x10-12)",
            "Supino com bandas elásticas (3x6-8)",
            "Dips com peso (3x8-12)",
            "Supino spoto (3x5-8)",
        ],
    },
    "Costas": {
        "Básico": [
            "Remada curvada (4x8-12)",
            "Puxada alta (3x10-12)",
            "Pull-down (3x12-15)",
            "Remada sentado (3x10-12)",
            "Hiperextensão (3x12-15)",
        ],
        "Intermediário": [
            "Barra fixa (4x6-10)",
            "Remada cavalinho (3x8-12)",
            "Pull-over (3x10-12)",
            "Remada unilateral maquina (3x10-12 cada lado)",
            "Puxada frontal (3x10-12)",
            "Deadlift (Levantamento Terra) (3x8-10)",
        ],
        "Avançado": [
            "Remada unilateral maquina (3x10-12 cada lado)",
            "Puxada frontal com pegada pronada (4x8-10)",
            "Deadlift (Levantamento Terra) (4x5-8)",
            "Pull-up com peso (3x6-8)",
            "Remada T-bar (3x8-10)",
            "Pulldown com corda atrás da cabeça (3x10-12)",
        ],
    },
    "Pernas": {
        "Básico": [
            "Agachamento livre (4x8-12)",
            "Leg press (3x10-12)",
            "Cadeira extensora (3x12-15)",
            "Mesa flexora (3x10-12)",
            "Panturrilha em pé (3x15-20)",
        ],
        "Intermediário": [
            "Agachamento frontal (4x8-10)",
            "Avanço com halteres (3x10-12 cada perna)",
            "Stiff (Levantamento Terra Romeno) (3x8-12)",
            "Leg press unilateral (3x10-12 cada perna)",
            "Cadeira flexora (3x10-12)",
            "Panturrilha sentado (3x15-20)",
            "Elevação pélvica (Hip Thrust) (3x10-15)",
        ],
        "Avançado": [
            "Agachamento sumô com barra (4x6-10)",
            "Levantamento Terra Romeno (RDL) (4x8-10)",
            "Panturrilha no leg press (4x15-20)",
            "Bulgarian split squat (Agachamento Búlgaro) (3x8-10 cada perna)",
            "Hack squat (3x8-10)",
            "Good morning (3x8-10)",
            "Extensão de perna unilateral (3x10-12 cada perna)",
            "Flexora nórdica (Nordic Hamstring Curl) (3x falha)",
        ],
    },
    "Ombros": {
        "Básico": [
            "Desenvolvimento com halteres (4x8-12)",
            "Elevação lateral (3x10-12)",
            "Remada alta com barra ou halteres (3x10-12)",
            "Elevação frontal com halteres (3x10-12)",
            "Crucifixo inverso com halteres (3x12-15)",
        ],
        "Intermediário": [
            "Desenvolvimento militar com barra (em pé) (4x8-10)",
            "Elevação lateral inclinada no banco (3x10-12)",
            "Elevação frontal com barra (3x8-12)",
            "Crucifixo inverso na máquina (Peck Deck Invertido) (3x10-12)",
            "Arnold press (3x8-10)",
            "Face pull (3x12-15)",
            "Encolhimento com halteres (Shrugs) (3x10-15)",
        ],
        "Avançado": [
            "Arnold press sentado (4x6-10)",
            "Elevação posterior com halteres no banco inclinado (4x10-12)",
            "Face pull com corda na polia alta (4x12-15)",
            (
                "Desenvolvimento com barra por trás da nuca (cuidado com a"
                " mobilidade) (3x6-8)"
            ),
            "Elevação lateral com rotação (Lu Raises) (3x10-12)",
            "Push Press (3x5-8)",
            (
                "Encolhimento com barra por trás (Behind-the-Back Shrugs)"
                " (3x10-12)"
            ),
        ],
    },
    "Tríceps": {
        "Básico": [
            "Tríceps pulley com barra reta (4x10-12)",
            "Tríceps testa com barra EZ ou halteres (3x8-12)",
            "Mergulho no banco (3x10-15)",
            (
                "Extensão de tríceps com haltere acima da cabeça (duas mãos)"
                " (3x10-12)"
            ),
            "Tríceps kickback (coice) (3x12-15 por braço)",
        ],
        "Intermediário": [
            "Tríceps pulley com corda (4x10-12)",
            "Tríceps francês com barra EZ (deitado ou sentado) (3x8-10)",
            "Mergulho entre bancos com peso (3x8-12)",
            (
                "Extensão unilateral com haltere acima da cabeça (3x10-12 cada"
                " braço)"
            ),
            "Tríceps no cabo com pegada inversa (3x10-12)",
            (
                "Paralelas (Dips) com foco no tríceps (3x até a falha ou com"
                " peso)"
            ),
        ],
        "Avançado": [
            "Supino fechado (Close-Grip Bench Press) (4x6-10)",
            (
                "Extensão unilateral com corda na polia alta (Overhead Cable"
                " Extension) (4x10-12 por braço)"
            ),
            (
                "Tríceps no cabo com variação de pegadas (barra V, corda,"
                " unilateral) (4x8-12)"
            ),
            "Tríceps testa com barra W (3x6-8)",
            "Mergulho em paralelas com peso adicional (Weighted Dips) (3x6-8)",
            "JM Press (3x5-8)",
            "Floor Press com pegada fechada (3x8-10)",
        ],
    },
    "Bíceps": {
        "Básico": [
            "Rosca direta com barra reta ou EZ (4x8-12)",
            "Rosca martelo com halteres (3x10-12)",
            "Rosca concentrada com haltere (3x10-12 por braço)",
            "Rosca Scott com barra W ou halteres (3x10-12)",
            "Rosca inversa com barra (3x10-12)",
        ],
        "Intermediário": [
            "Rosca alternada com halteres (sentado ou em pé) (4x8-10 cada braço)",
            "Rosca 21 com barra (3x21)",
            "Rosca Scott com barra EZ (pegada fechada e aberta) (3x8-10)",
            "Rosca spider com barra ou halteres (3x10-12)",
            "Rosca com cabo na polia baixa (com barra ou corda) (3x10-12)",
            "Rosca no banco inclinado com halteres (3x8-10)",
        ],
        "Avançado": [
            "Rosca spider com barra W (4x8-10)",
            "Rosca inversa com barra grossa (Fat Gripz) (4x8-10)",
            "Rosca com cabo na polia alta (simulando dupla bíceps) (4x8-12)",
            (
                "Rosca concentrada com halteres (com pico de contração)"
                " (3x10-12 cada braço)"
            ),
            "Rosca Zottman (3x10-12)",
            "Rosca com bandas elásticas (para variação de tensão) (3x12-15)",
            "Chin-ups com pegada supinada (foco no bíceps) (3x até a falha)",
        ],
    },
    "Abdômen": {
        "Básico": [
            "Abdominal crunch ( Supra) (3x15-20)",
            "Prancha frontal (Plank) (3x30-60 seg)",
            "Elevação de pernas deitado (Infra) (3x12-15)",
            "Russian twist (Giro Russo) sem peso (3x15 cada lado)",
            "Abdominal bicicleta no chão (3x15-20 cada lado)",
        ],
        "Intermediário": [
            "Prancha lateral (Side Plank) (3x30-45 seg cada lado)",
            (
                "Elevação de pernas suspenso na barra (Hanging Leg Raise)"
                " (3x10-12)"
            ),
            "Abdominal com peso no peito (Weighted Crunch) (3x12-15)",
            "Woodchopper com cabo ou halter (Lenhador) (3x10-12 cada lado)",
            "Abdominal na roda (Ab Wheel Rollout) - joelhos no chão (3x8-12)",
            "Dragon flag (negativas ou com assistência) (3x6-8)",
        ],
        "Avançado": [
            "Dragon flag completo (4x6-8)",
            (
                "Hanging Windshield Wipers (Limpador de Para-brisa Suspenso)"
                " (3x8-10 cada lado)"
            ),
            "Abdominal com cabo na polia alta (Cable Crunch) (4x12-15)",
            "Prancha com movimento (ex: tocar ombros, estender braços) (3x45-60 seg)",
            "Abdominal canivete (V-ups) (3x12-15)",
            "Toes-to-bar (Pés na Barra) (3x8-10)",
            "Abdominal na roda (Ab Wheel Rollout) - em pé (3x6-10)",
        ],
    },
}

ALIMENTOS = {
    "Proteínas": [
        "Frango (peito grelhado/cozido) (100g)",
        "Peito de peru defumado (100g)",
        "Peixe branco (tilápia, linguado, merluza) (100g)",
        "Salmão grelhado/assado (100g)",
        "Atum em água (lata 80g drenado)",
        "Carne vermelha magra (patinho, alcatra, maminha) (100g)",
        "Ovos inteiros cozidos (2 unidades grandes)",
        "Clara de ovo pasteurizada (equivalente a 4 claras)",
        "Queijo cottage (100g)",
        "Iogurte grego natural desnatado (1 pote 100-150g)",
        "Whey protein isolado/concentrado (1 dose/scoop)",
        "Camarão cozido (100g)",
        "Lentilha cozida (1 xícara ~180g)",
        "Grão de bico cozido (1 xícara ~160g)",
        "Tofu firme (100g)",
        "Carne de porco magra (lombo assado/grelhado) (100g)",
        "Ricota fresca (50g)",
        "Proteína de soja texturizada hidratada (100g)",
        (
            "Sardinha em lata (com óleo ou água, drenada) (1 lata pequena"
            " ~80g)"
        ),
        "Kefir natural (200ml)",
        "Queijo minas frescal (1 fatia média ~50g)",
    ],
    "Carboidratos": [
        "Arroz integral cozido (1 xícara ~150g)",
        "Batata-doce cozida/assada (1 média ~150g)",
        "Quinoa cozida (1 xícara ~180g)",
        "Aveia em flocos (4 colheres de sopa ~40g)",
        "Pão integral (100% integral) (2 fatias)",
        "Massa integral cozida (1 xícara ~140g)",
        "Batata inglesa cozida/assada (1 média ~150g)",
        "Inhame cozido (1 médio ~150g)",
        "Mandioca (aipim/macaxeira) cozida (1 pedaço médio ~150g)",
        (
            "Frutas variadas (1 porção média - ex: 1 maçã, 1 pera, 1 laranja, 1"
            " cacho pequeno de uvas, 1 fatia de abacaxi)"
        ),
        "Banana prata/nanica (1 unidade média)",
        "Maçã (Gala, Fuji) (1 unidade média)",
        "Mamão formosa (1 fatia média)",
        "Melancia (1 fatia grande)",
        "Manga (Tommy, Palmer) (1/2 unidade média)",
        "Pasta de amendoim integral sem açúcar (1 colher de sopa ~15g)",
        "Granola sem açúcar adicionado (4 colheres de sopa ~40g)",
        "Cuscuz nordestino cozido (1/2 xícara ~100g)",
        "Milho verde cozido (1 espiga média)",
        "Tapioca (goma hidratada) (3 colheres de sopa)",
        "Pão sírio integral (1 unidade pequena)",
        "Feijão (carioca, preto, fradinho) cozido (1 concha média ~100g)",
        "Ervilha fresca/congelada cozida (1/2 xícara ~80g)",
        "Arroz branco cozido (1 xícara ~150g)",
        "Pão de centeio (2 fatias)",
        "Biscoito de arroz integral (4 unidades)",
        "Beterraba cozida (1 pequena ~100g)",
        "Cenoura cozida (1 média ~100g)",
    ],
    "Gorduras": [
        (
            "Abacate (1/2 unidade pequena ou 1/4 unidade grande ~50-70g)"
        ),
        "Castanha do Pará (2-3 unidades)",
        "Castanha de caju (10-15 unidades ou punhado pequeno ~20g)",
        "Amêndoas (10-15 unidades ou punhado pequeno ~20g)",
        "Nozes (4-5 metades ou punhado pequeno ~20g)",
        "Azeite de oliva extra virgem (1 colher de sopa ~10ml)",
        "Sementes de linhaça (dourada/marrom) (1-2 colheres de sopa)",
        "Sementes de chia (1-2 colheres de sopa)",
        "Sementes de girassol sem casca (1-2 colheres de sopa)",
        "Gema de ovo (incluída nos ovos inteiros)",
        "Azeitonas (verdes/pretas) (10-15 unidades médias)",
        "Manteiga de amêndoa/castanhas (1 colher de sopa ~15g)",
        "Óleo de coco extra virgem (1 colher de chá ~5ml)",
        "Queijo amarelo (ex: muçarela, prato, cheddar) (1 fatia grossa ~30g)",
        "Iogurte integral natural (1 pote 100-150g)",
        "Tahine (pasta de gergelim) (1 colher de sopa ~15g)",
        "Amendoim torrado sem sal (punhado pequeno ~30g)",
        "Chocolate amargo (70% cacau ou mais) (2-3 quadradinhos ~20-30g)",
        "Óleo de abacate (1 colher de chá ~5ml)",
        "Coco ralado sem açúcar (1-2 colheres de sopa)",
        "Manteiga ghee (1 colher de chá ~5g)",
    ],
    "Vegetais": [
        "Brócolis (cozido/cru - 1 xícara)",
        "Espinafre (cru - 2 xícaras; cozido - 1 xícara)",
        "Abóbora cabotiá/moranga (cozida - 1 xícara)",
        "Couve-flor (cozida/crua - 1 xícara)",
        "Pepino (1 unidade média)",
        "Tomate (1 unidade média ou 10-12 tomates cereja)",
        "Alface (americana, romana, crespa, roxa - à vontade)",
        "Rúcula (à vontade)",
        "Repolho (branco/roxo - picado - 1 xícara)",
        "Cenoura (crua ralada/cozida - 1 unidade média)",
        "Beterraba (cozida/ralada crua - 1/2 unidade média)",
        "Berinjela (cozida - 1 xícara)",
        "Abobrinha (1 unidade média)",
        "Pimentão (verde, amarelo, vermelho - 1/2 unidade média)",
        "Cogumelos (paris, shitake, shimeji - fatiado - 1 xícara)",
        "Couve (folhas picadas - 1-2 xícaras)",
        "Agrião (à vontade)",
        "Vagem (cozida - 1 xícara)",
        "Quiabo (cozido - 1 xícara)",
        "Aspargos (6-8 talos médios)",
        "Palmito (pupunha/açaí - 1/2 xícara)",
        "Alho-poró (picado - 1/2 xícara)",
        "Cebola (branca/roxa - 1/2 unidade média)",
        "Salsão/Aipo (2-3 talos)",
        "Nabo (picado - 1/2 xícara)",
        "Rabanete (4-5 unidades)",
        "Jiló (2-3 unidades cozidas)",
        "Mostarda (folhas - à vontade)",
        "Escarola (à vontade)",
    ],
}


# --- FUNÇÕES AUXILIARES COM CACHE ---
@st.cache_data
def calcular_tmb(peso, altura, idade, genero):
  if genero == "Masculino":
    return (10 * peso) + (6.25 * altura) - (5 * idade) + 5
  else:
    return (10 * peso) + (6.25 * altura) - (5 * idade) - 161


@st.cache_data
def calcular_macros(
    peso, altura, idade, genero, meta, experiencia, atividade, dieta_selecionada
):
  tmb = calcular_tmb(peso, altura, idade, genero)
  multiplicador_atividade = NIVEIS_ATIVIDADE_MULTIPLICADORES.get(atividade, 1.55)
  calorias = tmb * multiplicador_atividade

  if meta == "Crescimento":
    calorias += (
        300
        if experiencia == "Básico"
        else (400 if experiencia == "Intermediário" else 500)
    )
  elif meta == "Emagrecimento":
    calorias -= (
        300
        if experiencia == "Básico"
        else (400 if experiencia == "Intermediário" else 500)
    )

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
    calorias_gorduras = (
        calorias_restantes_para_carb_gord - calorias_carboidratos
    )
    gorduras_total_g = calorias_gorduras / 9
    if gorduras_total_g < peso * gorduras_min_g_kg:
      gorduras_total_g = peso * gorduras_min_g_kg
  elif dieta_selecionada == "Low Carb":
    carboidratos_total_g = min(
        max(
            50,
            (
                calorias_restantes_para_carb_gord
                * random.uniform(0.20, 0.30)
            )
            / 4,
        ),
        150,
    )
    calorias_carboidratos = carboidratos_total_g * 4
    calorias_gorduras = (
        calorias_restantes_para_carb_gord - calorias_carboidratos
    )
    gorduras_total_g = calorias_gorduras / 9
  else:
    perc_carb_restante = 0.50
    if meta == "Crescimento" or dieta_selecionada == "Crescimento (Hipercalórica)":
      perc_carb_restante = random.uniform(0.55, 0.65)
    elif (
        meta == "Emagrecimento"
        or dieta_selecionada == "Emagrecimento (Hipocalórica)"
    ):
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

  calorias_recalculadas = (
      (proteinas_total_g * 4)
      + (carboidratos_total_g * 4)
      + (gorduras_total_g * 9)
  )

  return {
      "calorias": int(calorias_recalculadas),
      "proteinas": int(proteinas_total_g),
      "carboidratos": int(carboidratos_total_g),
      "gorduras": int(gorduras_total_g),
  }


@st.cache_data
def gerar_treino_completo(dias_treino, experiencia, meta):
  treino = {}
  if dias_treino == 1:
    split_escolhido = "Full Body A"
    grupos_por_dia = {1: ["Peito", "Costas", "Pernas", "Ombros"]}
  elif dias_treino == 2:
    split_escolhido = "Upper/Lower A/B"
    grupos_por_dia = {
        1: ["Peito", "Ombros", "Tríceps"],
        2: ["Pernas", "Costas", "Bíceps"],
    }
  elif dias_treino == 3:
    opcao_3d = random.choice(["PPL", "FullBodyx3"])
    if opcao_3d == "PPL":
      split_escolhido = "Push/Pull/Legs (PPL)"
      grupos_por_dia = {
          1: ["Peito", "Ombros", "Tríceps"],
          2: ["Costas", "Bíceps", "Abdômen"],
          3: ["Pernas"],
      }
    else:
      split_escolhido = "Full Body 3x (A/B/C)"
      grupos_por_dia = {
          1: ["Peito", "Costas", "Pernas"],
          2: ["Ombros", "Bíceps", "Tríceps", "Abdômen"],
          3: ["Peito", "Costas", "Pernas"],
      }
  elif dias_treino == 4:
    opcao_4d = random.choice(["UpperLower", "BroSplit"])
    if opcao_4d == "UpperLower":
      split_escolhido = "Upper/Lower 2x (A/B)"
      grupos_por_dia = {
          1: ["Peito", "Ombros", "Tríceps"],
          2: ["Pernas", "Abdômen"],
          3: ["Costas", "Bíceps", "Ombros"],
          4: ["Pernas"],
      }
    else:
      split_escolhido = "Bro Split Adaptado 4 dias"
      grupos_por_dia = {
          1: ["Peito", "Tríceps"],
          2: ["Costas", "Bíceps"],
          3: ["Pernas", "Abdômen"],
          4: ["Ombros", "Abdômen"],
      }
  elif dias_treino == 5:
    split_escolhido = "Bro Split 5 dias (Clássico)"
    grupos_por_dia = {
        1: ["Peito"],
        2: ["Costas"],
        3: ["Pernas"],
        4: ["Ombros", "Abdômen"],
        5: ["Bíceps", "Tríceps"],
    }
  elif dias_treino == 6:
    split_escolhido = "Push/Pull/Legs 2x (PPL PPL)"
    grupos_por_dia = {
        1: ["Peito", "Ombros", "Tríceps"],
        2: ["Costas", "Bíceps"],
        3: ["Pernas", "Abdômen"],
        4: ["Peito", "Ombros", "Tríceps"],
        5: ["Costas", "Bíceps"],
        6: ["Pernas"],
    }
  else:
    split_escolhido = "Alta Frequência/Ênfase (Avançado)"
    grupos_por_dia = {
        1: ["Peito", "Tríceps"],
        2: ["Costas", "Bíceps"],
        3: ["Pernas (Quadríceps)"],
        4: ["Ombros", "Abdômen"],
        5: ["Peito (Superior/Deload)"],
        6: ["Costas (Largura/Deload)"],
        7: ["Pernas (Posterior/Glúteos)", "Bíceps", "Tríceps"],
    }

  for dia_num in range(1, dias_treino + 1):
    nome_dia = f"Dia {dia_num}"
    treino[nome_dia] = {}
    grupos_do_dia_atuais = grupos_por_dia.get(dia_num, [])
    grupos_do_dia_normalizados = [
        g.split(" (")[0].strip() for g in grupos_do_dia_atuais
    ]

    for i_grupo, grupo_muscular_original in enumerate(grupos_do_dia_atuais):
      grupo_muscular_normalizado = grupos_do_dia_normalizados[i_grupo]
      if grupo_muscular_normalizado not in EXERCICIOS:
        continue

      exercicios_disponiveis = EXERCICIOS[grupo_muscular_normalizado].get(
          experiencia, EXERCICIOS[grupo_muscular_normalizado]["Básico"]
      )
      if not exercicios_disponiveis:
        continue

      num_exercicios = 2
      if len(grupos_do_dia_normalizados) == 1:
        num_exercicios = (
            random.randint(3, 4) if experiencia != "Avançado" else random.randint(4, 5)
        )
      elif len(grupos_do_dia_normalizados) == 2:
        num_exercicios = (
            random.randint(2, 3) if experiencia != "Avançado" else 3
        )
      elif (
          grupo_muscular_normalizado in ["Bíceps", "Tríceps", "Abdômen"]
          and len(grupos_do_dia_normalizados) > 2
      ):
        num_exercicios = random.randint(1, 2)

      if dias_treino <= 3 and len(grupos_do_dia_normalizados) >= 3:
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
      "Café da manhã": [],
      "Lanche da manhã": [],
      "Almoço": [],
      "Lanche da tarde": [],
      "Jantar": [],
      "Ceia": [],
  }
  perc_cal_refeicao = {
      "Café da manhã": 0.20,
      "Lanche da manhã": 0.10,
      "Almoço": 0.30,
      "Lanche da tarde": 0.15,
      "Jantar": 0.20,
      "Ceia": 0.05,
  }
  if (
      user_data["meta"] == "Emagrecimento"
      or dieta_tipo_selecionado == "Emagrecimento (Hipocalórica)"
  ):
    perc_cal_refeicao["Ceia"] = 0.00
    perc_cal_refeicao["Lanche da manhã"] = 0.05
    perc_cal_refeicao["Lanche da tarde"] = 0.10
    perc_cal_refeicao["Almoço"] = 0.35
  elif (
      user_data["meta"] == "Crescimento"
      or dieta_tipo_selecionado == "Crescimento (Hipercalórica)"
  ):
    perc_cal_refeicao["Lanche da manhã"] = 0.15
    perc_cal_refeicao["Lanche da tarde"] = 0.15
    perc_cal_refeicao["Ceia"] = 0.10

  dist_macros_ref = {"P": 0.30, "C": 0.40, "F": 0.30}
  if dieta_tipo_selecionado == "Cetogênica":
    dist_macros_ref = {"P": 0.20, "C": 0.05, "F": 0.75}
  elif dieta_tipo_selecionado == "Low Carb":
    dist_macros_ref = {"P": 0.30, "C": 0.20, "F": 0.50}
  elif (
      user_data["meta"] == "Crescimento"
      or dieta_tipo_selecionado == "Crescimento (Hipercalórica)"
  ):
    dist_macros_ref = {"P": 0.30, "C": 0.50, "F": 0.20}
  elif (
      user_data["meta"] == "Emagrecimento"
      or dieta_tipo_selecionado == "Emagrecimento (Hipocalórica)"
  ):
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
      sugestoes_itens.append(
          f"{int(g_p_ref)}g Proteína (ex: {op_p[0]} ou {op_p[1]})"
      )
    if g_c_ref > 5 and ALIMENTOS["Carboidratos"]:
      valid_carbs = ALIMENTOS["Carboidratos"]
      if dieta_tipo_selecionado == "Cetogênica":
        valid_carbs = (
            [
                a
                for a in ALIMENTOS["Gorduras"]
                if "castanha" in a
                or "semente" in a
                or "abacate" in a
                or "coco" in a
            ]
            + [
                v
                for v in ALIMENTOS["Vegetais"]
                if any(
                    k in v for k in ["folhas", "brócolis", "couve-flor", "abobrinha", "pepino"]
                )
            ]
        )
      if not valid_carbs:
        valid_carbs = ["Vegetais de baixo amido"]
      op_c = (
          random.sample(valid_carbs, min(2, len(valid_carbs)))
          if valid_carbs
          else []
      )
      if op_c:
        sugestoes_itens.append(
            f"{int(g_c_ref)}g Carboidratos (ex: {op_c[0]}"
            f"{f' ou {op_c[1]}' if len(op_c)>1 else ''})"
        )
    if g_f_ref > 3 and ALIMENTOS["Gorduras"]:
      op_f = random.sample(ALIMENTOS["Gorduras"], min(2, len(ALIMENTOS["Gorduras"])))
      sugestoes_itens.append(
          f"{int(g_f_ref)}g Gorduras (ex: {op_f[0]} ou {op_f[1]})"
      )
    if refeicao in ["Almoço", "Jantar"] and ALIMENTOS["Vegetais"]:
      op_v = random.sample(ALIMENTOS["Vegetais"], min(2, len(ALIMENTOS["Vegetais"])))
      sugestoes_itens.append(
          f"Vegetais (ex: {op_v[0]}, {op_v[1]} - à vontade ou porções indicadas)"
      )

    if sugestoes_itens:
      refeicoes_plano[refeicao].append(
          f"~{int(cal_ref)} kcal: " + "; ".join(sugestoes_itens)
      )
    else:
      refeicoes_plano[refeicao].append(
          f"~{int(cal_ref)} kcal: Ajustar com base nos macros ou refeição leve."
      )

  if user_data["dias_treino"] > 0:
    refeicoes_plano["Lanche da tarde"].append(
        "<i>Sugestão Pré-Treino (se treinar à tarde/noite):</i>"
        f" {random.choice(ALIMENTOS['Carboidratos'])} +"
        f" {random.choice(ALIMENTOS['Proteínas'])}"
    )
    refeicoes_plano["Jantar"].append(
        "<i>Sugestão Pós-Treino (se jantar for após o treino):</i> Refeição"
        f" completa com {random.choice(ALIMENTOS['Proteínas'])} e"
        f" {random.choice(ALIMENTOS['Carboidratos'])}"
    )
    if "Café da manhã" in refeicoes_plano and user_data["meta"] == "Crescimento":
      refeicoes_plano["Café da manhã"].append(
          "<i>Sugestão Pré-Treino (se treinar de manhã):</i>"
          f" {random.choice(ALIMENTOS['Carboidratos'])} +"
          f" {random.choice(ALIMENTOS['Proteínas'])}"
      )
      refeicoes_plano["Lanche da manhã"].append(
          "<i>Sugestão Pós-Treino (se lanche da manhã for após treino"
          f" matinal):</i> {random.choice(ALIMENTOS['Proteínas'])} +"
          f" {random.choice(ALIMENTOS['Frutas'] if 'Frutas' in ALIMENTOS else ALIMENTOS['Carboidratos'])}"
      )

  return refeicoes_plano


def gerar_pdf(treino, dieta_plano, macros, user_data):
  buffer = BytesIO()
  c = canvas.Canvas(buffer, pagesize=A4)
  width, height = A4

  styles = getSampleStyleSheet()
  title_style = ParagraphStyle(
      "TitleStyle",
      parent=styles["Title"],
      fontSize=18,
      alignment=1,
      spaceAfter=20,
      leading=22,
  )
  heading_style = ParagraphStyle(
      "HeadingStyle",
      parent=styles["h2"],
      fontSize=14,
      spaceAfter=10,
      spaceBefore=12,
      leading=18,
  )
  body_style = ParagraphStyle(
      "BodyStyle",
      parent=styles["Normal"],
      fontSize=10,
      leading=14,
      spaceAfter=6,
  )
  user_info_style = ParagraphStyle(
      "UserInfoStyle", parent=styles["Normal"], fontSize=9, leading=12, spaceAfter=10
  )
  table_header_style = ParagraphStyle(
      "TableHeaderStyle",
      parent=styles["Normal"],
      fontSize=10,
      fontName="Helvetica-Bold",
      alignment=0,
  )
  table_cell_style = ParagraphStyle(
      "TableCellStyle", parent=styles["Normal"], fontSize=10, alignment=0
  )

  story = []
  story.append(Paragraph("<b>PLANO COMPLETO DE TREINO E DIETA</b>", title_style))

  user_info_text = f"""
    <b>Nome:</b> {user_data.get('nome', 'N/A')}<br/>
    <b>Idade:</b> {user_data['idade']} anos | <b>Altura:</b> {user_data['altura']} cm | <b>Peso:</b> {user_data['peso']} kg<br/>
    <b>Gênero:</b> {user_data['genero']} | <b>Nível:</b> {user_data['experiencia']} | <b>Meta:</b> {user_data['meta']}<br/>
    <b>Dias de Treino:</b> {user_data['dias_treino']}/semana | <b>Dieta:</b> {user_data['dieta_selecionada']}<br/>
    <b>Data da Geração:</b> {datetime.now().strftime('%d/%m/%Y')}
    """
  story.append(Paragraph(user_info_text, user_info_style))

  story.append(Paragraph("<b>MACROS DIÁRIOS ESTIMADOS</b>", heading_style))
  macros_data_pdf = [
      [
          Paragraph("<b>Nutriente</b>", table_header_style),
          Paragraph("<b>Quantidade</b>", table_header_style),
      ],
      [
          Paragraph("Calorias:", table_cell_style),
          Paragraph(f"{macros['calorias']} kcal", table_cell_style),
      ],
      [
          Paragraph("Proteínas:", table_cell_style),
          Paragraph(f"{macros['proteinas']} g", table_cell_style),
      ],
      [
          Paragraph("Carboidratos:", table_cell_style),
          Paragraph(f"{macros['carboidratos']} g", table_cell_style),
      ],
      [
          Paragraph("Gorduras:", table_cell_style),
          Paragraph(f"{macros['gorduras']} g", table_cell_style),
      ],
  ]
  macros_table = Table(macros_data_pdf, colWidths=[width * 0.3, width * 0.5])
  macros_table.setStyle(
      TableStyle([
          ("GRID", (0, 0), (-1, -1), 0.5, (0, 0, 0)),
          ("BACKGROUND", (0, 0), (-1, 0), (0.8, 0.8, 0.8)),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
          ("TOPPADDING", (0, 0), (-1, -1), 8),
      ])
  )
  story.append(macros_table)
  story.append(Paragraph("<br/>", body_style))

  story.append(Paragraph("<b>PLANO DE TREINO SEMANAL</b>", heading_style))
  for dia, exercicios in treino.items():
    story.append(
        Paragraph(
            f"<b>{dia.upper()}</b>",
            ParagraphStyle(
                "DiaTreino",
                parent=body_style,
                fontName="Helvetica-Bold",
                spaceBefore=6,
            ),
        )
    )
    if not exercicios:
      story.append(Paragraph("• Descanso ou dia livre.", body_style))
    else:
      for grupo_chave_ex, exercicio_desc in exercicios.items():
        story.append(
            Paragraph(
                f"• <b>{grupo_chave_ex.replace(' - Ex. ', ' Exercício ')}:</b>"
                f" {exercicio_desc}",
                body_style,
            )
        )
    story.append(Paragraph("<br/>", body_style))

  story.append(
      Paragraph("<b>PLANO ALIMENTAR DIÁRIO (SUGESTÕES)</b>", heading_style)
  )
  for refeicao, itens in dieta_plano.items():
    story.append(
        Paragraph(
            f"<b>{refeicao.upper()}</b>",
            ParagraphStyle(
                "RefeicaoTitulo",
                parent=body_style,
                fontName="Helvetica-Bold",
                spaceBefore=6,
            ),
        )
    )
    if not itens or "Refeição opcional" in itens[0]:
      story.append(
          Paragraph("• Nenhuma sugestão específica ou refeição opcional.", body_style)
      )
    else:
      for item_desc in itens:
        item_desc_plain = (
            item_desc.replace("<b>", "")
            .replace("</b>", "")
            .replace("<i>", "")
            .replace("</i>", "")
            .replace("<small>", "")
            .replace("</small>", "")
        )
        story.append(Paragraph(f"• {item_desc_plain}", body_style))
    story.append(Paragraph("<br/>", body_style))

  def draw_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 30, 30, f"Página {doc.page}")
    canvas.restoreState()

  doc = SimpleDocTemplate(
      buffer,
      pagesize=A4,
      topMargin=30,
      bottomMargin=50,
      leftMargin=50,
      rightMargin=50,
  )
  doc.build(
      story, onFirstPage=draw_page_number, onLaterPages=draw_page_number
  )

  pdf = buffer.getvalue()
  buffer.close()
  return pdf


# --- GERENCIAMENTO DE ESTADO (SESSION STATE) ---
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

# --- INTERFACE DO USUÁRIO ---
st.title("💪 Treinador IA de Bodybuilding")
st.markdown("### Seu plano personalizado de treino e dieta com base em IA!")

with st.sidebar:
  st.header("📋 Seus Dados")
  with st.form("user_data_form"):
    nome = st.text_input("Nome (opcional):", placeholder="Ex: João Silva")
    genero = st.radio(
        "Gênero:", ["Masculino", "Feminino"], index=0, horizontal=True
    )
    peso = st.number_input(
        "Peso (kg):", min_value=30.0, max_value=250.0, value=70.0, step=0.5
    )
    altura = st.number_input(
        "Altura (cm):", min_value=100.0, max_value=250.0, value=175.0, step=0.5
    )
    idade = st.number_input("Idade:", min_value=14, max_value=99, value=25, step=1)
    meta = st.selectbox("🎯 Meta Principal:", META_OPCOES, index=0)
    experiencia = st.selectbox(
        "🏋️ Nível de Experiência em Treino:", EXPERIENCIA_OPCOES, index=1
    )
    atividade = st.selectbox(
        "🚶 Nível de Atividade Diária (sem contar treinos):",
        list(NIVEIS_ATIVIDADE_MULTIPLICADORES.keys()),
        index=2,
    )
    dias_treino = st.slider("📅 Dias de treino por semana:", 1, 7, 4)
    dieta_selecionada_usuario = st.selectbox(
        "🥗 Tipo de Dieta Preferencial:",
        DIETA_OPCOES,
        index=0,
        key="dieta_tipo_selectbox",
    )
    submitted = st.form_submit_button("🚀 Gerar Plano Completo Agora!")

  if submitted:
    with st.spinner(
        "🧠 Analisando seus dados e montando o plano perfeito... Aguarde!"
    ):
      st.session_state.user_data_dict = {
          "nome": nome if nome else "Usuário(a)",
          "genero": genero,
          "peso": float(peso),
          "altura": float(altura),
          "idade": int(idade),
          "meta": meta,
          "experiencia": experiencia,
          "atividade": atividade,
          "dias_treino": int(dias_treino),
          "dieta_selecionada": dieta_selecionada_usuario,
      }
      st.session_state.macros = calcular_macros(
          float(peso),
          float(altura),
          int(idade),
          genero,
          meta,
          experiencia,
          atividade,
          dieta_selecionada_usuario,
      )
      st.session_state.treino, st.session_state.split_info = (
          gerar_treino_completo(int(dias_treino), experiencia, meta)
      )
      st.session_state.dieta_plano = gerar_dieta_completa(
          st.session_state.macros,
          dieta_selecionada_usuario,
          st.session_state.user_data_dict,
      )
      st.session_state.plano_gerado = True

if st.session_state.plano_gerado:
  user_data_dict = st.session_state.user_data_dict
  macros = st.session_state.macros
  treino = st.session_state.treino
  split_info = st.session_state.split_info
  dieta_plano = st.session_state.dieta_plano

  st.success(
      f"✅ Plano Personalizado para **{user_data_dict['nome']}** Gerado com"
      " Sucesso!"
  )
  st.balloons()

  st.subheader("📊 Resumo do Plano")
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric("🔥 Calorias Diárias (aprox.)", f"{macros['calorias']} kcal")
    st.metric("🥩 Proteínas (aprox.)", f"{macros['proteinas']} g")
  with col2:
    st.metric("🍚 Carboidratos (aprox.)", f"{macros['carboidratos']} g")
    st.metric("🥑 Gorduras (aprox.)", f"{macros['gorduras']} g")
  with col3:
    st.metric("🗓️ Dias de Treino", f"{user_data_dict['dias_treino']} / semana")
    st.metric("🏆 Nível", user_data_dict['experiencia'])

  st.markdown(
      f"**🎯 Meta Principal:** {user_data_dict['meta']} | **🥗 Dieta Escolhida:**"
      f" {user_data_dict['dieta_selecionada']}"
  )
  st.markdown(
      f"**🏋️‍♂️ Split de Treino:** {split_info} | **🚶 Atividade Diária:**"
      f" {user_data_dict['atividade']}"
  )

  tab_treino, tab_dieta, tab_download = st.tabs(
      [
          "🏋️ Plano de Treino Detalhado",
          "🍽️ Plano Alimentar Sugerido",
          "📥 Download do Plano",
      ]
  )

  with tab_treino:
    st.header("📅 Seu Plano de Treino Semanal")
    if not treino:
      st.warning("Plano de treino não gerado.")
    else:
      for dia, exercicios_dia in treino.items():
        foco_dia_str = (
            ", ".join(set(ex.split(" - ")[0] for ex in exercicios_dia.keys()))
            if exercicios_dia
            else "Descanso"
        )
        with st.expander(f"**{dia.upper()}** - Foco: {foco_dia_str}"):
          if not exercicios_dia:
            st.write("Dia de descanso ou sem exercícios definidos.")
          else:
            for grupo_chave_ex, exercicio_desc in exercicios_dia.items():
              st.markdown(
                  f"💪 **{grupo_chave_ex.replace(' - Ex. ', ' Exercício ')}:**"
                  f" {exercicio_desc}"
              )
          st.markdown("---")
  with tab_dieta:
    st.header("🥗 Seu Plano Alimentar Diário (Sugestões)")
    st.markdown(
        "<small><i>Lembre-se: as quantidades de alimentos são exemplos. Ajuste"
        " conforme suas preferências e os alimentos disponíveis, mantendo os"
        " totais de macros em mente. Consulte um nutricionista para orientações"
        " individualizadas.</i></small>",
        unsafe_allow_html=True,
    )
    if not dieta_plano:
      st.warning("Plano alimentar não gerado.")
    else:
      for refeicao, itens_refeicao in dieta_plano.items():
        with st.expander(f"**{refeicao.upper()}**"):
          if not itens_refeicao or "Refeição opcional" in itens_refeicao[0]:
            st.write("Nenhuma sugestão específica ou refeição opcional.")
          else:
            for item_desc in itens_refeicao:
              st.markdown(f" • {item_desc}")
          st.markdown("---")
  with tab_download:
    st.header("📥 Baixar Seu Plano Completo em PDF")
    st.write("Seu plano personalizado está pronto para download!")
    try:
      pdf_bytes = gerar_pdf(treino, dieta_plano, macros, user_data_dict)
      st.download_button(
          label="⬇️ Baixar Plano em PDF Agora",
          data=pdf_bytes,
          file_name=(
              "plano_ia_bodybuilding_"
              f"{user_data_dict['nome'].replace(' ', '_').lower()}_"
              f"{datetime.now().strftime('%Y%m%d')}.pdf"
          ),
          mime="application/pdf",
          key="download_pdf_button",
      )
    except Exception as e:
      st.error(f"Ocorreu um erro ao gerar o PDF: {e}")
      st.exception(e)
      st.error(
          "Tente novamente. Se o erro persistir, o conteúdo pode ser muito"
          " extenso para o PDF."
      )
    st.markdown("---")
    st.subheader("💡 Dicas Importantes:")
    st.markdown("""
        * **Consistência > Perfeição:** Siga o plano o máximo possível, mas não se culpe por pequenos desvios.
        * **Progressão de Carga:** Aumente pesos/repetições/séries nos treinos gradualmente.
        * **Hidratação e Nutrição:** Beba água e alimente-se bem, mesmo fora das sugestões.
        * **Descanso é Crucial:** Durma bem para recuperação e crescimento muscular.
        * **Ouça seu Corpo:** Dores agudas são diferentes de dores musculares. Descanse se necessário.
        * **Ajustes Profissionais:** Este é um plano gerado por IA. Consulte um nutricionista e um educador físico.
        """)
else:
  st.info(
      "👈 Preencha seus dados na barra lateral e clique em 'Gerar Plano"
      " Completo Agora!' para começar sua jornada!"
  )
  st.markdown(
      """
    ### Transforme seu físico com o poder da Inteligência Artificial! 🚀

    Este aplicativo foi desenhado para ser seu parceiro na busca por seus objetivos de bodybuilding,
    fornecendo um ponto de partida sólido e personalizado.

    **O que esperar?**
    1.  **Dados Precisos:** Quanto mais informações você fornecer, mais ajustado será o plano.
    2.  **Metas Claras:** Defina se quer crescer, emagrecer ou manter o peso.
    3.  **Preferências Respeitadas:** Escolha seus dias de treino e o tipo de dieta que mais se adapta a você.
    4.  **Plano Detalhado:** Receba cálculos de macros, treinos semanais e sugestões alimentares.

    Fitness é uma maratona, não uma corrida de 100 metros. Use este plano como seu mapa inicial e ajuste-o conforme avança!
    """,
      unsafe_allow_html=True,
  )
  if st.button("Ver um Exemplo de Plano (Demonstração)"):
    demo_user_data = {
        "nome": "Atleta Exemplo",
        "genero": "Masculino",
        "peso": 80.0,
        "altura": 180.0,
        "idade": 30,
        "meta": "Crescimento",
        "experiencia": "Intermediário",
        "atividade": list(NIVEIS_ATIVIDADE_MULTIPLICADORES.keys())[2],
        "dias_treino": 5,
        "dieta_selecionada": "Crescimento (Hipercalórica)",
    }
    demo_macros = calcular_macros(
        demo_user_data["peso"],
        demo_user_data["altura"],
        demo_user_data["idade"],
        demo_user_data["genero"],
        demo_user_data["meta"],
        demo_user_data["experiencia"],
        demo_user_data["atividade"],
        demo_user_data["dieta_selecionada"],
    )
    demo_treino, demo_split = gerar_treino_completo(
        demo_user_data["dias_treino"],
        demo_user_data["experiencia"],
        demo_user_data["meta"],
    )
    demo_dieta = gerar_dieta_completa(
        demo_macros, demo_user_data["dieta_selecionada"], demo_user_data
    )

    st.subheader("Exemplo de Plano Gerado:")
    st.write(
        f"**Macros para {demo_user_data['nome']}:** Calorias:"
        f" {demo_macros['calorias']}, Proteínas: {demo_macros['proteinas']}g,"
        f" Carboidratos: {demo_macros['carboidratos']}g, Gorduras:"
        f" {demo_macros['gorduras']}g"
    )
    st.write(f"**Split de Treino:** {demo_split}")

    with st.expander("Exemplo de Treino - Dia 1"):
      if demo_treino and "Dia 1" in demo_treino:
        for ex_key, ex_val in demo_treino["Dia 1"].items():
          st.write(f" - **{ex_key.replace(' - Ex. ', ' Exercício ')}:** {ex_val}")
      else:
        st.write("Sem exercícios para o Dia 1 no exemplo.")

    with st.expander("Exemplo de Dieta - Café da Manhã"):
      if demo_dieta and "Café da manhã" in demo_dieta:
        for item in demo_dieta["Café da manhã"]:
          st.write(f" • {item}")
      else:
        st.write("Sem sugestões para o café da manhã no exemplo.")
    st.caption(
        "Este é apenas um exemplo. Preencha seus dados para um plano"
        " personalizado!"
    )