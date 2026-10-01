Documentação do Projeto: Treinador IA — Modo Monstro
1. Visão Geral do Projeto
O Treinador IA de Bodybuilding é uma aplicação web interativa desenvolvida em Python utilizando o framework Streamlit. O objetivo da ferramenta é automatizar e personalizar a criação de fichas de treino avançadas, cálculos metabólicos (TMB e macronutrientes) e planos alimentares adaptados às metas do atleta (hipertrofia, emagrecimento ou manutenção), incorporando uma identidade visual de estilo Hardcore ("Modo Monstro").

2. Pil tecnológico e Dependências
Linguagem: Python 3.x

Interface Web: Streamlit

Geração de Relatórios: ReportLab (para exportação de fichas em PDF)

Persistência de Dados: Armazenamento local em arquivo JSON (treinos_salvos.json)

Hospedagem e Deploy: Git / GitHub / Streamlit Cloud

Utilitários: urllib.parse (para geração de links dinâmicos de busca no YouTube)

3. Arquitetura e Principais Módulos
A. Cálculos Metabólicos e Nutricionais
Taxa Metabólica Basal (TMB): Calculada com base nas equações de Harris-Benedict adaptadas para gênero, peso, altura e idade.

Fator de Atividade: Multiplicadores dinâmicos que ajustam o gasto calórico diário de acordo com a rotina do usuário (sedentário a extremamente ativo).

Distribuição de Macronutrientes: Ajuste automatizado de proteínas, carboidratos e gorduras conforme o objetivo (Crescimento, Emagrecimento, Manutenção) e o tipo de dieta escolhido (Equilibrada, Hipercalórica, Hipocalórica, Cetogênica ou Low Carb).

B. Gerador de Treinos Inteligente & Híbrido
O sistema suporta múltiplos modelos de periodização e divisões de treino:

Padrões Automáticos: Geração baseada na quantidade de dias de treino selecionados (Full Body, Upper/Lower, PPL, Bro Split, etc.).

Full Body Superior: Divisão focada exclusivamente em membros superiores com alta frequência.

Híbrido (Full Body + Ênfase): Combina dias de treino global com dias específicos voltados para pontos fracos ou especialização (ex: 4 dias de Full Body + 1 dia de ênfase em Pernas).

Personalizado (Assistente de Montagem): Permite ao usuário escolher os grupos musculares de cada dia e selecionar manualmente os exercícios de um banco de dados categorizado (Básico, Intermediário e Avançado). Caso nenhum exercício manual seja marcado, a IA assume o preenchimento automático.

C. Guia de Execução Interativo (YouTube)
Cada exercício gerado ou salvo no aplicativo conta com um botão/link dinâmico integrado que direciona instantaneamente o usuário para uma pesquisa formatada no YouTube ("como executar [nome do exercício] musculação"), facilitando a correção postural na academia.

D. Persistência Local (JSON) e Gerenciamento de Fichas
Os usuários podem salvar seus protocolos de treino e dieta com nomes personalizados.

O sistema armazena os dados no arquivo local treinos_salvos.json, incluindo validações de segurança contra estruturas legadas.

Na aba Meus Planos Salvos, é possível visualizar detalhadamente cada treino, os macros calculados, os links de vídeo e o plano alimentar integrado, além de gerenciar a exclusão de fichas.

E. Exportação em PDF
Utiliza a biblioteca ReportLab para compilar dados do atleta, macros, cronograma semanal de treinos e sugestões alimentares em um documento PDF limpo e formatado para download direto.

4. Identidade Visual (Tema Hardcore / Modo Monstro)
A interface foi customizada via CSS injetado no Streamlit para refletir o universo do fisiculturismo pesado:

Paleta de Cores: Fundo em preto carvão (#0c0c0c), painéis laterais em cinza escuro (#141414) e detalhes de destaque em vermelho sangue/fogo (#e5383b).

Componentes: Botões com gradientes agressivos e efeitos de sombra, cartões de métricas customizados com bordas destacadas em vermelho, e abas de navegação modernas.
