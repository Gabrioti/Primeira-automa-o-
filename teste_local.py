#python teste_local.py
import os
import pdfplumber
import re

# ==========================================
# 1. FUNÇÃO PRINCIPAL DE EXTRAÇÃO E RENOMEAÇÃO
# ==========================================
# ---> MUDANÇA 1: A função agora recebe o 'numero_categoria' também <---
def extrair_dados_pdf(origem, numero_categoria):
    caminho_atual = "./teste.pdf" 
    
    # Verifica se o arquivo teste.pdf está na pasta
    if not os.path.exists(caminho_atual):
        print(f"\nErro: O arquivo '{caminho_atual}' não foi encontrado.")
        print("Arraste um PDF para a mesma pasta do código e renomeie para 'teste.pdf' antes de rodar.")
        return

    print(f"\nLendo o conteúdo do PDF da origem: {origem}...")
    status = "Indefinido"
    data_atualizacao = "00.00.00"
    
    # Abre o PDF usando o pdfplumber
    try:
        with pdfplumber.open(caminho_atual) as pdf:
            primeira_pagina = pdf.pages[0]
            texto_do_pdf = primeira_pagina.extract_text().upper()
            
            print("\n--- TEXTO EXTRAÍDO DO PDF ---")
            print(texto_do_pdf)
            print("-----------------------------\n")
            
            data_encontrada = None

            # ============================================================
            # REGRAS DE LEITURA (Separadas por Origem)
            # ============================================================
            
            # ---> REGRAS DA AGEHAB
            if origem == "AGEHAB":
                if "CERTIDÃO POSITIVA DE DÉBITOS COM EFEITO NEGATIVO" in texto_do_pdf or "CERTIDÃO POSITIVA COM EFEITO DE NEGATIVA" in texto_do_pdf:
                    status = "Positiva com Efeito Negativo"
                elif "CERTIDÃO POSITIVA DE DÉBITOS" in texto_do_pdf:
                    status = "Positiva"
                elif "CERTIDÃO NEGATIVA DE DÉBITOS" in texto_do_pdf:
                    status = "Negativa"

                busca_data = re.search(r'ATUALIZADA EM:\s*(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
                if busca_data:
                    data_encontrada = busca_data.group(1)

            # ---> REGRAS DO FGTS
            elif origem == "FGTS":
                # No FGTS, a certidão limpa diz que a situação é "REGULAR"
                # (Se você preferir que no arquivo saia escrito "Negativa", é só mudar aqui)
                if "SITUAÇÃO REGULAR" in texto_do_pdf:
                    status = "Negativa"
                else:
                    # Se não estiver regular, a Caixa geralmente nem emite o CRF, mas deixamos garantido
                    status = "Irregular"
                
                # Procura o formato: VALIDADE: 00/00/0000 A 00/00/0000 e pega só a última data
                busca_data = re.search(r'VALIDADE:\s*\d{2}[./]\d{2}[./]\d{2,4}\s*A\s*(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
                if busca_data:
                    data_encontrada = busca_data.group(1)


            # ============================================================
            # FORMATAÇÃO DA DATA (Isso serve para TODAS as origens)
            # ============================================================
            
            # Se as regras acima falharem em achar a data exata, ele tenta achar qualquer data solta
            if not data_encontrada:
                busca_data_solta = re.search(r'\d{2}[./]\d{2}[./]\d{2,4}', texto_do_pdf)
                if busca_data_solta:
                    data_encontrada = busca_data_solta.group()

            # Fatiar a data para pegar os 2 últimos dígitos do ano
            if data_encontrada:
                partes = data_encontrada.replace("/", ".").split(".")
                if len(partes) == 3:
                    dia = partes[0]
                    mes = partes[1]
                    ano = partes[2]
                    data_atualizacao = f"{dia}.{mes}.{ano[-2:]}"
                else:
                    data_atualizacao = data_encontrada.replace("/", ".")

    except Exception as e:
        print(f"Erro ao tentar ler o PDF: {e}")
        return

    # ==========================================
    # 2. RENOMEAR O ARQUIVO
    # ==========================================
    # ---> MUDANÇA 2: Usamos o numero_categoria no lugar do contador fixo <---
    nome_final = f"{numero_categoria} - CND {origem} - {status} - {data_atualizacao}.pdf"
    
    print("\n--- RESUMO DA EXTRAÇÃO ---")
    print(f"Origem: {origem}")
    print(f"Status encontrado: {status}")
    print(f"Data encontrada: {data_atualizacao}")
    print(f"Nome do arquivo será: {nome_final}")
    print("--------------------------\n")
    
    # Executa a renomeação do arquivo
    try:
        os.rename(caminho_atual, f"./{nome_final}")
        print(f"Sucesso! O arquivo foi renomeado para '{nome_final}'.")
    except Exception as e:
        print(f"Erro ao tentar renomear o arquivo: {e}")


# ==========================================
# 3. MENU PRINCIPAL (O Controle)
# ==========================================
def iniciar_menu():
    print("Digite qual CND será retirada:")
    escolha = input("1. Federal\n2. Estadual\n3. Municipal\n4. Trabalhista\n5. Comprasnet\n6. FGTS\n7. AGEHAB\n-> ")

    # ---> MUDANÇA 3: Passamos a 'escolha' como o número para a função <---
    match escolha:
        case "1":
            extrair_dados_pdf(origem="Federal", numero_categoria=escolha)
        case "2":
            extrair_dados_pdf(origem="Estadual", numero_categoria=escolha)
        case "3":
            extrair_dados_pdf(origem="Municipal", numero_categoria=escolha)
        case "4":
            extrair_dados_pdf(origem="Trabalhista", numero_categoria=escolha)
        case "5":
            extrair_dados_pdf(origem="Comprasnet", numero_categoria=escolha)
        case "6":
            extrair_dados_pdf(origem="FGTS", numero_categoria=escolha)
        case "7":
            extrair_dados_pdf(origem="AGEHAB", numero_categoria=escolha)
        case _:
            print("Opção inválida! Por favor, rode o script novamente e digite um número de 1 a 7.")

# ==========================================
# 4. GATILHO DE EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    iniciar_menu()