import streamlit as st
import pandas as pd
import re
from PyPDF2 import PdfReader
import unicodedata
from fpdf import FPDF
import time


def normalizar_texto(texto):
    """Remove acentos e converte para minúsculas."""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto.lower().strip()


def extrair_nomes_pdf(pdf_file):
    """Extrai nomes completos do PDF, normalizando-os."""
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    matches = re.findall(r'\b[A-ZÀ-Ú][A-ZÀ-Ú]+\s[A-ZÀ-Ú ]+\b', text)
    return sorted({normalizar_texto(name) for name in matches})


def gerar_pdf(resultados):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Relatorio de Alunos Aprovados", ln=True, align='C')
    pdf.ln(10)

    for idx, resultado in enumerate(resultados, start=1):
        pdf.cell(0, 10, f"{idx}. {resultado['Nome']} - {resultado['Arquivo PDF']}", ln=True)

    pdf_file = "alunos_aprovados.pdf"
    pdf.output(pdf_file)
    return pdf_file


def main():
    st.title("Comparador de Alunos Aprovados")
    st.write("Carregue um arquivo CSV com os nomes dos alunos e um ou mais PDFs com as listas de aprovados.")

    csv_file = st.file_uploader("Carregar arquivo CSV", type=["csv"])
    pdf_files = st.file_uploader("Carregar arquivos PDF", type=["pdf"], accept_multiple_files=True)

    if csv_file and pdf_files:
        df_csv = pd.read_csv(csv_file)
        colunas = df_csv.columns.tolist()
        coluna_nomes = st.selectbox("Selecione a coluna que contém os nomes:", colunas)
        csv_names = {normalizar_texto(name) for name in df_csv[coluna_nomes].dropna().tolist()}

        results = []
        total_pdfs = len(pdf_files)
        progress_bar = st.progress(0)

        for i, pdf_file in enumerate(pdf_files, start=1):
            approved_names = extrair_nomes_pdf(pdf_file)
            common_names = sorted(csv_names.intersection(approved_names))

            for idx, name in enumerate(common_names, start=1):
                results.append({"Ordem": idx, "Nome": name, "Arquivo PDF": pdf_file.name})

            progress_bar.progress(i / total_pdfs)

        if results:
            st.success("Alunos aprovados encontrados!")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df)

            csv_download = results_df.to_csv(index=False).encode("utf-8")
            st.download_button("Baixar resultados como CSV", data=csv_download, file_name="alunos_aprovados.csv")

            pdf_download = gerar_pdf(results)
            with open(pdf_download, "rb") as pdf_file:
                st.download_button("Baixar resultados como PDF", data=pdf_file, file_name="alunos_aprovados.pdf",
                                   mime="application/pdf")
        else:
            st.warning("Nenhum aluno aprovado foi encontrado nos PDFs enviados.")


if __name__ == "__main__":
    main()
