import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página (deve ser sempre a primeira instrução do Streamlit)
st.set_page_config(page_title="Painel de Chamadas - Alemão Autopeças", layout="wide")

# Exibindo a logo da Alemão Autopeças no topo da barra lateral
st.sidebar.image("Calendário Alemão 2025.png (3).png", use_container_width=True)
st.sidebar.divider()

st.title(":material/phone: Painel de Análise de Chamadas da Alemão Autopeças")

# Permitindo múltiplos arquivos no uploader
arquivos_enviados = st.file_uploader(
    "Envie o(s) seu(s) relatório(s) de chamadas (.xls ou .xlsx)", 
    type=["xls", "xlsx"], 
    accept_multiple_files=True
)

if arquivos_enviados:
    # Lista para guardar os dataframes caso sejam vários arquivos
    lista_dfs = []
    
    for arquivo in arquivos_enviados:
        try:
            # Lendo cada arquivo HTML/XLS do Sonax
            tabelas = pd.read_html(arquivo)
            df_temp = tabelas[0]
            lista_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo {arquivo.name}: {e}")
    
    # Se conseguirmos ler os arquivos, juntamos todos em um único DataFrame
    if lista_dfs:
        df = pd.concat(lista_dfs, ignore_index=True)
        
        # Limpando possíveis espaços em branco invisíveis na coluna Status
        df['Status'] = df['Status'].astype(str).str.strip()
        
        # 1. Convertendo a coluna 'Data/hora' para o formato de data real (necessario pro pandas)
        df['Data/hora'] = pd.to_datetime(df['Data/hora'], errors='coerce')
        
        # 2. Criando um dicionário para traduzir o número do mês para o nome em português
        meses_pt = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro',
            10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        # Aplicando o mapeamento na coluna do mês
        df['Nome_Mes'] = df['Data/hora'].dt.month.map(meses_pt)
        df['Num_Mes'] = df['Data/hora'].dt.month

        # 2. CRIANDO A BARRA LATERAL DE FILTROS 🔍
        st.sidebar.header("🔍 Filtros do Painel")
        
        # Filtro por Mês
        meses_disponiveis = df['Nome_Mes'].dropna().unique()
        meses_selecionados = st.sidebar.multiselect(
            "Filtrar por Mês:", 
            options=meses_disponiveis, 
            default=meses_disponiveis
        )
        
        # Filtro por Vendedor (ignorando valores nulos para não sumir com a URA)
        agentes_disponiveis = df['Agente'].dropna().unique()
        agentes_selecionados = st.sidebar.multiselect(
            "Filtrar por Vendedor:", 
            options=agentes_disponiveis, 
            default=agentes_disponiveis
        )
        
        # Aplicando os filtros mantendo as chamadas de URA (onde o agente é vazio/NaN) ou filtrando corretamente
        if meses_selecionados:
            df = df[df['Nome_Mes'].isin(meses_selecionados)]
            
        if agentes_selecionados:
            # Mantém as linhas do vendedor selecionado OU linhas onde o status é 'Atendimento URA'
            df = df[df['Agente'].isin(agentes_selecionados) | (df['Status'] == 'Atendimento URA')]
        
        st.success(f"Painel carregado! Total de registros filtrados: {len(df)}")

        # CÁLCULO DOS KPIS (Necessários para a tela)
        total_chamadas = len(df)
        chamadas_atendidas = (df['Status'] == 'Atendida').sum()
        chamadas_perdidas = (df['Status'] == 'Não Atendida').sum()
        
        # Contando chamadas que terminaram no atendimento URA
        chamadas_ura = (df['Status'] == 'Atendimento URA').sum()
    
        # 3. INDICADORES PRINCIPAIS (KPIs) COM A URA INCLUÍDA 
        st.divider()
        st.subheader(":material/push_pin: Indicadores Principais")

        # Criando colunas lado a lado para os cartões
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="Total de Chamadas", value=total_chamadas)

        with col2:
            pct_atendidas = (chamadas_atendidas / total_chamadas * 100) if total_chamadas > 0 else 0
            st.metric(label="Atendidas", value=chamadas_atendidas, delta=f"{pct_atendidas:.1f}%")

        with col3:
            pct_perdidas = (chamadas_perdidas / total_chamadas * 100) if total_chamadas > 0 else 0
            st.metric(label="Perdidas", value=chamadas_perdidas, delta=f"-{pct_perdidas:.1f}%", delta_color="inverse")

        with col4:
            pct_ura = (chamadas_ura / total_chamadas * 100) if total_chamadas > 0 else 0
            st.metric(label="Atendimento URA", value=chamadas_ura, delta=f"{pct_ura:.1f}%")

        st.divider()

        # Extração e análise das métricas

        # se eu quisesse puxar um status específico 
        #total_atendidas = (df['Status'] == 'Atendida').sum()
        #st.write(f"Total de chamadas atendidas: {total_atendidas}") 

        #total_perdidas = (df['Status']== 'Não Atendida').sum()
        #st.write(f"total de chamadas perdidas: {total_perdidas}")

        # Criação de abas para visualização organizada
        aba1, aba2, aba3 = st.tabs(["📊 Visão Geral", "👥 Desempenho da Equipe", "📈 Evolução Temporal"])

        with aba1:
            st.subheader(":material/bar_chart: Proporção de Status das Chamadas")
            
            # Contagem de status limpa com a coluna 'Quantidade'
            df_status = df['Status'].value_counts().reset_index(name='Quantidade')
            df_status.columns = ['Status', 'Quantidade']

            st.write("Contagem geral de status:")
            st.dataframe(df_status, hide_index=True)

            # 2. Criando o gráfico de rosca com Plotly
            fig_status = px.pie(
                df_status, 
                names='Status', 
                values='Quantidade', 
                hole=0.4, # Deixa o gráfico com formato de rosca
                title="Distribuição Percentual dos Status de Chamada"
            )
            
            # 3. Exibindo no Streamlit
            st.plotly_chart(fig_status, use_container_width=True)

        with aba2:
            st.subheader("Análise de chamadas atendidas por vendedor:")
            
            # Vendas por agente convertidas em DataFrame limpo
            vendas_por_agente = df[df['Status'] == 'Atendida']['Agente'].value_counts().reset_index(name='Quantidade')
            vendas_por_agente.columns = ['Agente', 'Quantidade']
            
            st.dataframe(vendas_por_agente, hide_index=True)
            st.bar_chart(vendas_por_agente.set_index('Agente'))  # grafico com uma funçao propria do streamlit

            st.subheader("👥 Desempenho Detalhado por Agente")
            
            # 1. Criando uma tabela cruzada entre Agente e Status
            df_agente_detalhe = pd.crosstab(df['Agente'], df['Status'], margins=True, margins_name="Total")
            df_agente_detalhe = df_agente_detalhe.rename_axis("Status", axis=1)
            
            # Exibindo a tabela gerencial no Streamlit
            st.dataframe(df_agente_detalhe, use_container_width=True)
            
            # 2. Criando um gráfico de barras empilhadas para comparar os agentes visualmente
            # (Removemos a linha 'Total' para o gráfico não distorcer)
            df_grafico_agente = pd.crosstab(df['Agente'], df['Status']).reset_index()
            
            fig_agente_detalhe = px.bar(
                df_grafico_agente,
                x='Agente',
                y=df_grafico_agente.columns[1:], # Pega todas as colunas de status dinamicamente
                title="Volume de Atendimentos por Status e por Vendedor",
                labels={'value': 'Quantidade de Chamadas', 'variable': 'Status'}
            )
            
            st.plotly_chart(fig_agente_detalhe, use_container_width=True)

        with aba3:
            st.subheader("📅 Volume de Chamadas por Mês")
            
            # 3. Contando o volume de chamadas por nome do mês
            chamadas_por_mes = df.groupby(['Num_Mes', 'Nome_Mes']).size().reset_index(name='Total_Chamadas')
            st.dataframe(chamadas_por_mes[['Nome_Mes', 'Total_Chamadas']], hide_index=True)

            st.subheader("📉 Taxa de Perda Mensal (%)")
            
            # 1. Criando uma cópia ou tabela agrupada por mês e status
            df_taxa_perda = df.groupby(['Num_Mes', 'Nome_Mes', 'Status']).size().unstack(fill_value=0)
            
            # Garantindo que as colunas 'Atendida' e 'Não Atendida' existem para evitar erros
            if 'Não Atendida' in df_taxa_perda.columns and 'Atendida' in df_taxa_perda.columns:
                # Calculando o total do mês e a porcentagem de perdidas
                df_taxa_perda['Total'] = df_taxa_perda.sum(axis=1)
                df_taxa_perda['Pct_Perdidas'] = (df_taxa_perda['Não Atendida'] / df_taxa_perda['Total']) * 100
                
                # Limpando e organizando a tabela para o gráfico
                df_taxa_perda = df_taxa_perda.reset_index().sort_values('Num_Mes')
                
                # 2. Criando um gráfico de linha com Plotly
                fig_perda = px.line(
                    df_taxa_perda,
                    x='Nome_Mes',
                    y='Pct_Perdidas',
                    markers=True,
                    title="Evolução da Taxa de Chamadas Perdidas (%) por Mês",
                    labels={'Pct_Perdidas': 'Taxa de Perda (%)', 'Nome_Mes': 'Mês'}
                )
                
                # Ajustando o eixo y para porcentagem visual
                fig_perda.update_traces(line=dict(color='firebrick', width=3))
                
                st.plotly_chart(fig_perda, use_container_width=True)
            else:
                st.info("As colunas de status necessárias não foram encontradas para calcular a taxa de perda.")
