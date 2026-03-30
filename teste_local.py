#python teste_local.py

import os
import pdfplumber
import re

def testar_leitura_pdf():
    # Esse é o arquivo que você arrastou para dentro do Codespace
    caminho_atual = "./teste.pdf" 
    
    # Verifica se você realmente fez o upload do arquivo
    if not os.path.exists(caminho_atual):
        print(f"Erro: O arquivo {caminho_atual} não foi encontrado no Codespace.")
        print("Arraste um PDF para cá e renomeie para 'teste.pdf' antes de rodar.")
        return

    print("Lendo o conteúdo do PDF...")
    status = "Indefinido"
    data_atualizacao = "00.00.00"
    
    # Abre o PDF usando o pdfplumber
    with pdfplumber.open(caminho_atual) as pdf:
        primeira_pagina = pdf.pages[0]
        # Extrai o texto e já deixa tudo em maiúsculo para facilitar a busca
        texto_do_pdf = primeira_pagina.extract_text().upper()
        
        # Imprime o texto lido para você ver como o Python enxerga o PDF
        print("\n--- TEXTO EXTRAÍDO DO PDF ---")
        print(texto_do_pdf)
        print("-----------------------------\n")
        
        # 1. Descobrir o Status
        if "CERTIDÃO POSITIVA DE DÉBITOS COM EFEITO NEGATIVO" in texto_do_pdf:
            status = "Positiva com Efeito Negativo"
        elif "CERTIDÃO POSITIVA DE DÉBITOS" in texto_do_pdf:
            status = "Positiva"
        elif "CERTIDÃO NEGATIVA DE DÉBITOS" in texto_do_pdf:
            status = "Negativa"

        # 2. Descobrir a Data
        # Procura o padrão de data especificamente depois da palavra "ATUALIZADA EM:"
        # O \s* significa "pode ter espaços aqui", e \d é para números.
        busca_data = re.search(r'ATUALIZADA EM:\s*(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
        
        if busca_data:
            # O group(1) pega apenas a parte da data que colocamos entre parênteses na busca
            data_encontrada = busca_data.group(1)
            data_atualizacao = data_encontrada.replace("/", ".")
        else:
            # Se não achar do lado do "Atualizada em:", procura qualquer data solta no padrão 00/00/0000
            busca_data_solta = re.search(r'\d{2}[./]\d{2}[./]\d{2,4}', texto_do_pdf)
            if busca_data_solta:
                data_atualizacao = busca_data_solta.group().replace("/", ".")

    # 3. Simular a renomeação
    contador = 1 # Apenas um número de teste
    origem = "CND AGEHAB"
    
    nome_final = f"{contador} - {origem} - {status} - {data_atualizacao}.pdf"
    
    print(f"Resumo da Extração:")
    print(f"Status encontrado: {status}")
    print(f"Data encontrada: {data_atualizacao}")
    print(f"Nome do arquivo será: {nome_final}")
    
    # Executa a renomeação do arquivo
    try:
        os.rename(caminho_atual, f"./{nome_final}")
        print("\nSucesso! O arquivo 'teste.pdf' foi renomeado no seu Codespace.")
    except Exception as e:
        print(f"\nErro ao tentar renomear o arquivo: {e}")

if __name__ == "__main__":
    testar_leitura_pdf()