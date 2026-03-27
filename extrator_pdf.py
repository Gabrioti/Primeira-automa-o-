from playwright.sync_api import sync_playwright

def extrair_pdf():
    with sync_playwright() as p:
        navegador = p.chromium.launch(
    headless=True,
    proxy={
        "server": "http://IP_DE_UM_PROXY_BRASILEIRO:PORTA" # O disfarce entra aqui
    }
)
        
        # 1. A MÁGICA ACONTECE AQUI: Criamos um "contexto" já com as credenciais
        contexto = navegador.new_context(
            http_credentials={
                'username': 'FAGabrioti',
                'password': 'Lara@2854'
            }
        )
        
        # 2. Abrimos a página usando esse contexto autenticado
        pagina = contexto.new_page()

        print("Acessando a página (o login será feito automaticamente)...")
        # O Playwright vai preencher aquela janela invisível pra você
        pagina.goto("http://appweb2.agehab.com.br/")

        # Aguarda a página carregar
        pagina.wait_for_load_state('networkidle')

        # 3. Navegar pelos botões
        print("Acessando o Palladio Gerencial...")
        # Lembre-se que o texto aqui tem que ser exatamente igual ao que está no botão do site
        pagina.locator("text='palladiogerencial'").click() 
        pagina.wait_for_load_state('networkidle')

        print("Acessando Certidões...")
        # 4. Preparar para interceptar o download do PDF
        with pagina.expect_download() as info_download:
            pagina.locator("text='Certidões'").click() 
        
        # 5. Salvar o arquivo baixado
        download = info_download.value
        nome_arquivo = download.suggested_filename
        caminho_salvar = f"./{nome_arquivo}" # Salva na mesma pasta do código
        
        download.save_as(caminho_salvar)
        print(f"Sucesso! PDF salvo como: {caminho_salvar}")

        navegador.close()

if __name__ == "__main__":
    extrair_pdf()