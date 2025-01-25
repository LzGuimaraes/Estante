from django.shortcuts import render, redirect 
import zipfile
from bs4 import BeautifulSoup
import os
from django.contrib import messages
from django.conf import settings
from .models import Documento
# Create your views here.

def estante(request):
    """
    Funcionalidade: Lista os livros do usuario(no tengo users).

    """
    livros = Documento.objects.all()
    #livros.delete()
    return render(request, 'estante.html', {'livros': livros})


def upload_epub(request):
    if request.method ==  'POST' and request.FILES['epub-file'] and  request.FILES['capa']:
        epub_file = request.FILES['epub-file']
        capa = request.FILES['capa']
        titulo, html_path = processa_epub(epub_file)
        documento_existente = Documento.objects.filter(titulo=titulo).first()
        if documento_existente:
            # Se o documento já existe, evite duplicar
            # Opcional: Atualize os campos caso necessário
            documento_existente.capa = capa  # Atualiza a capa, se necessário
            documento_existente.save()
            messages.error(request,'Livro repetido')
            return redirect('estante')
        documento = Documento.objects.create(
            titulo=titulo,
            conteudo_html=os.path.relpath(html_path, settings.MEDIA_ROOT),  # Caminho relativo ao MEDIA_ROOT
            autor=titulo,
            capa=capa
        )
        
        return redirect('estante')

def livro(request, id_livro):
    livro = Documento.objects.get(id=id_livro)
    print(livro)
    return render(request, 'livro.html')

def processa_epub(epub_file):

    """
    Processa um arquivo EPUB, extraindo seu conteúdo e gerando um arquivo HTML.
    Args:
        epub_file (str): Caminho para o arquivo EPUB a ser processado.
    Returns:
        None
    """
    nome_do_livro = str(epub_file).replace('.epub','')
    livro_dir = os.path.join(settings.MEDIA_ROOT, 'documentos', nome_do_livro)
    os.makedirs(livro_dir, exist_ok=True)

    # Nome do arquivo HTML de saída
    output_file = os.path.join(livro_dir, f"{nome_do_livro}.html")


    # Abrir e listar os arquivos no ePub
    with zipfile.ZipFile(epub_file, 'r') as z:
        page_content = ''
        for file in z.namelist():
            # Verificar e salvar imagens
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                image_data = z.read(file)
                image_path = os.path.join(livro_dir, os.path.basename(file))
                with open(image_path, 'wb') as img_file:
                    img_file.write(image_data)

            # Processar arquivos HTML ou XHTML
            elif file.endswith('.html') or file.endswith('.xhtml'):
                content = z.read(file).decode('utf-8')

                # Usar BeautifulSoup para processar o HTML
                soup = BeautifulSoup(content, 'html.parser')

                # Atualizar caminhos das imagens no HTML
                for img in soup.find_all('img'):
                    if 'src' in img.attrs:
                        img_src = img['src']
                        img_name = os.path.basename(img_src)
                        img['src'] = img_name

                # Obter o conteúiner principal (geralmente <body> ou equivalente)
                body = soup.find('body') or soup
                #print(body)
                body_content = body.decode_contents()
                soup_content = BeautifulSoup(body_content, 'html.parser')
                for p in soup_content.find_all('p'):
                    page_content += f"\n<div class='page'>\n{p}\n</div>\n"
                for img in soup_content.find_all('img'):
                    page_content += f"\n<div class='page'>\n{img}\n</div>\n"
                
 # Salvar o arquivo HTML
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(page_content)

    return nome_do_livro, output_file
