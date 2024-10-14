from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup
import conexao_postgre

opcoes = webdriver.FirefoxOptions()
opcoes.add_argument("--width=1350")
opcoes.add_argument("--height=930")

driver = webdriver.Firefox(options=opcoes)
driver.get("https://alepa.pa.gov.br/Transparencia/VerbaDeGabinete")
sleep(2)

#a variavel conexao recebe a conexao com o bd postgresql
conexao = conexao_postgre.conexao

''' 
A funcao switch_to é responsável por acessar o conteúdo que está dentro da tag <iframe> 
sem essa função não é possível acessar os dados contidos na página pois eles estão sob a tag <iframe> 
foi passado o valor 0 para a função frame devido ao iframe onde estão os dados ser o primeiro e o único da página'''
driver.switch_to.frame(0)

#funcao responsavel por inserir registros na tabela deputados
def inserir_deputado(nome, valor_verba, ano, mes):
    meses = {"Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04", "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08", "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"}
    mes = str(meses[mes])
    # despesa_id = int(despesa_id)
    nome = str(nome)
    valor_verba = float(valor_verba)
    ano = str(ano)
    data_referencia = ano + "-" + mes + "-" + "01"
    data_referencia = datetime.strptime(data_referencia, "%Y-%m-%d")
    sql = """
        INSERT INTO verba_gabinete(nome_deputado, valor_verba, mes_referencia) VALUES (%s, %s, %s)
"""
    cursor = conexao.cursor()
    cursor.execute(sql, (nome, valor_verba, data_referencia))
    conexao.commit()

#essa funcao formata o valor da verba, para que o valor possa ser inserido no banco de dados
def converter_valor_verba(verbas):
    verba = str(verbas)   
    verba = verba.replace("R$", "")
    verba = verba.replace(".", "")
    verba = verba.replace(",", ".")
    verba = float(verba)  
    return verba

#essa funcao retira os acentos e o prefixo "Dep." do nome dos deputados
def formatar_nome_deputado(nome):
    acentos = {"Â": "A", "Ã": "A", "Á": "A", "É": "E", "Ê": "E", "Í": "I", "Ó": "O", "Ô": "O", "Ú": "U"}
    nome_deputado = str(nome)
    nome_deputado = nome_deputado.replace("Dep. ", "")
    primeira_letra = nome_deputado[0]
    if(primeira_letra in acentos):
        nome_deputado = list(nome_deputado)
        # index_letra_acento = nome_deputado.index(letra)
        nome_deputado[0] = acentos[primeira_letra]
        nome_deputado = "".join(nome_deputado)
    return nome_deputado

for i in range(4):
    ano = driver.find_elements(By.CSS_SELECTOR, "select#anoref > option")[i]
    valor_ano = ano.text
    ano.click()
    for j in range(1, 13):
        botao_mes = driver.find_element(By.CSS_SELECTOR,"button.btn.btn-default")
        mes = driver.find_elements(By.CSS_SELECTOR, "select[name = mes] > option")[j]
        valor_mes = mes.text
        mes.click()
        botao_mes.click()
        sleep(1)
        pagina_site = BeautifulSoup(driver.page_source, "html.parser")
        tabela_deputados = pagina_site.find("table", attrs={"class": "table table-hover"})
        verbas_gabinete = tabela_deputados.find_all("span", attrs={"class": "label label-success"})
        nomes_deputados = tabela_deputados.find_all("a")
        #essa list comprehension retorna apenas os elementos que tem index par, ou seja, retira do nomes_deputados todos os links que não sejam nomes de deputados
        nomes_deputados = [nomes_deputados[index] for index in range(0, len(nomes_deputados)) if index % 2 == 0]
        if(verbas_gabinete):
            for k in range(0, len(verbas_gabinete)):
                nome = nomes_deputados[k].text
                verba = verbas_gabinete[k].text
                verba = converter_valor_verba(verba)
                nome = formatar_nome_deputado(nome)
                inserir_deputado(nome, verba, valor_ano, valor_mes)

driver.close()