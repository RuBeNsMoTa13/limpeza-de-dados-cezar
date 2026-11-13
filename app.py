import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Trabalho: Análise Prescritiva • Amazon Delivery",
    page_icon="📦",
    layout="wide"
)

# ---------------------------------------------------------
# SELETOR DE IDIOMA DAS VARIÁVEIS (PT-BR OU INGLÊS ORIGINAL)
# ---------------------------------------------------------
st.sidebar.title("🎛️ Configurações e Filtros")
idioma = st.sidebar.radio(
    "🌎 Idioma das Variáveis e Tabelas:",
    options=["🇧🇷 Português (Traduzido)", "🇺🇸 Inglês (Original do CSV)"],
    index=0
)
usar_pt = idioma.startswith("🇧🇷")

# Mapas reversos (PT-BR -> Inglês) caso o usuário queira visualizar no Inglês original sem arquivos extras
PT_PARA_EN_PRODUTO = {
    'Eletrônicos': 'Electronics', 'Livros': 'Books', 'Joias': 'Jewelry', 'Brinquedos': 'Toys',
    'Cuidados com a Pele': 'Skincare', 'Lanches': 'Snacks', 'Ar Livre e Camping': 'Outdoors',
    'Vestuário': 'Apparel', 'Esportes': 'Sports', 'Mercado (Perecíveis)': 'Grocery',
    'Pet Shop': 'Pet Supplies', 'Casa e Decoração': 'Home', 'Cosméticos': 'Cosmetics',
    'Cozinha': 'Kitchen', 'Roupas': 'Clothing', 'Calçados': 'Shoes'
}
PT_PARA_EN_CLIMA = {
    'Ensolarado': 'Sunny', 'Tempestade': 'Stormy', 'Nublado': 'Cloudy', 'Neblina': 'Fog',
    'Ventania': 'Windy', 'Tempestade de Areia': 'Sandstorms', 'Não Informado': 'Unknown'
}
PT_PARA_EN_TRANSITO = {
    'Livre': 'Low', 'Médio': 'Medium', 'Alto': 'High', 'Engarrafamento': 'Jam', 'Não Informado': 'Unknown'
}
PT_PARA_EN_VEICULO = {
    'Moto': 'motorcycle', 'Scooter': 'scooter', 'Van': 'van', 'Bicicleta': 'bicycle'
}
PT_PARA_EN_REGIAO = {
    'Urbana': 'Urban', 'Metropolitana': 'Metropolitan', 'Semiurbana': 'Semi-Urban', 'Outra': 'Other'
}

@st.cache_data
def carregar_dados(em_portugues: bool):
    pedidos = pd.read_csv("amazon_pedidos_limpo.csv")
    estoque = pd.read_csv("amazon_estoque_diario.csv")
    parametros = pd.read_csv("amazon_parametros_produtos.csv")
    pedidos["data_pedido"] = pd.to_datetime(pedidos["data_pedido"])
    estoque["data_pedido"] = pd.to_datetime(estoque["data_pedido"])

    if not em_portugues:
        pedidos["produto"] = pedidos["produto"].replace(PT_PARA_EN_PRODUTO)
        pedidos["clima"] = pedidos["clima"].replace(PT_PARA_EN_CLIMA)
        pedidos["transito"] = pedidos["transito"].replace(PT_PARA_EN_TRANSITO)
        pedidos["veiculo"] = pedidos["veiculo"].replace(PT_PARA_EN_VEICULO)
        pedidos["regiao"] = pedidos["regiao"].replace(PT_PARA_EN_REGIAO)
        pedidos = pedidos.rename(columns={
            "id_pedido": "Order_ID", "data_pedido": "Order_Date", "hora_pedido": "Order_Time",
            "hora_coleta": "Pickup_Time", "produto": "Category", "regiao": "Area",
            "clima": "Weather", "transito": "Traffic", "veiculo": "Vehicle",
            "idade_entregador": "Agent_Age", "nota_entregador": "Agent_Rating",
            "distancia_km": "Distance_km", "tempo_entrega_min": "Delivery_Time",
            "tempo_entrega_horas": "Delivery_Time_Hours", "tempo_entrega_dias": "Delivery_Time_Days"
        })
        estoque["produto"] = estoque["produto"].replace(PT_PARA_EN_PRODUTO)
        estoque = estoque.rename(columns={
            "data_pedido": "Order_Date", "produto": "Category", "demanda_diaria": "Daily_Demand",
            "tempo_medio_horas": "Avg_Delivery_Hours", "tempo_desvio_horas": "Std_Delivery_Hours",
            "distancia_media_km": "Avg_Distance_km"
        })
        parametros["produto"] = parametros["produto"].replace(PT_PARA_EN_PRODUTO)
        parametros = parametros.rename(columns={
            "produto": "Category", "dias_analisados": "Days_Analyzed", "total_pedidos": "Total_Orders",
            "demanda_media_diaria": "Avg_Daily_Demand", "demanda_desvio_diario": "Std_Daily_Demand",
            "tempo_medio_horas": "Avg_Delivery_Hours", "tempo_desvio_horas": "Std_Delivery_Hours",
            "distancia_media_km": "Avg_Distance_km"
        })
    return pedidos, estoque, parametros

try:
    df_pedidos, df_estoque, df_parametros = carregar_dados(usar_pt)
except Exception as e:
    st.error(f"Execute primeiro `python limpeza.py` para gerar as tabelas limpas. Erro: {e}")
    st.stop()

COL_PRODUTO = "produto" if usar_pt else "Category"
COL_CLIMA = "clima" if usar_pt else "Weather"
COL_TRANSITO = "transito" if usar_pt else "Traffic"
COL_VEICULO = "veiculo" if usar_pt else "Vehicle"
COL_TEMPO_MIN = "tempo_entrega_min" if usar_pt else "Delivery_Time"
COL_DISTANCIA = "distancia_km" if usar_pt else "Distance_km"
COL_ESTOQUE_DATA = "data_pedido" if usar_pt else "Order_Date"
COL_ESTOQUE_DEMANDA = "demanda_diaria" if usar_pt else "Daily_Demand"

# ---------------------------------------------------------
# BARRA LATERAL (FILTROS DE PRODUTOS E CENÁRIO)
# ---------------------------------------------------------
st.sidebar.divider()
st.sidebar.markdown("Escolha o **Produto** e as condições de **Clima** e **Trânsito**:")

lista_produtos = sorted(df_pedidos[COL_PRODUTO].unique())
padrao_prod = "Eletrônicos" if usar_pt else "Electronics"
produto_sel = st.sidebar.selectbox(
    f"1. Produto ({COL_PRODUTO}):",
    options=lista_produtos,
    index=lista_produtos.index(padrao_prod) if padrao_prod in lista_produtos else 0
)

lista_climas = sorted(df_pedidos[COL_CLIMA].unique())
clima_sel = st.sidebar.selectbox(
    f"2. Clima ({COL_CLIMA}):",
    options=["Todos"] + lista_climas
)

lista_transitos = sorted(df_pedidos[COL_TRANSITO].unique())
transito_sel = st.sidebar.selectbox(
    f"3. Trânsito ({COL_TRANSITO}):",
    options=["Todos"] + lista_transitos
)

st.sidebar.divider()
st.sidebar.subheader("📦 Parâmetros de Estoque")
dias_reposicao = st.sidebar.slider(
    "Dias para repor o estoque:",
    min_value=1, max_value=10, value=3
)
margem_seguranca_pct = st.sidebar.slider(
    "Reserva de Segurança (%):",
    min_value=0, max_value=100, value=20, step=5
)

# ---------------------------------------------------------
# FILTRAR DADOS DO PRODUTO E CENÁRIO
# ---------------------------------------------------------
df_prod = df_pedidos[df_pedidos[COL_PRODUTO] == produto_sel].copy()
df_cenario = df_prod.copy()

if clima_sel != "Todos":
    df_cenario = df_cenario[df_cenario[COL_CLIMA] == clima_sel]
if transito_sel != "Todos":
    df_cenario = df_cenario[df_cenario[COL_TRANSITO] == transito_sel]

if df_cenario.empty:
    st.warning("Não há entregas para essa combinação exata. Mostrando todos os dados do produto.")
    df_cenario = df_prod.copy()

df_diario_prod = df_estoque[df_estoque[COL_PRODUTO] == produto_sel].sort_values(COL_ESTOQUE_DATA).reset_index(drop=True)
df_diario_prod["dia_num"] = np.arange(1, len(df_diario_prod) + 1)

# ---------------------------------------------------------
# CÁLCULOS E REGRESSÃO LINEAR (PESSOA 2)
# ---------------------------------------------------------
total_pedidos_prod = len(df_prod)
pedidos_no_cenario = len(df_cenario)
media_pedidos_dia = df_diario_prod[COL_ESTOQUE_DEMANDA].mean()
desvio_pedidos_dia = df_diario_prod[COL_ESTOQUE_DEMANDA].std()

x_dias = df_diario_prod["dia_num"].values
y_demanda = df_diario_prod[COL_ESTOQUE_DEMANDA].values
coef_a_dem, coef_b_dem = np.polyfit(x_dias, y_demanda, 1)
df_diario_prod["demanda_tendencia"] = (coef_a_dem * x_dias + coef_b_dem).round(2)

x_dist = df_cenario[COL_DISTANCIA].values
y_tempo = df_cenario[COL_TEMPO_MIN].values
if len(x_dist) > 1 and np.std(x_dist) > 0:
    coef_a_dist, coef_b_dist = np.polyfit(x_dist, y_tempo, 1)
else:
    coef_a_dist, coef_b_dist = 0.0, float(np.mean(y_tempo))

tempo_medio_geral_min = df_prod[COL_TEMPO_MIN].mean()
tempo_medio_cenario_min = df_cenario[COL_TEMPO_MIN].mean()
diferenca_tempo_min = tempo_medio_cenario_min - tempo_medio_geral_min

estoque_basico = media_pedidos_dia * dias_reposicao
fator_atraso = tempo_medio_cenario_min / tempo_medio_geral_min if tempo_medio_geral_min > 0 else 1.0
reserva_seguranca = estoque_basico * (margem_seguranca_pct / 100.0) * fator_atraso
ponto_de_pedido = round(estoque_basico + reserva_seguranca)

estoque_atual = ponto_de_pedido * 2
lote_reposicao = round(media_pedidos_dia * dias_reposicao * 1.5)
historico_sim = []

for _, linha in df_diario_prod.iterrows():
    vendas_hoje = int(linha[COL_ESTOQUE_DEMANDA])
    estoque_atual -= vendas_hoje
    pediu_reposicao = "Não"
    if estoque_atual <= ponto_de_pedido:
        estoque_atual += lote_reposicao
        pediu_reposicao = f"Sim (+{lote_reposicao} un)"

    historico_sim.append({
        "dia_numero": int(linha["dia_num"]),
        "data": linha[COL_ESTOQUE_DATA],
        "demanda_real_dia": vendas_hoje,
        "demanda_regressao_linear": linha["demanda_tendencia"],
        "estoque_fim_do_dia": max(0, estoque_atual),
        "acionou_reposicao": pediu_reposicao
    })

df_sim_real = pd.DataFrame(historico_sim)

ranking_veiculos = (
    df_cenario.groupby(COL_VEICULO)[COL_TEMPO_MIN]
    .agg(tempo_medio_min="mean", quantidade_entregas="count")
    .reset_index()
    .sort_values("tempo_medio_min")
)
melhor_veiculo = ranking_veiculos.iloc[0][COL_VEICULO]
melhor_tempo = ranking_veiculos.iloc[0]["tempo_medio_min"]

# ---------------------------------------------------------
# CABEÇALHO E MÉTRICAS PRINCIPAIS
# ---------------------------------------------------------
st.title("📦 Análise Prescritiva • Estudo de Caso Amazon Delivery")
st.markdown(
    f"Painel integrando **Parte 1 (Tratamento de Dados)**, **Parte 2 (Modelagem Matemática: Regressão Linear e Dispersão)** "
    f"e **Parte 3 (Interface Interativa Streamlit)**. Idioma ativo: **{idioma}** | Produto: **{produto_sel}**."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "1. Demanda Média Diária",
    f"{media_pedidos_dia:.1f} un/dia",
    f"Desvio: ±{desvio_pedidos_dia:.1f} un | Total: {total_pedidos_prod}"
)
c2.metric(
    "2. Equação da Demanda (Regressão)",
    f"y = {coef_a_dem:+.2f}x + {coef_b_dem:.1f}",
    "Tendência diária (x = dia)"
)
c3.metric(
    "3. Tempo Médio de Entrega",
    f"{tempo_medio_cenario_min:.0f} min ({tempo_medio_cenario_min/60:.1f} h)",
    f"{diferenca_tempo_min:+.0f} min vs média geral",
    delta_color="inverse"
)
c4.metric(
    "4. Ponto de Reposição (Estoque)",
    f"{ponto_de_pedido} unidades",
    f"Inclui +{round(reserva_seguranca)} un. de segurança"
)

st.divider()

aba1, aba2, aba3, aba4 = st.tabs([
    "🧹 Parte 1: Tratamento de Dados e Tabelas",
    "📐 Parte 2: Regressão Linear e Diagramas de Dispersão",
    "🌦️ Parte 3A: Análise de Sensibilidade e Otimização",
    "📉 Parte 3B: Comportamento do Estoque no Tempo"
])

with aba1:
    st.subheader("Parte 1 (Tratamento de Dados): Limpeza e Tabelas Prontas para os Cálculos")
    st.info(
        "💡 **O que a Parte 1 entrega:** Base do Kaggle higienizada (`43.739` entregas válidas, `0` valores vazios), "
        "com todas as variáveis traduzidas para **Português (PT-BR)** (ou **Inglês Original**, basta trocar no menu esquerdo)."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Dicionário de Variáveis (Português PT-BR ↔ Inglês Original)")
        df_dic = pd.DataFrame([
            {"Variável PT-BR": "id_pedido", "Original (Inglês)": "Order_ID", "Descrição": "Identificador único da entrega"},
            {"Variável PT-BR": "data_pedido", "Original (Inglês)": "Order_Date", "Descrição": "Data do pedido (44 dias analisados)"},
            {"Variável PT-BR": "hora_pedido", "Original (Inglês)": "Order_Time", "Descrição": "Hora em que o pedido foi realizado"},
            {"Variável PT-BR": "hora_coleta", "Original (Inglês)": "Pickup_Time", "Descrição": "Hora em que o entregador coletou na loja"},
            {"Variável PT-BR": "produto", "Original (Inglês)": "Category", "Descrição": "Categoria do produto (16 categorias)"},
            {"Variável PT-BR": "regiao", "Original (Inglês)": "Area", "Descrição": "Tipo de região (Urbana, Metropolitana, etc.)"},
            {"Variável PT-BR": "clima", "Original (Inglês)": "Weather", "Descrição": "Condição climática na entrega"},
            {"Variável PT-BR": "transito", "Original (Inglês)": "Traffic", "Descrição": "Nível de trânsito na entrega"},
            {"Variável PT-BR": "veiculo", "Original (Inglês)": "Vehicle", "Descrição": "Veículo utilizado pelo entregador"},
            {"Variável PT-BR": "idade_entregador", "Original (Inglês)": "Agent_Age", "Descrição": "Idade do entregador"},
            {"Variável PT-BR": "nota_entregador", "Original (Inglês)": "Agent_Rating", "Descrição": "Avaliação do entregador"},
            {"Variável PT-BR": "distancia_km", "Original (Inglês)": "Distance_km", "Descrição": "Distância Loja–Cliente (calculada via GPS corrigido)"},
            {"Variável PT-BR": "tempo_entrega_min", "Original (Inglês)": "Delivery_Time", "Descrição": "Tempo total da entrega (em minutos)"},
            {"Variável PT-BR": "tempo_entrega_horas", "Original (Inglês)": "Delivery_Time_Hours", "Descrição": "Tempo de entrega convertido para horas"},
            {"Variável PT-BR": "tempo_entrega_dias", "Original (Inglês)": "Delivery_Time_Days", "Descrição": "Tempo de entrega convertido para dias"},
        ])
        st.dataframe(df_dic, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown(f"#### Tabela de Parâmetros por Produto ({'PT-BR' if usar_pt else 'Inglês Original'})")
        st.dataframe(df_parametros, use_container_width=True, hide_index=True)

    st.markdown(f"#### Amostra da Base Limpa ({'PT-BR' if usar_pt else 'Inglês Original'} — 43.739 linhas)")
    st.dataframe(df_pedidos.head(25), use_container_width=True, hide_index=True)

with aba2:
    st.subheader("Parte 2 (Modelagem Matemática): Equações de Regressão Linear e Diagramas de Dispersão")
    st.info(
        "💡 **O que é a Regressão Linear?** É a equação de uma reta ($y = a \\cdot x + b$) que passa pelo meio dos pontos "
        "do **Diagrama de Dispersão**, permitindo entender a tendência da demanda e prever o comportamento futuro."
    )

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("#### 1. Regressão Linear da Variação da Demanda Diária")
        st.latex(rf"y = {coef_a_dem:.3f} \cdot x + {coef_b_dem:.2f}")
        st.markdown(
            f"- **$y$**: Demanda prevista no dia (unidades)\n"
            f"- **$x$**: Número do dia ($1$ a $44$)\n"
            f"- **Inclinação ($a = {coef_a_dem:+.3f}$)**: A demanda varia em média `{coef_a_dem:+.2f}` pedidos a cada dia que passa.\n"
            f"- **Valor inicial ($b = {coef_b_dem:.2f}$)**: Patamar base de pedidos no início do período."
        )

        fig_disp_dem = go.Figure()
        fig_disp_dem.add_trace(go.Scatter(
            x=df_diario_prod["dia_num"],
            y=df_diario_prod[COL_ESTOQUE_DEMANDA],
            mode="markers",
            name="Demanda Real do Dia (Dispersão)",
            marker=dict(size=9, opacity=0.8)
        ))
        fig_disp_dem.add_trace(go.Scatter(
            x=df_diario_prod["dia_num"],
            y=df_diario_prod["demanda_tendencia"],
            mode="lines",
            name=f"Reta de Regressão (y = {coef_a_dem:+.2f}x + {coef_b_dem:.1f})",
            line=dict(color="red", width=3)
        ))
        fig_disp_dem.update_layout(
            title=f"Diagrama de Dispersão: Demanda Diária × Tempo ({produto_sel})",
            xaxis_title="Dia de Operação (x = 1 a 44)",
            yaxis_title="Quantidade de Pedidos no Dia (y)"
        )
        st.plotly_chart(fig_disp_dem, use_container_width=True)

    with col_r2:
        st.markdown("#### 2. Regressão Linear: Tempo de Entrega × Distância (km)")
        st.latex(rf"Tempo = {coef_a_dist:.2f} \cdot Dist\hat{{a}}ncia + {coef_b_dist:.1f}")
        st.markdown(
            f"- **Interpretação prática**: No cenário selecionado, cada **1 km a mais de distância** adiciona em média "
            f"**`{coef_a_dist:.2f}` minutos** ao tempo de entrega, partindo de um tempo base fixo de **`{coef_b_dist:.1f}` minutos**."
        )

        df_amostra_disp = df_cenario.sample(min(600, len(df_cenario)), random_state=42)
        x_line = np.linspace(df_cenario[COL_DISTANCIA].min(), df_cenario[COL_DISTANCIA].max(), 50)
        y_line = coef_a_dist * x_line + coef_b_dist

        fig_disp_dist = go.Figure()
        fig_disp_dist.add_trace(go.Scatter(
            x=df_amostra_disp[COL_DISTANCIA],
            y=df_amostra_disp[COL_TEMPO_MIN],
            mode="markers",
            name="Entregas Individuais (Dispersão)",
            marker=dict(size=6, opacity=0.5)
        ))
        fig_disp_dist.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            name=f"Regressão (y = {coef_a_dist:.2f}x + {coef_b_dist:.1f})",
            line=dict(color="orange", width=3)
        ))
        fig_disp_dist.update_layout(
            title=f"Diagrama de Dispersão: Tempo de Entrega × Distância ({produto_sel})",
            xaxis_title="Distância Loja–Cliente em km (x)",
            yaxis_title="Tempo de Entrega em Minutos (y)"
        )
        st.plotly_chart(fig_disp_dist, use_container_width=True)

with aba3:
    st.subheader("Análise de Sensibilidade (Clima e Trânsito) e Otimização de Veículos")
    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        df_por_transito = (
            df_prod.groupby(COL_TRANSITO)[COL_TEMPO_MIN]
            .mean()
            .reset_index()
            .sort_values(COL_TEMPO_MIN)
        )
        fig_tr = px.bar(
            df_por_transito, x=COL_TRANSITO, y=COL_TEMPO_MIN, text_auto=".0f",
            color=COL_TEMPO_MIN, color_continuous_scale="Reds",
            title="Sensibilidade ao Trânsito (Minutos)"
        )
        st.plotly_chart(fig_tr, use_container_width=True)

    with col_g2:
        df_por_clima = (
            df_prod.groupby(COL_CLIMA)[COL_TEMPO_MIN]
            .mean()
            .reset_index()
            .sort_values(COL_TEMPO_MIN)
        )
        fig_cl = px.bar(
            df_por_clima, x=COL_CLIMA, y=COL_TEMPO_MIN, text_auto=".0f",
            color=COL_TEMPO_MIN, color_continuous_scale="Blues",
            title="Sensibilidade ao Clima (Minutos)"
        )
        st.plotly_chart(fig_cl, use_container_width=True)

    with col_g3:
        fig_veic = px.bar(
            ranking_veiculos, x=COL_VEICULO, y="tempo_medio_min", text_auto=".1f",
            color=COL_VEICULO,
            title="Otimização: Tempo por Veículo (Min)"
        )
        st.plotly_chart(fig_veic, use_container_width=True)

    st.success(
        f"✅ **Decisão Prescritiva para `{produto_sel}` neste cenário:** Priorizar o veículo **{str(melhor_veiculo).upper()}** "
        f"(média de **{melhor_tempo:.1f} min**) e acionar reposição sempre que o estoque atingir **{ponto_de_pedido} unidades**."
    )

with aba4:
    st.subheader("Visualização do Comportamento do Estoque ao Longo do Tempo (44 Dias)")
    col_e1, col_e2 = st.columns(2)

    with col_e1:
        fig_est_disp = px.scatter(
            df_sim_real, x="dia_numero", y="estoque_fim_do_Dia" if "estoque_fim_do_Dia" in df_sim_real else "estoque_fim_do_dia",
            color="acionou_reposicao",
            size="demanda_real_dia",
            title=f"Diagrama de Dispersão do Estoque ao Longo do Tempo ({produto_sel})",
            labels={
                "dia_numero": "Dia de Operação (1 a 44)",
                "estoque_fim_do_dia": "Nível de Estoque (Unidades)",
                "acionou_reposicao": "Reposição?"
            }
        )
        fig_est_disp.add_hline(
            y=ponto_de_pedido, line_dash="dash", line_color="orange",
            annotation_text=f"Ponto de Reposição ({ponto_de_pedido} un)"
        )
        st.plotly_chart(fig_est_disp, use_container_width=True)

    with col_e2:
        fig_est_linha = px.line(
            df_sim_real, x="data", y=["estoque_fim_do_dia", "demanda_real_dia", "demanda_regressao_linear"],
            markers=True,
            title=f"Trajetória Contínua do Estoque vs Demanda ({produto_sel})",
            labels={"value": "Unidades", "variable": "Indicador"}
        )
        fig_est_linha.add_hline(
            y=ponto_de_pedido, line_dash="dash", line_color="orange",
            annotation_text=f"Ponto de Reposição ({ponto_de_pedido} un)"
        )
        st.plotly_chart(fig_est_linha, use_container_width=True)

    st.dataframe(df_sim_real, use_container_width=True, hide_index=True)
