import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide")
conexao = st.connection("neon", type="sql")

@st.cache_data
def converter_df_para_csv(df):
    return df.to_csv(index=False, sep=";").encode("utf-8")

@st.cache_data
def converter_df_para_string(df):
    return df.to_string(index=False)

@st.cache_data
def converter_df_para_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="openpyxl")
    df.to_excel(writer, index=False, sheet_name="Planilha1")
    writer.close()  
    xlsx = output.getvalue()
    return xlsx

df = conexao.query('SELECT nome_deputado, valor_diaria, mes_referencia, classificacao_diaria, descricao_diaria FROM diarias;', ttl="10m")

df.columns = ["Deputado", "Valor", "Data", "Classificacao", "Descricao"]

#a função to_datetime irá converter os dados da coluna data para o tipo datetime assim será possível manipular as datas através de funções
df["Data"] = pd.to_datetime(df["Data"])

st.title("Tabela de Dados")
st.write("### Valor Gasto com Diárias Entre os Anos de 2022 a 2024")
st.sidebar.header("Filtros")
data_inicio = st.sidebar.date_input("Data Inicial", format="DD/MM/YYYY", min_value=df["Data"].min(), max_value=df["Data"].max())
data_fim = st.sidebar.date_input("Data Final", format="DD/MM/YYYY", min_value=df["Data"].min(), max_value=df["Data"].max())
#o multiselect só irá exibir os deputados que estão no período entre data_inicio e data_fim
opcoes = df.query("Data >= @data_inicio and Data <= @data_fim").sort_values("Deputado")
opcoes = opcoes["Deputado"].unique()
deputado = st.sidebar.multiselect("Deputado", options=opcoes, placeholder="Escolha Uma Opção")
classificacao = st.sidebar.multiselect("Classificação", options=df["Classificacao"].unique(), placeholder="Escolha Uma Opção", default=df["Classificacao"].unique())

#menu de opcoes de download
csv = converter_df_para_csv(df)
txt = converter_df_para_string(df)
xlsx = converter_df_para_excel(df)
with st.sidebar.expander("Baixar Dados"):
    st.download_button(
        "Baixar CSV",
        csv,
        "dataframe_alepa.csv",
        "text/csv"
    )
    st.download_button(
        "Baixar TXT",
        txt,
        "dataframe_alepa.txt",
        "text/plain"
    )
    st.download_button(
        "Baixar XLSX",
        xlsx,
        "dataframe_alepa.xlsx",
        "application/octet-stream"
    )

#a função query vai retornar as linhas que cumprem as condições definidas pelos filtros
df = df.query("Deputado == @deputado and Classificacao == @classificacao and (Data >= @data_inicio and Data <= @data_fim)").sort_values(["Deputado", "Data"])
df_exibicao = df.copy()
#formatando a data para exbição no dataframe
df_exibicao["Data"] = df_exibicao["Data"].dt.strftime("%d/%m/%Y")
#formatando o valor para exbição no dataframe
df_exibicao["Valor"] = df_exibicao["Valor"].apply(lambda x: "R$ {:_.2f}".format(x).replace(".", ",").replace("_", "."))
#exibindo o dataframe
st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

#formata a exibição do total
total = "{:_.2f}".format(df['Valor'].sum())
total = total.replace(".", ",").replace("_", ".")
st.write(f"## Total: R${total}")

st.title("Gráficos")
# col1, col2 = st.columns(2)

df_grafico = df.groupby(by=["Deputado"])["Valor"].sum().reset_index()

#criar o grafico de barra
fig_deputados = px.bar(
    df_grafico,
    x="Valor",
    y="Deputado",
    color="Deputado",
    # text_auto=".5s",
    orientation="h",
    title="Valor gasto com diárias por deputado"
    # width=1000
)
fig_deputados.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", 
    # paper_bgcolor="white",
    hoverlabel=dict(
        bgcolor="white",
        font_size=16,
        font_color="black"
    ),
    legend=dict(
        font_size=14,
        title_font_size=16
    ),
    yaxis=dict(
        title="Deputados",
        titlefont_size=18,
        tickfont_size=16,
        showgrid=False
    ),
    xaxis=dict(
        title="Valor total das diárias (R$)",
        titlefont_size=18,
        tickfont_size=16,
        showgrid=False
        # tickangle=-45,
    )
)
fig_deputados.update_traces(
    textposition="outside",
    cliponaxis=False,
    textfont_size=16,
    textangle=0,
    texttemplate="R$ %{x:,.2f}",
    hovertemplate="Deputado: %{y}<br> Total: R$ %{x:,.2f}<extra></extra>"
    # orientation="h"
)
#criar o gráfico de linha
# fig_deputados_linha = px.line(
#     df,
#     x="Data",
#     y="Valor",
#     color="Deputado",
#     # text_auto=".3s",
#     title="Valor de verba de gabinete por deputado"
# )

#plotar os gráficos
# col1.plotly_chart(fig_deputados, use_container_width=True)
# col2.plotly_chart(fig_deputados_linha, use_container_width=True)
fig_deputados

#Documentação
with st.expander("Documentação do Projeto"):
    st.markdown("""
            # Projeto Webscraper ALEPA

            >**Introdução**:

            Esta documentação fornece uma visão geral desse projeto desenvolvido através do framework Streamlit e conectado a um banco de dados PostgreSQL. 
            A aplicação permite que os usuários visualizem de uma forma mais dinâmica os dados de verba de gabinete, verba indenizatória e diárias de viagem dos deputados da Assembléia Legislativa do Estado do Pará (ALEPA).
            A visualização dos gráficos e tabelas muda de acordo com os filtros de pesquisa aplicados pelo usuário, além disso os usuários podem fazer o download dos dados em qualquer um dos respectivos formatos: CSV, TXT, XLSX.

            >**Visão Geral do Projeto**

            *Objetivo Específico*: Através de ferramentas de web scraping, extrair os dados públicos relacionados a despesas do portal da transparência da ALEPA e armazená-los em um banco de dados integrado a ferramenta Streamlit, possibilitando a visualização dos dados através de gráficos e tabelas.
                
            *Objetivo Geral*: O objetivo desse projeto é permitir que o cidadão possa visualizar e analisar as despesas dos parlamentares de maneira mais simples onde seja possível indentificar gastos suspeitos e incentivando a população a questioná-los.

            >**Tecnologias Utilizadas**:

            * Streamlit
            * Python
            * PostgreSQL
            * Plotly
            * Selenium

            >**Funcionamento**:

            1. Entrada de dados: Através da biblioteca selenium, da linguagem de programação Python, os dados são extraídos do Portal da Transparência ALEPA e posteriormente são tratados a fim de armazená-los de forma correta no banco de dados.

            2. Integração com o banco de dados: Após serem extraídos, os dados oriundos de cada página são inseridos em uma tabela correspondente no banco de dados em que fica registrado a data e o horário que esses dados foram extraídos.

            3. Visualização: O framework Streamlit é responsável por fazer a conexão com o banco de dados e construir a página web e seus elementos como tabelas, botões e etc. Enquanto que os gráficos são construídos através da biblioteca Plotly que por meio dos dados filtrados pelo usuário irá gerar o gráfico.

            4. Download: É possível fazer o download dos dados assim como no Portal da Transparência, esse recurso é indicado para os usuários que desejam fazer análises mais aprofundadas dos dados usando outras ferramentas.

            > **Conclusão**:

            O sistema ao extrair os dados do Portal da Transparência ALEPA e armazená-los permite que os dados sejam exibidos de uma forma mais dinâmica, possibilita que os usuários possam fazer análises de maneira mais simples, pois os dados já foram extraídos e combinados, devido a isso o cidadão pode fiscalizar de maneira mais eficiente os gastos relacionados aos parlamentares.

            > **Possíveis Melhorias Futuras**

            * O projeto pode ser melhorado futuramente ao automatizar o script responsável pela extração de dados da página web do Portal da Transparência ALEPA, com o objetivo de que toda vez que um dado for inserido na página web do portal ele também já seja inserido no banco de dados do projeto. 
            * Após o script de extração de dados ser automatizado, poderá ser criado uma tabela de auditoria no banco de dados em que toda vez que é feita uma alteração na página web do Portal da Transparência ALEPA essa alteração seja inserida nessa tabela para posteriormente verificar se houve alguma alteração nos valores dispostos no portal.
            * Extrair mais tipos de despesas contidas no Portal da Transparência
            * Adição de gráficos, tabelas e outros elementos visuais.
             """)
# st.bar_chart(df)