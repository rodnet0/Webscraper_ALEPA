from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import conexao_postgre
from time import sleep

#a variavel conexao recebe a conexao com o bd postgresql
conexao = conexao_postgre.conexao

opcoes = webdriver.FirefoxOptions()
opcoes.add_argument("--width=1350")
opcoes.add_argument("--height=930")

driver = webdriver.Firefox(options=opcoes)
driver.get("https://alepa.pa.gov.br/Transparencia/Page/DiariasdosParlamentares")
sleep(3)

#essa funcao formata o valor da diaria, para que o valor possa ser inserido no banco de dados
def converter_valor_diaria(valor_diaria):
    valor_diaria = str(valor_diaria)   
    valor_diaria = valor_diaria.replace("R$ ", "")
    valor_diaria = valor_diaria.replace(".", "")
    valor_diaria = valor_diaria.replace(",", ".")
    valor_diaria = float(valor_diaria)  
    return valor_diaria

def converter_data(data):
    data = str(data)
    #converte a data de dia/mês/ano para ano-mês-dia
    nova_data = datetime.strptime(data, "%d/%m/%Y").date()
    return nova_data

#essa funcao retira os acentos do nome dos deputados
def formatar_nome_deputado(nome):
    acentos = {"Â": "A", "Ã": "A", "Á": "A", "É": "E", "Ê": "E", "Í": "I", "Ó": "O", "Ô": "O", "Ú": "U"}
    nome_deputado = str(nome)
    primeira_letra = nome_deputado[0]
    if(primeira_letra in acentos):
        nome_deputado = list(nome_deputado)
        nome_deputado[0] = acentos[primeira_letra]
        nome_deputado = "".join(nome_deputado)
    return nome_deputado

def inserir_diaria(celulas_tabela):
    lista_celulas = []
    celulas_tabela = list(celulas_tabela)
    for celula in celulas_tabela:
        lista_celulas.append(celula.text)
    #o valor -1 se refere ao fato que o valor da verba é o último elemento da lista
    lista_celulas[-1] = converter_valor_diaria(lista_celulas[-1])
    #o valor 0 se refere ao fato que a data da diaria é o primeiro elemento da lista
    lista_celulas[0] = converter_data(lista_celulas[0])
    #o valor 1 se refere ao fato que o nome do deputado é sempre o segundo elemento da lista
    lista_celulas[1] = formatar_nome_deputado(lista_celulas[1])
    lista_celulas = tuple(lista_celulas)
    sql = """
        INSERT INTO diarias (mes_referencia, nome_deputado, classificacao_diaria, descricao_diaria, valor_diaria) VALUES (%s, %s, %s, %s, %s)
"""
    cursor = conexao.cursor()
    cursor.execute(sql, lista_celulas)
    conexao.commit()

for i in range(3):
    numero_linhas = int(driver.find_element(By.CSS_SELECTOR, "div[role = grid]").get_attribute("aria-rowcount"))
    driver.execute_script("window.scrollTo(0,500);")
    for j in range(1, numero_linhas + 1):
        #o celulas_tabela vai receber a linha inteira cujo o numero da linha seja igual j
        celulas_tabela = driver.find_elements(By.XPATH, f"//tr[@aria-rowindex='{j}']/td")
        inserir_diaria(celulas_tabela)
        for celula in celulas_tabela:
            #o atributo location_once_scrolled_into_view é o responsável por scrollar a tabela
            celula.location_once_scrolled_into_view
        
    #a função refresh vai recarregar a página para a tabela poder iniciar a partir da primeira linha
    driver.refresh()
    sleep(3)
    input_ano = driver.find_elements(By.CSS_SELECTOR, "div.dx-texteditor-input-container")[0]
    input_ano.click()
    #procurar uma forma de tirar esse if do código
    if i == 2:
        ano = driver.find_elements(By.XPATH, "//div[@aria-selected='false']")[0]
    else:
        ano = driver.find_elements(By.XPATH, "//div[@aria-selected='false']")[i]
    ano.click()
    sleep(2)

driver.close()