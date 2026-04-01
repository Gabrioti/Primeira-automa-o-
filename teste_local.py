#                   python teste_local.py
import sys
import subprocess

# ==========================================
# AUTO-INSTALADOR DE BIBLIOTECAS PYTHON
# ==========================================
def instalar_dependencias():
    pacotes = {
        'pdfplumber': 'pdfplumber',
        'pytesseract': 'pytesseract',
        'pdf2image': 'pdf2image'
    }
    
    for modulo, pacote_pip in pacotes.items():
        try:
            __import__(modulo)
        except ImportError:
            print(f"-> Biblioteca '{modulo}' não encontrada. Instalando automaticamente...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pacote_pip])
                print(f"-> '{modulo}' instalado com sucesso!\n")
            except Exception as e:
                print(f"-> ERRO ao tentar instalar '{modulo}': {e}")
                print("Por favor, instale manualmente no terminal.")
                sys.exit(1) # Para o código se não conseguir instalar

# Roda a verificação antes de tentar importar o resto
instalar_dependencias()

# ==========================================
# AGORA SIM, OS IMPORTS DO SEU CÓDIGO
# ==========================================
import os
import pdfplumber
import re
from datetime import datetime, timedelta
import pytesseract
from pdf2image import convert_from_path

# ==========================================
# 0. FUNÇÃO DE OCR (Para PDFs Fantasma e Fontes Corrompidas)
# ==========================================
def extrair_texto_com_ocr(caminho_pdf):
    print("-> Fonte corrompida ou PDF imagem detectado. Acionando OCR (isso pode levar alguns segundos)...")
    texto_extraido = ""
    try:
        imagens = convert_from_path(caminho_pdf) 
        for imagem in imagens:
            texto = pytesseract.image_to_string(imagem, lang='por')
            texto_extraido += texto + "\n"
        return texto_extraido.upper()
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return ""

# ==========================================
# 1. FUNÇÃO DETETIVE (Descobre a origem da CND)
# ==========================================
def identificar_cnd(texto):
    """Lê o texto e retorna a Origem e o Número correspondente."""
    if "AGEHAB" in texto or "AGÊNCIA GOIANA DE HABITAÇÃO" in texto or "AGENCIA GOIANA DE HABITACAO" in texto:
        return "AGEHAB", "7"
    elif "FUNDO DE GARANTIA" in texto or "FGTS" in texto or "CAIXA ECONOMICA FEDERAL" in texto:
        return "FGTS", "6"
    elif "SICAF" in texto or "COMPRASNET" in texto or "SISTEMA DE CADASTRAMENTO UNIFICADO" in texto:
        return "Comprasnet", "5"
    elif "JUSTIÇA DO TRABALHO" in texto or "DÉBITOS TRABALHISTAS" in texto:
        return "Trabalhista", "4"
    elif "MUNICIPAL" in texto or "PREFEITURA" in texto or "MUNICÍPIO" in texto:
        return "Municipal", "3"
    elif "ESTADO DE GOIAS" in texto or "RECEITA ESTADUAL" in texto or "FAZENDA PUBLICA ESTADUAL" in texto:
        return "Estadual", "2"
    elif "RECEITA FEDERAL" in texto or "FAZENDA NACIONAL" in texto or "MINISTÉRIO DA FAZENDA" in texto:
        return "Federal", "1"
    
    return None, None # Retorna vazio se não conseguir identificar

# ==========================================
# 2. FUNÇÃO PRINCIPAL DE PROCESSAMENTO EM LOTE
# ==========================================
def processar_todas_cnds():
    arquivos_pdf = [arquivo for arquivo in os.listdir('./') if arquivo.lower().endswith('.pdf')]
    
    if not arquivos_pdf:
        print("\nErro: Nenhum arquivo PDF foi encontrado nesta pasta.")
        print("Coloque os PDFs das CNDs na mesma pasta do código antes de rodar.")
        return

    print(f"\nIniciando AUTO-DETECÇÃO em {len(arquivos_pdf)} arquivo(s) PDF...")

    for nome_arquivo in arquivos_pdf:
        # Pula arquivos que já foram renomeados por esse script no formato "Numero - CND..."
        if re.match(r'^\d\s-\sCND', nome_arquivo):
            continue

        caminho_atual = f"./{nome_arquivo}"
        print(f"\n{'-'*50}")
        print(f"Lendo: {nome_arquivo}")
        
        status = "Indefinido"
        data_atualizacao = "00.00.00"
        data_encontrada = None
        origem = None
        numero_categoria = None
        cidade = "" # Inicializa a variável da cidade vazia
        
        try:
            with pdfplumber.open(caminho_atual) as pdf:
                primeira_pagina = pdf.pages[0]
                texto_do_pdf = primeira_pagina.extract_text()
                
                # Prepara o texto e conta quantas letras reais existem para checar corrupção de fonte
                if texto_do_pdf:
                    texto_do_pdf = texto_do_pdf.upper()
                    letras_normais = len(re.findall(r'[A-Z]', texto_do_pdf))
                else:
                    letras_normais = 0
                
                # 1. Verifica se precisa de OCR (vazio, curto ou cheio de símbolos)
                if not texto_do_pdf or len(texto_do_pdf.strip()) < 20 or letras_normais < 20:
                    texto_do_pdf = extrair_texto_com_ocr(caminho_atual)

                # 2. Manda o texto pro Detetive descobrir qual é a CND
                origem, numero_categoria = identificar_cnd(texto_do_pdf)

                if not origem:
                    print("-> AVISO: Não consegui identificar a qual órgão este PDF pertence. Pulando...")
                    continue

                print(f"-> Identificado como: CND {origem} (Categoria {numero_categoria})")

                # ============================================================
                # REGRAS DE LEITURA (Separadas por Origem)
                # ============================================================
                
                # ---> REGRAS DA FEDERAL
                if origem == "Federal":
                    if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                        status = "Positiva com Efeito Negativo"
                    elif "NEGATIVA" in texto_do_pdf or "NÃO CONSTA" in texto_do_pdf or "NAO CONSTA" in texto_do_pdf:
                        status = "Negativa"
                    elif "POSITIVA" in texto_do_pdf or "CONSTA" in texto_do_pdf:
                        status = "Positiva"
                    
                    busca_validade = re.search(r'V[ÁA]LIDA AT[ÉE]\s*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                    if busca_validade:
                        data_encontrada = busca_validade.group(1)

                # ---> REGRAS DA ESTADUAL (GOIÁS)
                elif origem == "Estadual":
                    if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                        status = "Positiva com Efeito Negativo"
                    elif "NEGATIVA" in texto_do_pdf or "NAO CONSTA DEBITO" in texto_do_pdf:
                        status = "Negativa"
                    elif "POSITIVA" in texto_do_pdf or "CONSTA DEBITO" in texto_do_pdf:
                        status = "Positiva"

                    dias_validade = 60
                    busca_dias = re.search(r'VALIDA POR\s+(\d+)\s+DIAS', texto_do_pdf)
                    if busca_dias:
                        dias_validade = int(busca_dias.group(1))

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

                # ---> REGRAS DA MUNICIPAL
                elif origem == "Municipal":
                    # 1. Tenta extrair o nome da cidade (Regex) e formata com .title()
                    busca_nome_cidade = re.search(r'(?:PREFEITURA MUNICIPAL DE|MUNIC[ÍI]PIO DE)\s+([A-ZÁÀÂÃÉÈÊÍÏÓÒÔÕÚÙÛÇ ]+)', texto_do_pdf)
                    
                    if busca_nome_cidade:
                        cidade = busca_nome_cidade.group(1).split('\n')[0].strip().title()
                        print(f"-> Cidade detectada: {cidade}")
                    
                    if not cidade:
                        print(f"\n[!] Atenção: Não achei o nome da cidade no PDF: {nome_arquivo}")
                        cidade = input("Por favor, digite o nome da cidade: ").strip().title()

                    # 2. Status
                    if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf or "EFEITO NEGATIVO" in texto_do_pdf:
                        status = "Positiva com Efeito Negativo"
                    elif "NEGATIVA" in texto_do_pdf or "NÃO CONSTA" in texto_do_pdf or "NAO CONSTA" in texto_do_pdf:
                        status = "Negativa"
                    elif "POSITIVA" in texto_do_pdf:
                        status = "Positiva"
                    
                    # 3. Busca de data por extenso
                    busca_emissao = re.search(r'VALIDADE[^\d]*(\d{1,2})\s+([A-ZÇ]+)[^\d]*(\d{4})', texto_do_pdf)
                    if busca_emissao:
                        dia = int(busca_emissao.group(1))
                        mes_texto = busca_emissao.group(2).replace("Ç", "C")
                        ano = int(busca_emissao.group(3))
                        meses = {"JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6, 
                                 "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12}
                        mes_numero = meses.get(mes_texto)
                        if mes_numero:
                            try:
                                data_obj = datetime(ano, mes_numero, dia)
                                data_encontrada = data_obj.strftime("%d/%m/%Y")
                            except: pass
                    
                    # 4. Plano B (Data com barras)
                    if not data_encontrada:
                        busca_validade_barras = re.search(r'(V[ÁA]LIDA AT[ÉE]|VALIDADE)[^\d]*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                        if busca_validade_barras:
                            data_encontrada = busca_validade_barras.group(2)

                # ---> REGRAS DA TRABALHISTA
                elif origem == "Trabalhista":
                    if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                        status = "Positiva com Efeito Negativo"
                    elif "CERTIDÃO NEGATIVA" in texto_do_pdf or "NÃO CONSTA COMO INADIMPLENTE" in texto_do_pdf:
                        status = "Negativa"
                    elif "CERTIDÃO POSITIVA" in texto_do_pdf:
                        status = "Positiva"

                    busca_validade = re.search(r'VALIDADE:\s*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                    if busca_validade:
                        data_encontrada = busca_validade.group(1)

                # ---> REGRAS DO COMPRASNET
                elif origem == "Comprasnet":
                    if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                        status = "Positiva com Efeito Negativo"
                    elif "CERTIDÃO - NEGATIVA" in texto_do_pdf or "NÃO CONSTA REGISTRO" in texto_do_pdf:
                        status = "Negativa"
                    elif "CERTIDÃO - POSITIVA" in texto_do_pdf:
                        status = "Positiva"
                    
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
                    if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                        status = "Positiva com Efeito Negativo"
                    elif "SITUAÇÃO REGULAR" in texto_do_pdf or "SITUACAO REGULAR" in texto_do_pdf:
                        status = "Negativa" 
                    else:
                        status = "Positiva"
                    
                    busca_data = re.search(r'VALIDADE:\s*\d{2}[./]\d{2}[./]\d{2,4}\s*A\s*(\d{2}[./]\d{2}[./]\d{2,4})', texto_do_pdf)
                    if busca_data:
                        data_encontrada = busca_data.group(1)

                # ---> REGRAS DA AGEHAB
                elif origem == "AGEHAB":
                    if "EFEITO DE NEGATIVA" in texto_do_pdf or "EFEITOS DE NEGATIVA" in texto_do_pdf:
                        status = "Positiva com Efeito Negativo"
                    elif "NEGATIVA" in texto_do_pdf:
                        status = "Negativa"
                    elif "POSITIVA" in texto_do_pdf:
                        status = "Positiva"

                    busca_validade = re.search(r'V[ÁA]LIDA AT[ÉE][^\d]*(\d{2}/\d{2}/\d{4})', texto_do_pdf)
                    if busca_validade:
                        data_encontrada = busca_validade.group(1)

                # ============================================================
                # FORMATAÇÃO DA DATA (Isso serve para TODAS as origens)
                # ============================================================
                if not data_encontrada:
                    busca_data_solta = re.search(r'\d{2}[./]\d{2}[./]\d{2,4}', texto_do_pdf)
                    if busca_data_solta:
                        data_encontrada = busca_data_solta.group()

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
            print(f"Erro ao tentar ler o arquivo {nome_arquivo}: {e}")
            continue

        # ==========================================
        # 3. RENOMEAR O ARQUIVO (Com verificador de duplicatas)
        # ==========================================
        
        # Regra de nomeação: se for Municipal, mostra só a cidade. Senão, mostra a origem.
        if origem == "Municipal" and cidade:
            nome_origem = cidade
        else:
            nome_origem = origem
        
        nome_base = f"{numero_categoria} - CND {nome_origem} - {status} - {data_atualizacao}"
        nome_final = f"{nome_base}.pdf"
        
        contador = 1
        while os.path.exists(f"./{nome_final}"):
            nome_final = f"{nome_base} ({contador}).pdf"
            contador += 1
        
        print(f"-> Status: {status} | Data: {data_atualizacao}")
        
        try:
            os.rename(caminho_atual, f"./{nome_final}")
            print(f"-> SUCESSO! Renomeado para: '{nome_final}'")
        except Exception as e:
            print(f"-> ERRO ao tentar renomear o arquivo: {e}")

    print(f"\n{'-'*50}")
    print("Automação concluída! Todos os PDFs possíveis foram processados.")

# ==========================================
# GATILHO DE EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    processar_todas_cnds()