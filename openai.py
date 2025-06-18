import openai
import json
from datetime import datetime
import pandas as pd
import time
from fpdf import FPDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.doctemplate import Indenter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import openai
import csv
import time
from reportlab.lib.pagesizes import A4
import unicodedata

OPENAI_API_KEY ="insert your OpenAI API key here"
openai.api_key = OPENAI_API_KEY

# Constant parameters for the API
MODELLO  = "gpt-4o-mini" #cheaper one
MAX_RETRY = 3


def chat_with_gpt(messages, 
                  temperature, 
                  max_tokens):
    """
    Esegue la chiamata all’API OpenAI con i parametri di default.

    messages: lista di dict {"role": ..., "content": ...}
    """
    response = openai.ChatCompletion.create(
        model=MODELLO,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response['choices'][0]['message']['content'].strip()



def normalizza_ascii(testo):
    return unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode("ascii")

# calls the api and returns the response

def call_api_single_prompt(prompt, temperature=0.7, max_tokens=500):
    retries = 0
    while retries < MAX_RETRY:
        try:
            messages = [{"role": "user", "content": prompt}]
            risposta = chat_with_gpt(messages, temperature=temperature, max_tokens=max_tokens)
            return risposta
        except openai.error.APIError as e:
            print(f"Errore API, tentativo {retries+1} di {MAX_RETRY} per temperatura={temperature}: {e}")
            retries += 1
            time.sleep(2)
    print(f"Fallito dopo {MAX_RETRY} tentativi per temperatura={temperature}: {prompt}")
    return None


# Save all responses to a CSV file
def salva_risposte_csv(filename, dati):
    with open(filename, mode='w', newline='', encoding='utf-8') as file_csv:
        writer = csv.DictWriter(file_csv, fieldnames=["categoria", "vaghezza", "prompt","temperature", "risposta"])
        writer.writeheader()
        for row in dati:
            writer.writerow(row)

#just modifies the prompt as user requested
prompt_set = {
    "generazione_fantastica": {
        "vago": [
            "Scrivi l'inizio di una storia che inizia con un viaggio imprevisto.",
            "Descrivi un oggetto molto antico trovato in un mercatino",
            "Scrivi un dialogo tra due persone che non si capiscono bene.",
            
        ],
        "preciso": [
            "Scrivi un racconto breve in cui una persona riceve per errore una lettera indirizzata a un'altra identità, e decide comunque di seguire le istruzioni contenute, intraprendendo un viaggio che sfocia in un finale sorprendente ma coerente.",
            "Immagina che uno studioso acquisti in un mercatino un oggetto apparentemente comune, ma che rivela via via proprietà anomale. Racconta in modo coerente e realistico il processo con cui egli cerca di capirne l’origine, evitando colpi di scena irrealistici.",
            "Scrivi un dialogo tra due personaggi con obiettivi impliciti opposti, ma che fingono di collaborare. Il lettore deve capire l’ambiguità dalle risposte e dai sottintesi.",
            ]
    },
    "domande_tecniche": {
        "vago": [
            "Come funzionano le reti neurali?",
            "Cosa succede quando un gene è danneggiato?",
            "Come si scelgono i rappresentanti in un parlamento?",
           
        ],
        "preciso": [
            "Spiega il funzionamento di una rete neurale feedforward specificando le funzioni di attivazione più usate e come intervengono nel backpropagation, con esempi matematici.",
            "Descrivi come una mutazione puntiforme può interferire con la sintesi proteica e contribuire all’insorgenza di una malattia monogenica rara.",
            "Confronta i sistemi proporzionali con soglia di sbarramento e i sistemi maggioritari a doppio turno, illustrando gli effetti sulla rappresentanza.",
           ]
    },
    "inferenza_logica": {
        "vago": ["Se qualcosa succede sempre prima di qualcos’altro, cosa possiamo dedurre?",
                "Cosa implica il fatto che due affermazioni siano entrambe vere, ma contraddittorie?",
                "Quali conseguenze logiche ha il fatto che un insieme sia contenuto in un altro, ma non lo esaurisca?",
                            
        ],
        "preciso": ["In un'azienda, tutti i dipendenti che partecipano al progetto X hanno ricevuto una formazione speciale. Alcuni dipendenti che hanno ricevuto quella formazione lavorano anche ad altri progetti, e uno di loro, Marco, è stato trasferito al progetto Y. Se si scopre che Marco ha commesso un errore legato alla mancanza di formazione, quale tra le seguenti affermazioni è logicamente incompatibile con le premesse iniziali?",
                    "Ogni scienziato che sostiene la teoria A è anche convinto che la teoria B sia almeno parzialmente errata. Tuttavia, vi sono scienziati che rigettano entrambe le teorie. Se un certo ricercatore afferma che la teoria A è plausibile ma che la teoria B è del tutto corretta, quali incoerenze si possono ipotizzare nel suo sistema di credenze rispetto alle affermazioni iniziali?",
                    "Un’indagine dimostra che: (1) tutte le piattaforme che utilizzano crittografia end-to-end non conservano i messaggi in chiaro; (2) alcune piattaforme che dichiarano di usare crittografia end-to-end sono risultate non conformi allo standard minimo. Se un utente usa una piattaforma che conserva i messaggi in chiaro ma pubblicizza l’uso di crittografia end-to-end, quali conclusioni si possono trarre riguardo all’affidabilità della dichiarazione e alla coerenza con la definizione tecnica di crittografia end-to-end?",
                    ]
    },
    "storia": {
        "vago": ["Quali furono le principali conseguenze sociali di una rivoluzione importante nella storia francese?",
                 "Che tipo di tensioni internazionali caratterizzarono il confronto tra potenze nel XX secolo?",
                 "Quali furono le principali difficoltà nell’unificazione politica di uno Stato europeo nel XIX secolo?",
                       
        ],
        "preciso": ["Durante la Rivoluzione francese, il passaggio dalla monarchia costituzionale alla Repubblica giacobina comportò un netto cambiamento di paradigma politico. In che modo le tensioni tra legalità, sovranità popolare e violenza politica si manifestarono nella fase del Terrore, e che tipo di legittimità fu invocata per giustificare la repressione?",
                    "Nel contesto della Guerra Fredda, la crisi dei missili di Cuba del 1962 rappresentò uno snodo cruciale. Quali furono i fattori strategici e diplomatici che portarono al confronto tra Stati Uniti e URSS, e come la gestione dell’evento influenzò il concetto di deterrenza nucleare negli anni successivi?",
                    "Durante il processo di unificazione italiana, diverse forze politiche e sociali agirono con obiettivi non sempre convergenti. Considerando il ruolo di Cavour, Mazzini e Garibaldi, quali furono le principali tensioni ideologiche e strategiche che emersero tra loro, e in che misura influenzarono la struttura istituzionale del Regno d’Italia successivo al 1861?",
                   
        ]
    }
}

# define temperature settings
temperature_settings = [0.2, 1.2]

risultati = []

for categoria, vaghezze in prompt_set.items():
    for vaghezza, prompts in vaghezze.items():
        for prompt in prompts:
            for temp in temperature_settings:
                print(f"Elaborando: categoria={categoria}, vaghezza={vaghezza}, temperatura={temp}")
                risposta = call_api_single_prompt(prompt, temperature=temp)
                risultati.append({
                    "categoria": categoria,
                    "vaghezza": vaghezza,
                    "prompt": prompt,
                    "temperature": temp,
                    "risposta": risposta if risposta else ""
                })
                time.sleep(1)

# Save results to CSV
nome_file_csv = "YOUR_NAME.csv"
salva_risposte_csv(nome_file_csv, risultati)
print(f"Dati salvati in {nome_file_csv}")

# CREATE A LEGGIBLE PDF FROM THE CSV FILE
class MyDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'toc_level'):
            text = flowable.getPlainText()
            bk_name = "bk_" + text.replace(" ", "_").replace(".", "")
            self.canv.bookmarkPage(bk_name)
            flowable._bookmarkName = bk_name
            page_num = self.canv.getPageNumber()
            self.notify('TOCEntry', (flowable.toc_level, text, page_num))

def genera_pdf_da_csv(csv_file, pdf_file):
    doc = MyDocTemplate(
        pdf_file,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    heading_style = styles['Heading1']
    heading2_style = styles['Heading2']
    heading3_style = ParagraphStyle(name='Heading3', parent=styles['Heading3'], fontSize=11, spaceBefore=6, spaceAfter=6)
    toc_style = ParagraphStyle(name='TOCHeading', fontSize=18, leading=22, spaceAfter=20)

    story = []
    story.append(Paragraph("Raccolta Risposte Prompt", styles['Title']))
    story.append(Spacer(1, 20))

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(fontSize=14, name='TOCLevel1', leftIndent=20, firstLineIndent=-20, spaceBefore=5),
        ParagraphStyle(fontSize=12, name='TOCLevel2', leftIndent=40, firstLineIndent=-20, spaceBefore=0),
    ]
    story.append(Paragraph("Indice", toc_style))
    story.append(toc)
    story.append(PageBreak())

    with open(csv_file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        current_category = None
        current_vaghezza = None

        for i, row in enumerate(reader):
            categoria = row['categoria']
            vaghezza = row['vaghezza']
            prompt = row['prompt']
            risposta = row['risposta']
            temperatura = row.get('temperature', '').strip()

            # Nuova categoria
            if categoria != current_category:
                current_category = categoria
                header_cat = Paragraph(categoria.replace("_", " ").capitalize(), heading_style)
                header_cat.toc_level = 0
                story.append(header_cat)
                story.append(Spacer(1, 20))
                current_vaghezza = None

            # Nuova vaghezza
            if vaghezza != current_vaghezza:
                current_vaghezza = vaghezza
                header_vag = Paragraph(vaghezza.capitalize(), heading2_style)
                header_vag.toc_level = 1
                story.append(header_vag)
                story.append(Spacer(1, 15))

            # Temperatura: mostrata ma non indicizzata
            temperatura_text = f"Temperatura: {temperatura}" if temperatura else "Temperatura: N/A"
            story.append(Paragraph(temperatura_text, heading3_style))

            # Prompt e risposta
            story.append(Paragraph(f"<b>Prompt:</b> {prompt}", normal_style))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>Risposta:</b> {risposta if risposta else 'Nessuna risposta disponibile'}", normal_style))
            story.append(Spacer(1, 24))

            if (i + 1) % 10 == 0:
                story.append(PageBreak())

    doc.multiBuild(story)

if __name__ == "__main__":
    genera_pdf_da_csv("YOUR_NAME.csv", "YOUR_NAME.pdf")
    print("PDF generato con successo: YOUR_NAME.pdf")
