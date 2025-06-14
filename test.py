# from flask import Flask, render_template
# import folium
# import pandas as pd
# from geopy.geocoders import Nominatim
# import time
# import os
# import re
#
# app = Flask(__name__)
#
#
# def clean_address(address):
#     """Czyści i normalizuje adres przed geokodowaniem"""
#     if pd.isna(address):
#         return None
#
#     # Konwertuj na string jeśli nie jest
#     address = str(address).strip()
#
#     # Usuń dodatkowe spacje
#     address = re.sub(r'\s+', ' ', address)
#
#     # Usuń zbędne znaki interpunkcyjne na końcu
#     address = address.rstrip('.,;')
#
#     return address
#
#
# def geocode_addresses(df):
#     geolocator = Nominatim(user_agent="galerie_map_v1.0")
#     latitudes = []
#     longitudes = []
#
#     for idx, row in df.iterrows():
#         address = clean_address(row['address'])
#
#         if not address:
#             print(f"Wiersz {idx}: Pusty adres")
#             latitudes.append(None)
#             longitudes.append(None)
#             continue
#
#         # Lista wariantów adresu do wypróbowania
#         address_variants = []
#
#         # Wariant 1: Oryginalny adres + Polska (jeśli nie ma)
#         if "Polska" not in address.lower() and "Poland" not in address.lower():
#             address_variants.append(address + ", Polska")
#         else:
#             address_variants.append(address)
#
#         # Wariant 2: Bez słowa "Polska" jeśli już jest
#         if "Polska" in address.lower():
#             clean_addr = re.sub(r',?\s*Polska\s*,?', '', address, flags=re.IGNORECASE).strip()
#             if clean_addr:
#                 address_variants.append(clean_addr + ", Poland")
#
#         # Wariant 3: Tylko miasto jeśli adres zawiera więcej informacji
#         parts = address.split(',')
#         if len(parts) > 1:
#             # Spróbuj z ostatnią częścią (prawdopodobnie miasto)
#             city_part = parts[-1].strip()
#             if "Polska" not in city_part.lower():
#                 address_variants.append(city_part + ", Polska")
#
#         print(f"Wiersz {idx}: Geokodowanie adresu: {address}")
#         location = None
#
#         # Próbuj każdy wariant adresu
#         for variant in address_variants:
#             try:
#                 print(f"  Próbuję wariant: {variant}")
#                 time.sleep(1.5)  # Zwiększone opóźnienie dla stabilności
#                 location = geolocator.geocode(variant, timeout=15, exactly_one=True)
#
#                 if location:
#                     # Sprawdź czy lokalizacja jest w Polsce (przybliżone granice)
#                     lat, lon = location.latitude, location.longitude
#                     if 49.0 <= lat <= 54.9 and 14.1 <= lon <= 24.2:
#                         print(f"  ✓ Znaleziono w Polsce: {lat:.4f}, {lon:.4f}")
#                         break
#                     else:
#                         print(f"  ⚠ Znaleziono poza Polską: {lat:.4f}, {lon:.4f} - szukam dalej")
#                         location = None
#                 else:
#                     print(f"  ✗ Nie znaleziono dla: {variant}")
#
#             except Exception as e:
#                 print(f"  ✗ Błąd dla {variant}: {e}")
#                 continue
#
#         if location:
#             latitudes.append(location.latitude)
#             longitudes.append(location.longitude)
#             print(f"  → Końcowy rezultat: {location.latitude:.4f}, {location.longitude:.4f}")
#         else:
#             print(f"  → Nie udało się znaleźć lokalizacji dla żadnego wariantu")
#             latitudes.append(None)
#             longitudes.append(None)
#
#     df['latitude'] = latitudes
#     df['longitude'] = longitudes
#     return df
#
#
# def fix_csv_structure(df):
#     """Naprawia błędną strukturę CSV gdzie dane są przesunięte"""
#     print("Naprawiam strukturę CSV...")
#     print(f"Oryginalne kolumny: {list(df.columns)}")
#
#     # Sprawdź pierwszych kilka wierszy
#     print("Pierwsze 3 wiersze:")
#     for i in range(min(3, len(df))):
#         print(f"  {df.iloc[i].to_dict()}")
#
#     # Jeśli latitude zawiera adresy (stringi), znaczy że kolumny są przesunięte
#     if df['latitude'].dtype == 'object' and any(',' in str(val) for val in df['latitude'].head()):
#         print("Wykryto przesunięcie kolumn - naprawiam...")
#
#         # Stwórz nową, poprawną strukturę
#         df_fixed = pd.DataFrame()
#
#         df_fixed['name'] = df['name']
#         df_fixed['address'] = df['latitude']  # Prawdziwe adresy są w kolumnie latitude
#
#         # Wyczyść współrzędne - usuń stare błędne wartości
#         df_fixed['latitude'] = None
#         df_fixed['longitude'] = None
#
#         print("Struktura naprawiona!")
#         return df_fixed
#
#     return df
#
#
# @app.route("/")
# def home():
#     source_file = "galerie.csv"  # Poprawiona nazwa pliku
#
#     # Sprawdź czy plik istnieje
#     if not os.path.exists(source_file):
#         return f"Błąd: Nie znaleziono pliku {source_file}"
#
#     try:
#         # Wczytanie pliku z różnymi kodowaniami
#         encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1250']
#         df = None
#
#         for encoding in encodings:
#             try:
#                 df = pd.read_csv(source_file, encoding=encoding)
#                 print(f"Wczytano plik z kodowaniem: {encoding}")
#                 break
#             except UnicodeDecodeError:
#                 continue
#
#         if df is None:
#             return "Błąd: Nie udało się wczytać pliku CSV"
#
#         print(f"Wczytano {len(df)} wierszy")
#         print(f"Oryginalne kolumny: {list(df.columns)}")
#
#         # Napraw strukturę CSV jeśli jest potrzeba
#         df = fix_csv_structure(df)
#
#         # Sprawdź czy kolumna 'address' istnieje
#         if 'address' not in df.columns:
#             return f"Błąd: Brak kolumny 'address' w pliku. Dostępne kolumny: {list(df.columns)}"
#
#         print(f"Końcowe kolumny: {list(df.columns)}")
#
#         # Sprawdzenie czy współrzędne istnieją i są prawidłowe
#         coords_invalid = (
#                 'latitude' not in df.columns or
#                 'longitude' not in df.columns or
#                 df['latitude'].isnull().all() or
#                 df['longitude'].isnull().all() or
#                 (df['latitude'].nunique() <= 1 and df['longitude'].nunique() <= 1)
#         )
#
#         if coords_invalid:
#             print("Współrzędne są nieprawidłowe lub puste, wykonuję geokodowanie...")
#             df = geocode_addresses(df)
#
#             # Zapisz z kopią zapasową
#             backup_file = source_file.replace('.csv', '_backup.csv')
#             if os.path.exists(source_file):
#                 import shutil
#                 shutil.copy2(source_file, backup_file)
#                 print(f"Utworzono kopię zapasową: {backup_file}")
#
#             df.to_csv(source_file, index=False, encoding="utf-8-sig")
#             print("Geokodowanie zakończone i zapisane.")
#
#         # Tworzenie mapy
#         valid_coords = df[(df['latitude'].notnull()) & (df['longitude'].notnull())]
#
#         if len(valid_coords) > 0:
#             # Wyśrodkuj mapę na podstawie wszystkich punktów
#             center_lat = valid_coords['latitude'].mean()
#             center_lon = valid_coords['longitude'].mean()
#             start_coords = [center_lat, center_lon]
#
#             # Dostosuj zoom na podstawie rozrzutu punktów
#             lat_range = valid_coords['latitude'].max() - valid_coords['latitude'].min()
#             lon_range = valid_coords['longitude'].max() - valid_coords['longitude'].min()
#             zoom = 10 if max(lat_range, lon_range) > 1 else 13
#         else:
#             start_coords = [52.4069, 16.9299]  # Poznań domyślnie
#             zoom = 6
#
#         m = folium.Map(location=start_coords, zoom_start=zoom)
#
#         # Dodaj markery
#         successful_markers = 0
#         for idx, row in df.iterrows():
#             if pd.notnull(row.get('latitude')) and pd.notnull(row.get('longitude')):
#                 popup_text = f"<b>{row.get('name', 'Brak nazwy')}</b><br>{row.get('address', '')}"
#
#                 folium.Marker(
#                     location=[row['latitude'], row['longitude']],
#                     popup=folium.Popup(popup_text, max_width=300),
#                     tooltip=row.get('name', 'Punkt'),
#                     icon=folium.Icon(color='red', icon='info-sign')
#                 ).add_to(m)
#                 successful_markers += 1
#
#         print(f"Dodano {successful_markers} markerów do mapy")
#
#         # Stwórz katalog static jeśli nie istnieje
#         os.makedirs('static', exist_ok=True)
#         m.save("static/galerie_w_polsce_interaktywna.html")
#
#         return render_template("index.html")
#
#     except Exception as e:
#         return f"Błąd aplikacji: {str(e)}"
#
#
# if __name__ == "__main__":
#     app.run(debug=True)

# from flask import Flask, render_template, request, jsonify
# import folium
# import pandas as pd
# from geopy.geocoders import Nominatim
# import time
# import os
# import re
# import requests
# from bs4 import BeautifulSoup
# from datetime import datetime, timedelta
# from geopy.distance import geodesic
# import json
# # from diagn import EchoPoznanInfiniteScrollScraper
#
#
# app = Flask(__name__)
#
#
# def clean_address(address):
#     """Czyści i normalizuje adres przed geokodowaniem"""
#     if pd.isna(address):
#         return None
#
#     # Konwertuj na string jeśli nie jest
#     address = str(address).strip()
#
#     # Usuń dodatkowe spacje
#     address = re.sub(r'\s+', ' ', address)
#
#     # Usuń zbędne znaki interpunkcyjne na końcu
#     address = address.rstrip('.,;')
#
#     return address
#
#
# def scrape_echo_poznan_events():
#     """Pobiera wydarzenia ze strony Echo Poznań"""
#     try:
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         }
#
#         # URL do listy wydarzeń
#         events_url = "https://echopoznan.com/wydarzenia/"
#
#         print(f"Pobieranie wydarzeń z: {events_url}")
#         response = requests.get(events_url, headers=headers, timeout=30)
#         response.raise_for_status()
#
#         soup = BeautifulSoup(response.content, 'html.parser')
#         events = []
#
#         # Znajdź wszystkie linki do wydarzeń (dostosuj selektory do struktury strony)
#         event_links = soup.find_all('a', href=re.compile(r'/wydarzenia/'))
#
#         for link in event_links[:20]:  # Ograniczenie do 20 pierwszych wydarzeń
#             try:
#                 event_url = link.get('href')
#                 if not event_url.startswith('http'):
#                     event_url = 'https://echopoznan.com' + event_url
#
#                 # Pobierz szczegóły wydarzenia
#                 print(f"Pobieranie szczegółów: {event_url}")
#                 event_response = requests.get(event_url, headers=headers, timeout=15)
#                 event_soup = BeautifulSoup(event_response.content, 'html.parser')
#
#                 # Ekstraktuj dane wydarzenia (dostosuj selektory)
#                 title = event_soup.find('h1')
#                 title = title.get_text(strip=True) if title else "Brak tytułu"
#
#                 # Szukaj daty
#                 date_element = event_soup.find(['time', 'span'], class_=re.compile(r'date|time'))
#                 event_date = None
#                 if date_element:
#                     date_text = date_element.get_text(strip=True)
#                     event_date = parse_event_date(date_text)
#
#                 # Szukaj lokalizacji/adresu
#                 location = extract_location_from_event(event_soup)
#
#                 # Sprawdź czy to wystawa
#                 is_exhibition = any(keyword in title.lower() for keyword in [
#                     'wystawa', 'exhibition', 'galeria', 'wernisaż', 'prezentacja', 'ekspozycja'
#                 ])
#
#                 if is_exhibition and location:
#                     events.append({
#                         'title': title,
#                         'url': event_url,
#                         'date': event_date,
#                         'location': location,
#                         'type': 'exhibition'
#                     })
#
#                 time.sleep(1)  # Opóźnienie między requestami
#
#             except Exception as e:
#                 print(f"Błąd przy pobieraniu wydarzenia {event_url}: {e}")
#                 continue
#
#         print(f"Znaleziono {len(events)} wystaw")
#         return events
#
#     except Exception as e:
#         print(f"Błąd przy pobieraniu wydarzeń: {e}")
#         return []
#
#
# def parse_event_date(date_text):
#     """Parsuje datę wydarzenia z tekstu"""
#     try:
#         # Różne formaty dat do wypróbowania
#         formats = [
#             '%d.%m.%Y',
#             '%d/%m/%Y',
#             '%Y-%m-%d',
#             '%d-%m-%Y'
#         ]
#
#         # Wyczyść tekst z daty
#         date_clean = re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{4}', date_text)
#         if date_clean:
#             date_str = date_clean.group()
#             for fmt in formats:
#                 try:
#                     return datetime.strptime(date_str, fmt).date()
#                 except ValueError:
#                     continue
#     except Exception:
#         pass
#
#     return None
#
#
# def extract_location_from_event(soup):
#     """Ekstraktuje lokalizację z opisu wydarzenia"""
#     try:
#         # Szukaj w różnych miejscach
#         location_selectors = [
#             'address',
#             '[class*="location"]',
#             '[class*="venue"]',
#             '[class*="place"]',
#             'p:contains("ul.")',
#             'p:contains("Poznań")',
#         ]
#
#         for selector in location_selectors:
#             element = soup.select_one(selector)
#             if element:
#                 text = element.get_text(strip=True)
#                 if 'poznań' in text.lower() or 'ul.' in text.lower():
#                     return text
#
#         # Szukaj w całym tekście
#         all_text = soup.get_text()
#         address_patterns = [
#             r'ul\.\s*[A-ZĆŁŚŻŹ][a-ząćęłńóśźż\s]+\d+[a-z]?',
#             r'[A-ZĆŁŚŻŹ][a-ząćęłńóśźż\s]+,\s*Poznań',
#         ]
#
#         for pattern in address_patterns:
#             match = re.search(pattern, all_text, re.IGNORECASE)
#             if match:
#                 return match.group().strip()
#
#     except Exception as e:
#         print(f"Błąd przy ekstraktowaniu lokalizacji: {e}")
#
#     return None
#
#
# def match_events_to_galleries(events, galleries_df):
#     """Dopasowuje wydarzenia do galerii na mapie"""
#     matched_events = []
#
#     geolocator = Nominatim(user_agent="events_matcher_v1.0")
#
#     for event in events:
#         try:
#             # Geokoduj lokalizację wydarzenia
#             location = geolocator.geocode(event['location'] + ", Poznań", timeout=10)
#             time.sleep(1)
#
#             if location:
#                 event_coords = (location.latitude, location.longitude)
#
#                 # Znajdź najbliższą galerię
#                 min_distance = float('inf')
#                 matched_gallery = None
#
#                 for idx, gallery in galleries_df.iterrows():
#                     if pd.notnull(gallery['latitude']) and pd.notnull(gallery['longitude']):
#                         gallery_coords = (gallery['latitude'], gallery['longitude'])
#                         distance = geodesic(event_coords, gallery_coords).meters
#
#                         # Jeśli dystans < 200m, uznaj za match
#                         if distance < 200 and distance < min_distance:
#                             min_distance = distance
#                             matched_gallery = idx
#
#                 if matched_gallery is not None:
#                     matched_events.append({
#                         'event': event,
#                         'gallery_index': matched_gallery,
#                         'distance': min_distance
#                     })
#                     print(f"Dopasowano: {event['title']} -> {galleries_df.iloc[matched_gallery]['name']}")
#
#         except Exception as e:
#             print(f"Błąd przy dopasowywaniu wydarzenia {event['title']}: {e}")
#             continue
#
#     return matched_events
#
#
# def filter_events_by_timeframe(events, timeframe):
#     """Filtruje wydarzenia według wybranego okresu"""
#     today = datetime.now().date()
#
#     if timeframe == 'today':
#         target_date = today
#         return [e for e in events if e['event']['date'] == target_date]
#     elif timeframe == 'week':
#         week_start = today
#         week_end = today + timedelta(days=7)
#         return [e for e in events if e['event']['date'] and week_start <= e['event']['date'] <= week_end]
#     elif timeframe == 'month':
#         month_start = today
#         month_end = today + timedelta(days=30)
#         return [e for e in events if e['event']['date'] and month_start <= e['event']['date'] <= month_end]
#
#     return events
#
#
# def geocode_addresses(df):
#     # [Pozostała część funkcji bez zmian - skopiuj z oryginalnego kodu]
#     geolocator = Nominatim(user_agent="galerie_map_v1.0")
#     latitudes = []
#     longitudes = []
#
#     for idx, row in df.iterrows():
#         address = clean_address(row['address'])
#
#         if not address:
#             print(f"Wiersz {idx}: Pusty adres")
#             latitudes.append(None)
#             longitudes.append(None)
#             continue
#
#         # Lista wariantów adresu do wypróbowania
#         address_variants = []
#
#         # Wariant 1: Oryginalny adres + Polska (jeśli nie ma)
#         if "Polska" not in address.lower() and "Poland" not in address.lower():
#             address_variants.append(address + ", Polska")
#         else:
#             address_variants.append(address)
#
#         # Wariant 2: Bez słowa "Polska" jeśli już jest
#         if "Polska" in address.lower():
#             clean_addr = re.sub(r',?\s*Polska\s*,?', '', address, flags=re.IGNORECASE).strip()
#             if clean_addr:
#                 address_variants.append(clean_addr + ", Poland")
#
#         # Wariant 3: Tylko miasto jeśli adres zawiera więcej informacji
#         parts = address.split(',')
#         if len(parts) > 1:
#             # Spróbuj z ostatnią częścią (prawdopodobnie miasto)
#             city_part = parts[-1].strip()
#             if "Polska" not in city_part.lower():
#                 address_variants.append(city_part + ", Polska")
#
#         print(f"Wiersz {idx}: Geokodowanie adresu: {address}")
#         location = None
#
#         # Próbuj każdy wariant adresu
#         for variant in address_variants:
#             try:
#                 print(f"  Próbuję wariant: {variant}")
#                 time.sleep(1.5)  # Zwiększone opóźnienie dla stabilności
#                 location = geolocator.geocode(variant, timeout=15, exactly_one=True)
#
#                 if location:
#                     # Sprawdź czy lokalizacja jest w Polsce (przybliżone granice)
#                     lat, lon = location.latitude, location.longitude
#                     if 49.0 <= lat <= 54.9 and 14.1 <= lon <= 24.2:
#                         print(f"  ✓ Znaleziono w Polsce: {lat:.4f}, {lon:.4f}")
#                         break
#                     else:
#                         print(f"  ⚠ Znaleziono poza Polską: {lat:.4f}, {lon:.4f} - szukam dalej")
#                         location = None
#                 else:
#                     print(f"  ✗ Nie znaleziono dla: {variant}")
#
#             except Exception as e:
#                 print(f"  ✗ Błąd dla {variant}: {e}")
#                 continue
#
#         if location:
#             latitudes.append(location.latitude)
#             longitudes.append(location.longitude)
#             print(f"  → Końcowy rezultat: {location.latitude:.4f}, {location.longitude:.4f}")
#         else:
#             print(f"  → Nie udało się znaleźć lokalizacji dla żadnego wariantu")
#             latitudes.append(None)
#             longitudes.append(None)
#
#     df['latitude'] = latitudes
#     df['longitude'] = longitudes
#     return df
#
#
# def fix_csv_structure(df):
#     # [Pozostała część funkcji bez zmian - skopiuj z oryginalnego kodu]
#     """Naprawia błędną strukturę CSV gdzie dane są przesunięte"""
#     print("Naprawiam strukturę CSV...")
#     print(f"Oryginalne kolumny: {list(df.columns)}")
#
#     # Sprawdź pierwszych kilka wierszy
#     print("Pierwsze 3 wiersze:")
#     for i in range(min(3, len(df))):
#         print(f"  {df.iloc[i].to_dict()}")
#
#     # Jeśli latitude zawiera adresy (stringi), znaczy że kolumny są przesunięte
#     if df['latitude'].dtype == 'object' and any(',' in str(val) for val in df['latitude'].head()):
#         print("Wykryto przesunięcie kolumn - naprawiam...")
#
#         # Stwórz nową, poprawną strukturę
#         df_fixed = pd.DataFrame()
#
#         df_fixed['name'] = df['name']
#         df_fixed['address'] = df['latitude']  # Prawdziwe adresy są w kolumnie latitude
#
#         # Wyczyść współrzędne - usuń stare błędne wartości
#         df_fixed['latitude'] = None
#         df_fixed['longitude'] = None
#
#         print("Struktura naprawiona!")
#         return df_fixed
#
#     return df
#
#
# @app.route("/")
# def home():
#     # Pobierz parametr okresu z URL
#     timeframe = request.args.get('period', 'today')
#
#     source_file = "galerie.csv"
#
#     # Sprawdź czy plik istnieje
#     if not os.path.exists(source_file):
#         return f"Błąd: Nie znaleziono pliku {source_file}"
#
#     try:
#         # Wczytanie pliku z różnymi kodowaniami
#         encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1250']
#         df = None
#
#         for encoding in encodings:
#             try:
#                 df = pd.read_csv(source_file, encoding=encoding)
#                 print(f"Wczytano plik z kodowaniem: {encoding}")
#                 break
#             except UnicodeDecodeError:
#                 continue
#
#         if df is None:
#             return "Błąd: Nie udało się wczytać pliku CSV"
#
#         print(f"Wczytano {len(df)} wierszy")
#
#         # Napraw strukturę CSV jeśli jest potrzeba
#         df = fix_csv_structure(df)
#
#         # Sprawdź czy kolumna 'address' istnieje
#         if 'address' not in df.columns:
#             return f"Błąd: Brak kolumny 'address' w pliku. Dostępne kolumny: {list(df.columns)}"
#
#         # Sprawdzenie czy współrzędne istnieją i są prawidłowe
#         coords_invalid = (
#                 'latitude' not in df.columns or
#                 'longitude' not in df.columns or
#                 df['latitude'].isnull().all() or
#                 df['longitude'].isnull().all() or
#                 (df['latitude'].nunique() <= 1 and df['longitude'].nunique() <= 1)
#         )
#
#         if coords_invalid:
#             print("Współrzędne są nieprawidłowe lub puste, wykonuję geokodowanie...")
#             df = geocode_addresses(df)
#
#             # Zapisz z kopią zapasową
#             backup_file = source_file.replace('.csv', '_backup.csv')
#             if os.path.exists(source_file):
#                 import shutil
#                 shutil.copy2(source_file, backup_file)
#                 print(f"Utworzono kopię zapasową: {backup_file}")
#
#             df.to_csv(source_file, index=False, encoding="utf-8-sig")
#             print("Geokodowanie zakończone i zapisane.")
#
#         # Pobierz wydarzenia z Echo Poznań
#         print("Pobieranie wydarzeń z Echo Poznań...")
#         events = scrape_echo_poznan_events()
#
#         # Dopasuj wydarzenia do galerii
#         matched_events = match_events_to_galleries(events, df)
#
#         # Filtruj według wybranego okresu
#         filtered_events = filter_events_by_timeframe(matched_events, timeframe)
#
#         # Tworzenie mapy
#         valid_coords = df[(df['latitude'].notnull()) & (df['longitude'].notnull())]
#
#         if len(valid_coords) > 0:
#             center_lat = valid_coords['latitude'].mean()
#             center_lon = valid_coords['longitude'].mean()
#             start_coords = [center_lat, center_lon]
#
#             lat_range = valid_coords['latitude'].max() - valid_coords['latitude'].min()
#             lon_range = valid_coords['longitude'].max() - valid_coords['longitude'].min()
#             zoom = 10 if max(lat_range, lon_range) > 1 else 13
#         else:
#             start_coords = [52.4069, 16.9299]  # Poznań domyślnie
#             zoom = 6
#
#         m = folium.Map(location=start_coords, zoom_start=zoom)
#
#         # Zbiór indeksów galerii z wydarzeniami
#         galleries_with_events = {event['gallery_index'] for event in filtered_events}
#
#         # Dodaj markery
#         successful_markers = 0
#         for idx, row in df.iterrows():
#             if pd.notnull(row.get('latitude')) and pd.notnull(row.get('longitude')):
#                 # Sprawdź czy galeria ma wydarzenia
#                 has_events = idx in galleries_with_events
#
#                 # Przygotuj popup z informacjami o wydarzeniach
#                 popup_text = f"<b>{row.get('name', 'Brak nazwy')}</b><br>{row.get('address', '')}"
#
#                 if has_events:
#                     gallery_events = [e for e in filtered_events if e['gallery_index'] == idx]
#                     popup_text += "<br><br><b>Aktualne wydarzenia:</b>"
#                     for event in gallery_events:
#                         event_date = event['event']['date'].strftime('%d.%m.%Y') if event['event'][
#                             'date'] else 'Brak daty'
#                         popup_text += f"<br>• {event['event']['title']} ({event_date})"
#
#                 # Wybierz kolor markera
#                 marker_color = 'blue' if has_events else 'red'
#                 icon_name = 'star' if has_events else 'info-sign'
#
#                 folium.Marker(
#                     location=[row['latitude'], row['longitude']],
#                     popup=folium.Popup(popup_text, max_width=400),
#                     tooltip=row.get('name', 'Punkt'),
#                     icon=folium.Icon(color=marker_color, icon=icon_name)
#                 ).add_to(m)
#                 successful_markers += 1
#
#         print(f"Dodano {successful_markers} markerów do mapy")
#         print(f"Znaleziono {len(filtered_events)} wydarzeń dla okresu: {timeframe}")
#
#         # Stwórz katalog static jeśli nie istnieje
#         os.makedirs('static', exist_ok=True)
#         m.save("static/galerie_w_polsce_interaktywna.html")
#
#         return render_template("index.html", events=filtered_events)
#
#     except Exception as e:
#         print(f"Szczegóły błędu: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return f"Błąd aplikacji: {str(e)}"
#
# if __name__ == "__main__":
#     app.run(debug=True)

from flask import Flask, render_template, request, jsonify
import folium
import pandas as pd
from geopy.geocoders import Nominatim
import time
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from geopy.distance import geodesic

app = Flask(__name__)

def clean_address(address):
    """Czyści i normalizuje adres przed geokodowaniem"""
    if pd.isna(address):
        return None

    # Konwertuj na string jeśli nie jest
    address = str(address).strip()

    # Usuń dodatkowe spacje
    address = re.sub(r'\s+', ' ', address)

    # Usuń zbędne znaki interpunkcyjne na końcu
    address = address.rstrip('.,;')

    return address


def scrape_echo_poznan_events():
    """Pobiera wydarzenia ze strony Echo Poznań"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # URL do listy wydarzeń
        events_url = "https://echopoznan.com/wydarzenia/"

        print(f"Pobieranie wydarzeń z: {events_url}")
        response = requests.get(events_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        events = []

        # Znajdź wszystkie linki do wydarzeń (dostosuj selektory do struktury strony)
        event_links = soup.find_all('a', href=re.compile(r'/wydarzenia/'))

        for link in event_links[:20]:  # Ograniczenie do 20 pierwszych wydarzeń
            try:
                event_url = link.get('href')
                if not event_url.startswith('http'):
                    event_url = 'https://echopoznan.com' + event_url

                # Pobierz szczegóły wydarzenia
                print(f"Pobieranie szczegółów: {event_url}")
                event_response = requests.get(event_url, headers=headers, timeout=15)
                event_soup = BeautifulSoup(event_response.content, 'html.parser')

                # Ekstraktuj dane wydarzenia (dostosuj selektory)
                title = event_soup.find('h1')
                title = title.get_text(strip=True) if title else "Brak tytułu"

                # Szukaj daty
                date_element = event_soup.find(['time', 'span'], class_=re.compile(r'date|time'))
                event_date = None
                if date_element:
                    date_text = date_element.get_text(strip=True)
                    event_date = parse_event_date(date_text)

                # Szukaj lokalizacji/adresu
                location = extract_location_from_event(event_soup)

                # Sprawdź czy to wystawa
                is_exhibition = any(keyword in title.lower() for keyword in [
                    'wystawa', 'exhibition', 'galeria', 'wernisaż', 'prezentacja', 'ekspozycja'
                ])

                if is_exhibition and location:
                    events.append({
                        'title': title,
                        'url': event_url,
                        'date': event_date,
                        'location': location,
                        'type': 'exhibition'
                    })

                time.sleep(1)  # Opóźnienie między requestami

            except Exception as e:
                print(f"Błąd przy pobieraniu wydarzenia {event_url}: {e}")
                continue

        print(f"Znaleziono {len(events)} wystaw")
        return events

    except Exception as e:
        print(f"Błąd przy pobieraniu wydarzeń: {e}")
        return []


def parse_event_date(date_text):
    """Parsuje datę wydarzenia z tekstu"""
    try:
        # Różne formaty dat do wypróbowania
        formats = [
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y'
        ]

        # Wyczyść tekst z daty
        date_clean = re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{4}', date_text)
        if date_clean:
            date_str = date_clean.group()
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
    except Exception:
        pass

    return None


def extract_location_from_event(soup):
    """Ekstraktuje lokalizację z opisu wydarzenia"""
    try:
        # Szukaj w różnych miejscach
        location_selectors = [
            'address',
            '[class*="location"]',
            '[class*="venue"]',
            '[class*="place"]',
            'p:contains("ul.")',
            'p:contains("Poznań")',
        ]

        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if 'poznań' in text.lower() or 'ul.' in text.lower():
                    return text

        # Szukaj w całym tekście
        all_text = soup.get_text()
        address_patterns = [
            r'ul\.\s*[A-ZĆŁŚŻŹ][a-ząćęłńóśźż\s]+\d+[a-z]?',
            r'[A-ZĆŁŚŻŹ][a-ząćęłńóśźż\s]+,\s*Poznań',
        ]

        for pattern in address_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                return match.group().strip()

    except Exception as e:
        print(f"Błąd przy ekstraktowaniu lokalizacji: {e}")

    return None


def match_events_to_galleries(events, galleries_df):
    """Dopasowuje wydarzenia do galerii na mapie"""
    matched_events = []

    geolocator = Nominatim(user_agent="events_matcher_v1.0")

    for event in events:
        try:
            # Geokoduj lokalizację wydarzenia
            location = geolocator.geocode(event['location'] + ", Poznań", timeout=10)
            time.sleep(1)

            if location:
                event_coords = (location.latitude, location.longitude)

                # Znajdź najbliższą galerię
                min_distance = float('inf')
                matched_gallery = None

                for idx, gallery in galleries_df.iterrows():
                    if pd.notnull(gallery['latitude']) and pd.notnull(gallery['longitude']):
                        gallery_coords = (gallery['latitude'], gallery['longitude'])
                        distance = geodesic(event_coords, gallery_coords).meters

                        # Jeśli dystans < 200m, uznaj za match
                        if distance < 200 and distance < min_distance:
                            min_distance = distance
                            matched_gallery = idx

                if matched_gallery is not None:
                    matched_events.append({
                        'event': event,
                        'gallery_index': matched_gallery,
                        'distance': min_distance
                    })
                    print(f"Dopasowano: {event['title']} -> {galleries_df.iloc[matched_gallery]['name']}")

        except Exception as e:
            print(f"Błąd przy dopasowywaniu wydarzenia {event['title']}: {e}")
            continue

    return matched_events


def filter_events_by_timeframe(events, timeframe):
    """Filtruje wydarzenia według wybranego okresu"""
    today = datetime.now().date()

    if timeframe == 'today':
        target_date = today
        return [e for e in events if e['event']['date'] == target_date]
    elif timeframe == 'week':
        week_start = today
        week_end = today + timedelta(days=7)
        return [e for e in events if e['event']['date'] and week_start <= e['event']['date'] <= week_end]
    elif timeframe == 'month':
        month_start = today
        month_end = today + timedelta(days=30)
        return [e for e in events if e['event']['date'] and month_start <= e['event']['date'] <= month_end]

    return events


def geocode_addresses(df):
    # [Pozostała część funkcji bez zmian - skopiuj z oryginalnego kodu]
    geolocator = Nominatim(user_agent="galerie_map_v1.0")
    latitudes = []
    longitudes = []

    for idx, row in df.iterrows():
        address = clean_address(row['Adres'])

        if not address:
            print(f"Wiersz {idx}: Pusty adres")
            latitudes.append(None)
            longitudes.append(None)
            continue

        # Lista wariantów adresu do wypróbowania
        address_variants = []

        # Wariant 1: Oryginalny adres + Polska (jeśli nie ma)
        if "Polska" not in address.lower() and "Poland" not in address.lower():
            address_variants.append(address + ", Polska")
        else:
            address_variants.append(address)

        # Wariant 2: Bez słowa "Polska" jeśli już jest
        if "Polska" in address.lower():
            clean_addr = re.sub(r',?\s*Polska\s*,?', '', address, flags=re.IGNORECASE).strip()
            if clean_addr:
                address_variants.append(clean_addr + ", Poland")

        # Wariant 3: Tylko miasto jeśli adres zawiera więcej informacji
        parts = address.split(',')
        if len(parts) > 1:
            # Spróbuj z ostatnią częścią (prawdopodobnie miasto)
            city_part = parts[-1].strip()
            if "Polska" not in city_part.lower():
                address_variants.append(city_part + ", Polska")

        print(f"Wiersz {idx}: Geokodowanie adresu: {address}")
        location = None

        # Próbuj każdy wariant adresu
        for variant in address_variants:
            try:
                print(f"  Próbuję wariant: {variant}")
                time.sleep(1.5)  # Zwiększone opóźnienie dla stabilności
                location = geolocator.geocode(variant, timeout=15, exactly_one=True)

                if location:
                    # Sprawdź czy lokalizacja jest w Polsce (przybliżone granice)
                    lat, lon = location.latitude, location.longitude
                    if 49.0 <= lat <= 54.9 and 14.1 <= lon <= 24.2:
                        print(f"  ✓ Znaleziono w Polsce: {lat:.4f}, {lon:.4f}")
                        break
                    else:
                        print(f"  ⚠ Znaleziono poza Polską: {lat:.4f}, {lon:.4f} - szukam dalej")
                        location = None
                else:
                    print(f"  ✗ Nie znaleziono dla: {variant}")

            except Exception as e:
                print(f"  ✗ Błąd dla {variant}: {e}")
                continue

        if location:
            latitudes.append(location.latitude)
            longitudes.append(location.longitude)
            print(f"  → Końcowy rezultat: {location.latitude:.4f}, {location.longitude:.4f}")
        else:
            print(f"  → Nie udało się znaleźć lokalizacji dla żadnego wariantu")
            latitudes.append(None)
            longitudes.append(None)

    df['latitude'] = latitudes
    df['longitude'] = longitudes
    return df


def fix_csv_structure(df):
    # [Pozostała część funkcji bez zmian - skopiuj z oryginalnego kodu]
    """Naprawia błędną strukturę CSV gdzie dane są przesunięte"""
    print("Naprawiam strukturę CSV...")
    print(f"Oryginalne kolumny: {list(df.columns)}")

    # Sprawdź pierwszych kilka wierszy
    print("Pierwsze 3 wiersze:")
    for i in range(min(3, len(df))):
        print(f"  {df.iloc[i].to_dict()}")

    # Jeśli latitude zawiera adresy (stringi), znaczy że kolumny są przesunięte
    if df['latitude'].dtype == 'object' and any(',' in str(val) for val in df['latitude'].head()):
        print("Wykryto przesunięcie kolumn - naprawiam...")

        # Stwórz nową, poprawną strukturę
        df_fixed = pd.DataFrame()

        df_fixed['name'] = df['name']
        df_fixed['Adres'] = df['latitude']  # Prawdziwe adresy są w kolumnie latitude

        # Wyczyść współrzędne - usuń stare błędne wartości
        df_fixed['latitude'] = None
        df_fixed['longitude'] = None

        print("Struktura naprawiona!")
        return

    return df


def create_popup_html(row):
    """Tworzy HTML dla popup z markerami social media"""
    # Sprawdź czy kolumna to 'Nazwa' czy 'name'
    name = row.get('Nazwa') or row.get('name', 'Brak nazwy')
    address = row.get('Adres') or row.get('address', 'Brak adresu')

    html = f"""
   <div style="width: 250px;">
       <h3 style="margin: 0 0 10px 0; color: #333;">{name}</h3>
       <p><strong>📍</strong> {address}</p>
   """

    # Godziny otwarcia
    if pd.notna(row.get('Godziny')):
        html += f"<p><strong>🕐</strong> {row['Godziny']}</p>"

    # Telefon
    if pd.notna(row.get('Telefon')):
        html += f"<p><strong>📞</strong> {row['Telefon']}</p>"

    # Email
    if pd.notna(row.get('Email')):
        html += f"<p><strong>✉️</strong> {row['Email']}</p>"

    # Strona internetowa
    if pd.notna(row.get('Strona')):
        html += f'<p><strong>🌐</strong> <a href="{row["Strona"]}" target="_blank">{row["Strona"]}</a></p>'

    # Logo (mniejsze zdjęcie)
    if pd.notna(row.get('Logo')):
        html += f'<img src="{row["Logo"]}" style="width: 80px; height: auto; margin: 5px 0; border-radius: 5px;"><br>'

    # Zdjęcie główne (większe)
    if pd.notna(row.get('Zdjęcie')):
        html += f'<img src="{row["Zdjęcie"]}" style="width: 200px; height: auto; margin: 5px 0; border-radius: 5px;"><br>'

    # Social media z kolorowymi markerami
    social_links = []
    if pd.notna(row.get('Facebook')):
        social_links.append(
            f'<a href="{row["Facebook"]}" target="_blank" style="color: #4267B2; text-decoration: none;"><i class="fa-brands fa-facebook fa-beat"></i></a>')

    if pd.notna(row.get('Instagram')):
        social_links.append(
            f'<a href="{row["Instagram"]}" target="_blank" style="color:#C13584;width: 200px; height: 200px; text-decoration: none;"><i class="fa-brands fa-instagram fa-beat"></i></a>')

    if pd.notna(row.get('YouTube')):
        social_links.append(
            f'<a href="{row["YouTube"]}" target="_blank" style="color: #FF0000; text-decoration: none;"><i class="fa-brands fa-youtube fa-beat"></i></a>')

    if social_links:
        html += "<p><strong>🔗 Social Media:</strong><br>" + " | ".join(social_links) + "</p>"

    html += "</div>"
    return html


@app.route("/")
def home():
    # Pobierz parametr okresu z URL
    timeframe = request.args.get('period', 'today')

    source_file = "galerie.csv"

    # Sprawdź czy plik istnieje
    if not os.path.exists(source_file):
        return f"Błąd: Nie znaleziono pliku {source_file}"

    try:
        # Wczytanie pliku z różnymi kodowaniami
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1250']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(source_file, encoding=encoding)
                print(f"Wczytano plik z kodowaniem: {encoding}")
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            return "Błąd: Nie udało się wczytać pliku CSV"

        print(f"Wczytano {len(df)} wierszy")

        # Napraw strukturę CSV jeśli jest potrzeba
        df = fix_csv_structure(df)

        # Sprawdź czy kolumna 'address' istnieje
        if 'Adres' not in df.columns:
            return f"Błąd: Brak kolumny 'Adres' w pliku. Dostępne kolumny: {list(df.columns)}"

        # Sprawdzenie czy współrzędne istnieją i są prawidłowe
        coords_invalid = (
                'latitude' not in df.columns or
                'longitude' not in df.columns or
                df['latitude'].isnull().all() or
                df['longitude'].isnull().all() or
                (df['latitude'].nunique() <= 1 and df['longitude'].nunique() <= 1)
        )

        if coords_invalid:
            print("Współrzędne są nieprawidłowe lub puste, wykonuję geokodowanie...")
            df = geocode_addresses(df)

            # Zapisz z kopią zapasową
            backup_file = source_file.replace('.csv', '_backup.csv')
            if os.path.exists(source_file):
                import shutil
                shutil.copy2(source_file, backup_file)
                print(f"Utworzono kopię zapasową: {backup_file}")

            df.to_csv(source_file, index=False, encoding="utf-8-sig")
            print("Geokodowanie zakończone i zapisane.")

        # Pobierz wydarzenia z Echo Poznań
        print("Pobieranie wydarzeń z Echo Poznań...")
        events = scrape_echo_poznan_events()

        # Dopasuj wydarzenia do galerii
        matched_events = match_events_to_galleries(events, df)

        # Filtruj według wybranego okresu
        filtered_events = filter_events_by_timeframe(matched_events, timeframe)

        # Tworzenie mapy
        valid_coords = df[(df['latitude'].notnull()) & (df['longitude'].notnull())]

        if len(valid_coords) > 0:
            center_lat = valid_coords['latitude'].mean()
            center_lon = valid_coords['longitude'].mean()
            start_coords = [center_lat, center_lon]

            lat_range = valid_coords['latitude'].max() - valid_coords['latitude'].min()
            lon_range = valid_coords['longitude'].max() - valid_coords['longitude'].min()
            zoom = 10 if max(lat_range, lon_range) > 1 else 13
        else:
            start_coords = [52.4069, 16.9299]  # Poznań domyślnie
            zoom = 6

        m = folium.Map(location=start_coords, zoom_start=zoom)

        # Zbiór indeksów galerii z wydarzeniami
        galleries_with_events = {event['gallery_index'] for event in filtered_events}

        # Dodaj markery
        # Dodaj markery
        successful_markers = 0
        for idx, row in df.iterrows():
            if pd.notnull(row.get('latitude')) and pd.notnull(row.get('longitude')):
                # Sprawdź czy galeria ma wydarzenia
                has_events = idx in galleries_with_events

                # Użyj funkcji create_popup_html() dla pełnych danych galerii
                popup_html = create_popup_html(row)

                # Jeśli galeria ma wydarzenia, dodaj je do popup
                if has_events:
                    gallery_events = [e for e in filtered_events if e['gallery_index'] == idx]
                    events_html = "<br><br><div style='border-top: 1px solid #ccc; padding-top: 10px;'>"
                    events_html += "<h4 style='margin: 5px 0; color: #0066cc;'>🎨 Aktualne wydarzenia:</h4>"

                    for event in gallery_events:
                        event_date = event['event']['date'].strftime('%d.%m.%Y') if event['event'][
                            'date'] else 'Brak daty'
                        events_html += f"""
                        <div style='margin: 5px 0; padding: 5px; background-color: #f0f8ff; border-left: 3px solid #0066cc;'>
                            <strong>{event['event']['title']}</strong><br>
                            <small>📅 {event_date}</small><br>
                            <small>📍 {event['event']['location']}</small>
                        </div>
                        """
                    events_html += "</div>"

                    # Dodaj wydarzenia do popup (usuń ostatnie </div> i dodaj wydarzenia)
                    popup_html = popup_html.replace("</div>", events_html + "</div>")

                # Wybierz kolor markera
                marker_color = 'blue' if has_events else 'red'
                icon_name = 'star' if has_events else 'camera'

                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=400),
                    tooltip=row.get('Nazwa', 'Punkt'),
                    icon=folium.Icon(color=marker_color, icon=icon_name)
                ).add_to(m)
                successful_markers += 1

        print(f"Dodano {successful_markers} markerów do mapy")
        print(f"Znaleziono {len(filtered_events)} wydarzeń dla okresu: {timeframe}")

        # Stwórz katalog static jeśli nie istnieje
        os.makedirs('static', exist_ok=True)
        m.save("static/galerie_w_polsce_interaktywna.html")

        return render_template("index.html", events=filtered_events)

    except Exception as e:
        print(f"Szczegóły błędu: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Błąd aplikacji: {str(e)}"


def create_map(df):
    """Tworzy mapę z markerami galerii"""
    # Centrum na Poznaniu
    center_lat = 52.4069
    center_lon = 16.9299

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # Dodaj markery dla każdej galerii
    for idx, row in df.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            popup_html = create_popup_html(row)

            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=row['Nazwa'],
                icon=folium.Icon(color='red', icon='camera')
            ).add_to(m)

    # Zapisz mapę
    m.save('mapa_galerii.html')
    print("Mapa zapisana jako 'mapa_galerii.html'")
    return m

if __name__ == "__main__":
    app.run(debug=True)