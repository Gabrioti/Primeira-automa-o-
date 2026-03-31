#                               python teste_local.py
import os
import pdfplumber
import re
from datetime import datetime, timedelta
import pytesseract
from pdf2image import convert_from_path

# ==========================================
# 0. FUNÇÃO DE OCR (Para PDFs Fantasma)
# ==========================================
def extrair_texto_com_ocr(caminho_pdf):
    print("Iniciando extração via OCR (isso pode levar alguns segundos)...")
    texto_extraido = ""
    try:
        # No Codespaces (Linux), o poppler é encontrado automaticamente
        imagens = convert_from_path(caminho_pdf) 
        
        for imagem in imagens:
            # lang='por' para ler português com acentuação corretamente
            texto = pytesseract.image_to_string(imagem, lang='por')
            texto_extraido += texto + "\n"
            
        return texto_extraido.upper()
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return ""

# ==========================================
# 1. FUNÇÃO PRINCIPAL DE EXTRAÇÃO E RENOMEAÇÃO
# ==========================================
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
            texto_do_pdf = primeira_pagina.extract_text()
            
            # ---> SE FOR PDF FANTASMA OU ORIGEM ESPECÍFICA, USA O OCR <---
            if not texto_do_pdf or texto_do_pdf.strip() == "" or origem in ["Federal", "Trabalhista"]:
                print(f"PDF imagem detectado para a origem {origem}. Acionando OCR...")
                texto_do_pdf = extrair_texto_com_ocr(caminho_atual)
            else:
                texto_do_pdf = texto_do_pdf.upper()

            print("\n--- TEXTO EXTRAÍDO DO PDF ---")
            print(texto_do_pdf)
            print("-----------------------------\n")
            
            data_encontrada = None

            # ============================================================
            # REGRAS DE LEITURA (Separadas por Origem)
            # ============================================================
            
            # ---> REGRAS DA FEDERAL (Genérica inicial)
            if origem == "Federal":
                if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                    status = "Positiva com Efeito Negativo"
                elif "NEGATIVA" in texto_do_pdf or "NÃO CONSTA" in texto_do_pdf:
                    status = "Negativa"
                elif "POSITIVA" in texto_do_pdf or "CONSTA" in texto_do_pdf:
                    status = "Positiva"
                
                # 2. Busca a data de VALIDADE exata
                # O [ÁA] e [ÉE] garantem que ele ache a palavra mesmo se o OCR engolir o acento
                busca_validade = re.search(r'V[ÁA]LIDA AT[ÉE]\s*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                if busca_validade:
                    data_encontrada = busca_validade.group(1)

            # ---> REGRAS DA ESTADUAL (GOIÁS)
            elif origem == "Estadual":
                # 1. Status com "Escudo"
                if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                    status = "Positiva com Efeito Negativo"
                elif "NEGATIVA" in texto_do_pdf or "NAO CONSTA DEBITO" in texto_do_pdf:
                    status = "Negativa"
                elif "POSITIVA" in texto_do_pdf or "CONSTA DEBITO" in texto_do_pdf:
                    status = "Positiva"

                # 2. Dias de validade
                dias_validade = 60 # Padrão de segurança
                busca_dias = re.search(r'VALIDA POR\s+(\d+)\s+DIAS', texto_do_pdf)
                if busca_dias:
                    dias_validade = int(busca_dias.group(1))

                # 3. Data de emissão e matemática
                busca_emissao = re.search(r'(\d{1,2})\s+([A-ZÇ]+)\s+DE\s+(\d{4})', texto_do_pdf)
                if busca_emissao:
                    dia = int(busca_emissao.group(1))
                    mes_texto = busca_emissao.group(2).replace("Ç", "C")
                    ano = int(busca_emissao.group(3))

                    meses = {
                        "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4,
                        "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9,
                        "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12
                    }
                    mes_numero = meses.get(mes_texto)

                    if mes_numero:
                        try:
                            data_emissao_obj = datetime(ano, mes_numero, dia)
                            data_validade_obj = data_emissao_obj + timedelta(days=dias_validade)
                            data_encontrada = data_validade_obj.strftime("%d/%m/%Y")
                        except Exception as e:
                            print(f"Aviso: Erro ao calcular a data Estadual: {e}")

            # ---> REGRAS DA MUNICIPAL (Genérica inicial)
            elif origem == "Municipal":
                if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf or "EFEITO NEGATIVO" in texto_do_pdf:
                    status = "Positiva com Efeito Negativo"
                elif "NEGATIVA" in texto_do_pdf or "NÃO CONSTA" in texto_do_pdf:
                    status = "Negativa"
                elif "POSITIVA" in texto_do_pdf:
                    status = "Positiva"
                
                # 2. Busca a data de VALIDADE exata
                # O [ÁA] e [ÉE] garantem que ele ache a palavra mesmo se o OCR engolir o acento
                busca_validade = re.search(r'DATA VALIDADE:\s*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                if busca_validade:
                    data_encontrada = busca_validade.group(1)

            # ---> REGRAS DA TRABALHISTA
            elif origem == "Trabalhista":
                # 1. Status com "Escudo"
                if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                    status = "Positiva com Efeito Negativo"
                elif "CERTIDÃO NEGATIVA" in texto_do_pdf or "NÃO CONSTA COMO INADIMPLENTE" in texto_do_pdf:
                    status = "Negativa"
                elif "CERTIDÃO POSITIVA" in texto_do_pdf:
                    status = "Positiva"

                # 2. Busca a data de VALIDADE exata
                busca_validade = re.search(r'VALIDADE:\s*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                if busca_validade:
                    data_encontrada = busca_validade.group(1)

            # ---> REGRAS DO COMPRASNET
            elif origem == "Comprasnet":
                # 1. Status com "Escudo"
                if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                    status = "Positiva com Efeito Negativo"
                elif "CERTIDÃO - NEGATIVA" in texto_do_pdf or "NÃO CONSTA REGISTRO" in texto_do_pdf:
                    status = "Negativa"
                elif "CERTIDÃO - POSITIVA" in texto_do_pdf:
                    status = "Positiva"
                
                # 2. Busca de validade
                dias_validade = 30 
                busca_dias = re.search(r'VÁLIDA POR\s+(\d+)\s+DIAS', texto_do_pdf)
                if busca_dias:
                    dias_validade = int(busca_dias.group(1)) 

                busca_emissao = re.search(r'DATA DE EMISSÃO:\s*(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
                if busca_emissao:
                    data_emissao_str = busca_emissao.group(1).replace(".", "/") 
                    try:
                        formato = "%d/%m/%Y" if len(data_emissao_str) == 10 else "%d/%m/%y"
                        data_emissao_obj = datetime.strptime(data_emissao_str, formato)
                        data_validade_obj = data_emissao_obj + timedelta(days=dias_validade)
                        data_encontrada = data_validade_obj.strftime("%d/%m/%Y")
                    except Exception as e:
                        print(f"Aviso: Erro ao calcular a data do Comprasnet: {e}")
                        data_encontrada = data_emissao_str

            # ---> REGRAS DO FGTS
            elif origem == "FGTS":
                # 1. Status com "Escudo"
                if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                    status = "Positiva com Efeito Negativo"
                elif "SITUAÇÃO REGULAR" in texto_do_pdf:
                    status = "Negativa" 
                else:
                    status = "Positiva"
                
                # 2. Busca de data final
                busca_data = re.search(r'VALIDADE:\s*\d{2}[./]\d{2}[./]\d{2,4}\s*A\s*(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
                if busca_data:
                    data_encontrada = busca_data.group(1)

            # ---> REGRAS DA AGEHAB
            elif origem == "AGEHAB":
                # 1. Status com "Escudo"
                if "CERTIDÃO POSITIVA DE DÉBITOS COM EFEITO NEGATIVO" in texto_do_pdf or "CERTIDÃO POSITIVA COM EFEITO DE NEGATIVA" in texto_do_pdf:
                    status = "Positiva com Efeito Negativo"
                elif "CERTIDÃO NEGATIVA DE DÉBITOS" in texto_do_pdf:
                    status = "Negativa"
                elif "CERTIDÃO POSITIVA DE DÉBITOS" in texto_do_pdf:
                    status = "Positiva"

                # 2. Busca de data de atualização
                busca_data = re.search(r'ATUALIZADA EM:\s*(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
                if busca_data:
                    data_encontrada = busca_data.group(1)


            # ============================================================
            # FORMATAÇÃO DA DATA (Isso serve para TODAS as origens)
            # ============================================================
            
            # Se as regras acima falharem em achar a data exata, tenta achar qualquer data solta (Fallback genérico)
            if not data_encontrada:
                busca_data_solta = re.search(r'\d{2}[./]\d{2}[./]\d{2,4}', texto_do_pdf)
                if busca_data_solta:
                    data_encontrada = busca_data_solta.group()

            # Fatiar a data para pegar os 2 últimos dígitos do ano e formatar com pontos
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