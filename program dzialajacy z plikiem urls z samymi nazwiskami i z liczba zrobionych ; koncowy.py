import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_powiat_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Znajdź tabelę na podstawie nagłówków kolumn 'Powiat' i 'Razem'
    target_table = None
    tables = soup.find_all('table')
    for table in tables:
        headers = table.find_all('th')
        header_texts = [header.text.strip() for header in headers]
        if 'Powiat' in header_texts and 'Razem' in header_texts:
            target_table = table
            break

    powiat_list = []

    if target_table:
        # Znajdź wszystkie wiersze (tr) w tabeli
        rows = target_table.find_all('tr')

        for index, row in enumerate(rows):
            # Pomijamy pierwszy wiersz (nagłówki kolumn)
            if index == 0:
                continue

            # Znajdź wszystkie komórki (td) w wierszu (tr)
            cells = row.find_all('td')

            # Sprawdź, czy wiersz ma odpowiednią liczbę komórek
            if len(cells) >= 5:
                dic = {}
                dic['Powiat'] = cells[0].text.strip()
                dic['Razem'] = cells[4].text.strip()  # Użyj wartości z piątej kolumny

                # Dodaj do listy tylko jeśli 'Powiat' i 'Razem' są obecne
                if dic['Powiat'] and dic['Razem']:
                    powiat_list.append(dic)

    return powiat_list

# Czytaj nazwiska z pliku tekstowego z kodowaniem UTF-8
with open('urls.txt', 'r', encoding='utf-8') as file:
    surnames = [line.strip() for line in file if line.strip()]

# Generuj URL-e na podstawie nazwisk
base_url = 'http://nlp.actaforte.pl:8080/Nomina/Ndistr?nazwisko='
urls = [base_url + surname for surname in surnames]

# Pobierz dane z każdej strony
data_frames = []
total_surnames = len(surnames)
for i, url in enumerate(urls):
    powiat_list = get_powiat_data(url)
    df = pd.DataFrame(powiat_list)
    
    # Usuń wiersz o indeksie 1 (drugi wiersz)
    if not df.empty and len(df) > 0:
        df = df.drop(index=0)
    
    # Dodaj nazwisko jako nagłówek kolumny
    surname = url.split('=')[-1]
    df.columns = pd.MultiIndex.from_product([[surname], df.columns])
    
    data_frames.append(df)
    
    # Informacja o postępie
    print(f"Przetworzono {i+1}/{total_surnames} nazwisk: {surname}")

# Połącz dane z różnych stron z odstępem jednej kolumny
combined_df = data_frames[0]

for df in data_frames[1:]:
    combined_df = pd.concat([combined_df, pd.DataFrame({('', ''): [''] * len(df)}), df], axis=1)

# Przekształć MultiIndex na zwykłe kolumny
combined_df.columns = ['_'.join(col).strip() for col in combined_df.columns.values]

# Zapisz dane do pliku Excel (bez indeksów)
combined_df.to_excel('powiat_data_combined.xlsx', index=False)

print("Dane zostały zapisane do pliku powiat_data_combined.xlsx")
