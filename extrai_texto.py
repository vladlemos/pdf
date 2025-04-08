import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import os
from PIL import Image
import io

def extract_text_from_pdf(path, min_text_length=2000, apply_ocr_if_less=True):
    """
    Extrai texto de um PDF, usando OCR se a extração direta falhar.
    
    Args:
        path (str): Caminho para o arquivo PDF
        min_text_length (int): Tamanho mínimo de texto para considerar válido
        apply_ocr_if_less (bool): Se True, aplica OCR se o texto extraído for menor que min_text_length
    
    Returns:
        str: Texto extraído do PDF
    """
    def is_valid_text(text):
        """Verifica se o texto extraído é válido"""
        return text and len(text.strip()) >= min_text_length
    
    # Primeiro tentamos extrair texto diretamente
    texto_direto = ""
    try:
        with fitz.open(path) as doc:
            for page in doc:
                text = page.get_text().strip()
                if text:
                    texto_direto += text + "\n\n"  # Adiciona quebras entre páginas
            
            # Verifica se temos texto suficiente
            if is_valid_text(texto_direto):
                return texto_direto.strip()
            
            # Se não tem texto suficiente, verifica se há imagens para OCR
            needs_ocr = apply_ocr_if_less and not is_valid_text(texto_direto)
            if needs_ocr:
                print(f"Texto insuficiente ({len(texto_direto)} caracteres). Aplicando OCR...")
                
                # Primeiro tentamos extrair texto de imagens embutidas no PDF
                texto_ocr = try_extract_text_from_embedded_images(doc)
                if is_valid_text(texto_ocr):
                    return texto_ocr.strip()
                
                # Se ainda não tiver texto suficiente, converte o PDF para imagens
                print("Convertendo PDF para imagens para OCR...")
                return extract_text_with_ocr(path).strip()
            
            return texto_direto.strip()
    
    except Exception as e:
        print(f"Erro ao extrair texto diretamente: {e}")
        print("Tentando OCR como fallback...")
        return extract_text_with_ocr(path).strip()

def try_extract_text_from_embedded_images(doc):
    """Tenta extrair texto de imagens embutidas no PDF"""
    texto_ocr = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        for img_index, img in enumerate(page.get_images(full=True)):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                
                # Configurações otimizadas para OCR
                custom_config = r'--oem 3 --psm 6 -l por'
                texto_ocr += pytesseract.image_to_string(image, config=custom_config) + "\n\n"
                
            except Exception as e:
                print(f"Erro ao processar imagem {img_index} na página {page_num+1}: {e}")
                continue
    
    return texto_ocr

def extract_text_with_ocr(pdf_path, dpi=300):
    """Converte PDF para imagens e aplica OCR"""
    texto_ocr = ""
    try:
        imagens = convert_from_path(pdf_path, dpi=dpi, thread_count=4)
        
        # Configurações otimizadas para OCR
        custom_config = r'--oem 3 --psm 6 -l por'
        
        for i, imagem in enumerate(imagens):
            try:
                # Pré-processamento opcional da imagem pode ser adicionado aqui
                texto_pagina = pytesseract.image_to_string(imagem, config=custom_config)
                texto_ocr += texto_pagina + "\n\n"
            except Exception as e:
                print(f"Erro ao processar página {i+1} com OCR: {e}")
                continue
    
    except Exception as e:
        print(f"Erro ao converter PDF para imagens: {e}")
        return ""
    
    return texto_ocr