import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. ACESSAR A WEB
print("Acessando o site...")
url = 'https://quotes.toscrape.com/'
resposta = requests.get(url)

# Verifica se o site carregou corretamente (Código 200 é sucesso)
if resposta.status_code == 200:
    # 2. EXTRAIR OS DADOS
    print("Extraindo os dados...")
    sopa = BeautifulSoup(resposta.text, 'html.parser')
    
    dados_extraidos = []
    
    # Encontra todas as caixas de citação no HTML do site
    caixas_de_citacao = sopa.find_all('div', class_='quote')
    
    for caixa in caixas_de_citacao:
        # Pega o texto e o autor
        texto = caixa.find('span', class_='text').text
        autor = caixa.find('small', class_='author').text
        
        # Adiciona na nossa lista como um dicionário
        dados_extraidos.append({
            'Citação': texto,
            'Autor': autor
        })

    # 3. TRANSFORMAR EM TABELA E SALVAR NO EXCEL
    print("Gerando a planilha...")
    # Converte a lista para um DataFrame do Pandas (formato de tabela)
    tabela = pd.DataFrame(dados_extraidos)
    
    # Salva no formato Excel
    nome_do_arquivo = 'citacoes_da_web.xlsx'
    tabela.to_excel(nome_do_arquivo, index=False, engine='openpyxl')
    
    print(f"Sucesso! Os dados foram salvos na planilha: {nome_do_arquivo}")

else:
    print(f"Erro ao acessar o site. Código: {resposta.status_code}")