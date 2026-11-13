import pandas as pd
import numpy as np

# 1. Carregar o dataset bruto do Kaggle (43.739 linhas)
df = pd.read_csv('amazon_delivery.csv')

# 2. Limpeza de textos (remove espaços extras no fim das palavras, como 'Sunny ', 'Jam ', 'NaN ')
colunas_texto = ['Order_ID', 'Order_Date', 'Order_Time', 'Pickup_Time', 'Weather', 'Traffic', 'Vehicle', 'Area', 'Category']
for col in colunas_texto:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# Corrigir erro de digitação original do dataset ('Metropolitian' -> 'Metropolitan')
df['Area'] = df['Area'].replace({'Metropolitian': 'Metropolitan'})

# Converter textos 'nan' ou 'NaN' em valores nulos reais do Pandas
df = df.replace({'nan': pd.NA, 'NaN': pd.NA, '': pd.NA})

# 3. Preencher valores faltantes SEM perder nenhuma linha (mantém 100% dos 43.739 pedidos)
df['Weather'] = df['Weather'].fillna('Não Informado')
df['Traffic'] = df['Traffic'].fillna('Não Informado')
df['Order_Time'] = df['Order_Time'].fillna(df['Pickup_Time'])
df['Agent_Rating'] = df['Agent_Rating'].fillna(df['Agent_Rating'].median())

# 4. Converter data e tempo de entrega
df['Order_Date'] = pd.to_datetime(df['Order_Date'])
df['Delivery_Time'] = pd.to_numeric(df['Delivery_Time'], errors='coerce')

# Criar tempo de entrega em horas e em dias
df['tempo_entrega_horas'] = (df['Delivery_Time'] / 60).round(2)
df['tempo_entrega_dias'] = (df['Delivery_Time'] / 1440).round(4)

# 5. Corrigir sinal negativo das coordenadas GPS e calcular distância em km (Haversine)
df['Store_Latitude'] = df['Store_Latitude'].abs()
df['Store_Longitude'] = df['Store_Longitude'].abs()
df['Drop_Latitude'] = df['Drop_Latitude'].abs()
df['Drop_Longitude'] = df['Drop_Longitude'].abs()

def calcular_distancia_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return (r * c).round(2)

df['distancia_km'] = calcular_distancia_km(
    df['Store_Latitude'], df['Store_Longitude'],
    df['Drop_Latitude'], df['Drop_Longitude']
)

# 6. Traduzir nomes de produtos, clima, trânsito, veículo e região para Português (PT-BR)
TRADUCAO_PRODUTOS = {
    'Electronics': 'Eletrônicos',
    'Books': 'Livros',
    'Jewelry': 'Joias',
    'Toys': 'Brinquedos',
    'Skincare': 'Cuidados com a Pele',
    'Snacks': 'Lanches',
    'Outdoors': 'Ar Livre e Camping',
    'Apparel': 'Vestuário',
    'Sports': 'Esportes',
    'Grocery': 'Mercado (Perecíveis)',
    'Pet Supplies': 'Pet Shop',
    'Home': 'Casa e Decoração',
    'Cosmetics': 'Cosméticos',
    'Kitchen': 'Cozinha',
    'Clothing': 'Roupas',
    'Shoes': 'Calçados'
}

TRADUCAO_CLIMA = {
    'Sunny': 'Ensolarado',
    'Stormy': 'Tempestade',
    'Cloudy': 'Nublado',
    'Fog': 'Neblina',
    'Windy': 'Ventania',
    'Sandstorms': 'Tempestade de Areia',
    'Não Informado': 'Não Informado'
}

TRADUCAO_TRANSITO = {
    'Low': 'Livre',
    'Medium': 'Médio',
    'High': 'Alto',
    'Jam': 'Engarrafamento',
    'Não Informado': 'Não Informado'
}

TRADUCAO_VEICULO = {
    'motorcycle': 'Moto',
    'scooter': 'Scooter',
    'van': 'Van',
    'bicycle': 'Bicicleta'
}

TRADUCAO_REGIAO = {
    'Urban': 'Urbana',
    'Metropolitan': 'Metropolitana',
    'Semi-Urban': 'Semiurbana',
    'Other': 'Outra'
}

df['Category'] = df['Category'].replace(TRADUCAO_PRODUTOS)
df['Weather'] = df['Weather'].replace(TRADUCAO_CLIMA)
df['Traffic'] = df['Traffic'].replace(TRADUCAO_TRANSITO)
df['Vehicle'] = df['Vehicle'].replace(TRADUCAO_VEICULO)
df['Area'] = df['Area'].replace(TRADUCAO_REGIAO)

df = df.rename(columns={
    'Order_ID': 'id_pedido',
    'Order_Date': 'data_pedido',
    'Order_Time': 'hora_pedido',
    'Pickup_Time': 'hora_coleta',
    'Category': 'produto',
    'Area': 'regiao',
    'Weather': 'clima',
    'Traffic': 'transito',
    'Vehicle': 'veiculo',
    'Agent_Age': 'idade_entregador',
    'Agent_Rating': 'nota_entregador',
    'Delivery_Time': 'tempo_entrega_min'
})

# 7. EXPORTAÇÃO 1: Dataset Limpo Completo (43.739 entregas)
colunas_finais = [
    'id_pedido', 'data_pedido', 'hora_pedido', 'hora_coleta',
    'produto', 'regiao', 'clima', 'transito', 'veiculo',
    'idade_entregador', 'nota_entregador', 'distancia_km',
    'tempo_entrega_min', 'tempo_entrega_horas', 'tempo_entrega_dias'
]
df_limpo = df[colunas_finais].copy()
df_limpo.to_csv('amazon_pedidos_limpo.csv', index=False)

# 8. EXPORTAÇÃO 2: Tabela Agregada por Dia e Produto (704 linhas)
df_estoque = df_limpo.groupby(['data_pedido', 'produto']).agg(
    demanda_diaria=('id_pedido', 'count'),
    tempo_medio_horas=('tempo_entrega_horas', 'mean'),
    tempo_desvio_horas=('tempo_entrega_horas', 'std'),
    distancia_media_km=('distancia_km', 'mean')
).reset_index()
df_estoque['tempo_desvio_horas'] = df_estoque['tempo_desvio_horas'].fillna(0).round(2)
df_estoque['tempo_medio_horas'] = df_estoque['tempo_medio_horas'].round(2)
df_estoque['distancia_media_km'] = df_estoque['distancia_media_km'].round(2)
df_estoque.to_csv('amazon_estoque_diario.csv', index=False)

# 9. EXPORTAÇÃO 3: Tabela Consolidada de Parâmetros dos 16 Produtos
df_parametros = df_estoque.groupby('produto').agg(
    dias_analisados=('data_pedido', 'count'),
    total_pedidos=('demanda_diaria', 'sum'),
    demanda_media_diaria=('demanda_diaria', 'mean'),
    demanda_desvio_diario=('demanda_diaria', 'std'),
    tempo_medio_horas=('tempo_medio_horas', 'mean'),
    tempo_desvio_horas=('tempo_desvio_horas', 'mean'),
    distancia_media_km=('distancia_media_km', 'mean')
).reset_index().round(2)
df_parametros.to_csv('amazon_parametros_produtos.csv', index=False)

print("Tratamento concluído com sucesso!")
print(f"Total de entregas válidas: {len(df_limpo)} (0 linhas perdidas)")
