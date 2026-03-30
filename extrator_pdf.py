#python extrator_pdf.py <-- RODAR O CÓDIGO

import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def gerar_certidao(contador):
    print(f"--- Iniciando extração do documento #{contador} ---")
    
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        contexto = navegador.new_context(
            http_credentials={'username': 'SEU_USUARIO', 'password': 'SUA_SENHA'}
        )
        pagina = contexto.new_page()

        print("Acessando o sistema...")
        pagina.goto("http://appweb2.agehab.com.br/Logado/Default.aspx")
        pagina.wait_for_load_state('networkidle')

        print("Acessando o Palladio Gerencial...")
        pagina.locator("text='palladiogerencial'").click() 
        pagina.wait_for_load_state('networkidle')

        print("Abrindo a certidão...")
        pagina.locator("text='Certidões'").click() 
        pagina.wait_for_load_state('networkidle')
        
        # ==========================================
        # PASSO 1: EXTRAIR OS DADOS DO HTML DA TELA
        # ==========================================
        print("Lendo os dados da tela...")
        html_da_pagina = pagina.content()
        sopa = BeautifulSoup(html_da_pagina, 'html.parser')
        html_maiusculo = html_da_pagina.upper()
        
        # 1.1 Descobrir o Status 
        status = "Indefinido"
        if "CERTIDÃO POSITIVA DE DÉBITOS COM EFEITO NEGATIVO" in html_maiusculo:
            status = "Positiva com Efeito Negativo"
        elif "CERTIDÃO POSITIVA DE DÉBITOS" in html_maiusculo:
            status = "Positiva"
        elif "CERTIDÃO NEGATIVA DE DÉBITOS" in html_maiusculo:
            status = "Negativa"

        # 1.2 Descobrir a Data de Atualização e encurtar o ano
        tag_data = sopa.find('span', id='lblAtualizadaEm')
        data_atualizacao = "00.00.00"
        
        if tag_data:
            texto_data = tag_data.text.strip() # Exemplo do site: "18/12/2025"
            partes = texto_data.split('/') # Divide em ['18', '12', '2025']
            
            if len(partes) == 3:
                dia = partes[0]
                mes = partes[1]
                ano = partes[2]
                # Remonta a data usando apenas os 2 últimos dígitos do ano (ano[-2:])
                data_atualizacao = f"{dia}.{mes}.{ano[-2:]}"
            else:
                # Prevenção de erro caso a data venha num formato inesperado
                data_atualizacao = texto_data.replace("/", ".")

        # 1.3 Contar os Processos (Apenas se for Positiva ou Efeito de Negativo)
        quantidade_processos = 0
        if status in ["Positiva", "Positiva com Efeito Negativo"]:
            tabela = sopa.find('table', id='gvPendencias')
            if tabela:
                linhas = tabela.find_all('tr')
                quantidade_processos = len(linhas) - 1

        # ==========================================
        # PASSO 2: CRIAR O NOME DO ARQUIVO
        # ==========================================
        origem = "CND AGEHAB"
        texto_processos = f" - {quantidade_processos} processos" if quantidade_processos > 0 else ""
        
        nome_final = f"{contador} - {origem} - {status}{texto_processos} - {data_atualizacao}.pdf"
        caminho_salvar = f"./{nome_final}"

        # ==========================================
        # PASSO 3: MANDAR O PLAYWRIGHT GERAR O PDF
        # ==========================================
        print(f"Gerando PDF: {nome_final}...")
        try:
            pagina.pdf(path=caminho_salvar, format="A4", print_background=True)
            print("Sucesso! Certidão salva com o nome correto.")
        except Exception as e:
            print(f"Erro ao salvar o PDF: {e}")

        navegador.close()

if __name__ == "__main__":
    gerar_certidao(contador=7)