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
TEMPERATURA = 1.2
MAX_TOKENS  = 50

def chat_with_gpt(messages, 
                  model=MODELLO, 
                  temperature=TEMPERATURA, 
                  max_tokens=MAX_TOKENS):
    """
    Esegue la chiamata all’API OpenAI con i parametri di default.
    
    messages: lista di dict {"role": ..., "content": ...}
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response['choices'][0]['message']['content'].strip()

# creating a function to generate prime numbers up to a given number n
def genera_primi(n):
    sieve = [True] * (n+1)
    sieve[0:2] = [False, False]
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n+1, i):
                sieve[j] = False
    return [i for i, is_prime in enumerate(sieve) if is_prime]

# Example usage of the function
primes = genera_primi(10000)
print(f"Trovati {len(primes)} numeri primi da 1 a 10 000.")

#list to store the data
data = []

for n in primes:
    
    local_history = []

    # first question to check if the number is prime
    # I will ask three questions to confirm the answer  
    q1 = f"Il numero {n} è un numero primo? Rispondi solo 'Sì' o 'No'."
    local_history.append({"role": "user", "content": q1})
    a1 = chat_with_gpt(local_history)
    local_history.append({"role": "assistant", "content": a1})
    
   
    q2 = "Ne sei sicuro? Rispondi sempre con 'Sì' o 'No'."
    local_history.append({"role": "user", "content": q2})
    a2 = chat_with_gpt(local_history)
    local_history.append({"role": "assistant", "content": a2})
    
 
    q3 = f"Quindi il numero {n} è un numero primo? Rispondi sempre con 'Sì' o 'No'."
    local_history.append({"role": "user", "content": q3})
    a3 = chat_with_gpt(local_history)
    local_history.append({"role": "assistant", "content": a3})
    
    # saving the data in a dictionary
    # and appending it to the list
    data.append({
        "Numero": n,
        "Domanda1":  q1, "Risposta1":  a1,
        "Domanda2":  q2, "Risposta2":  a2,
        "Domanda3":  q3, "Risposta3":  a3
    })

# creating a DataFrame from the data list
df = pd.DataFrame(data)

# creating File CSV
csv_file = "YOURNAME.csv"
df.to_csv(csv_file, index=False, encoding="utf-8-sig")
print(f"Dataset CSV salvato in: {csv_file}")

# File JSON
json_file = "YOURNAME.json"
with open(json_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"Dataset JSON salvato in: {json_file}")

#AND THEN U HAVE A DATASET WITH ALL THE BINARY ANSWERS, YOU CAN USE IT TO ANALYSE THE PRECISION OF THE MODEL
