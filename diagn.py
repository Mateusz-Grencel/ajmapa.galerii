#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Poprawiony skrypt do pobierania danych o wystawach ze strony Echo Poznań
Naprawia problemy z duplikatami i brakiem danych
"""

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import re
import hashlib


class EchoPoznanImprovedScraper:
    def __init__(self, headless=True):
        self.base_url = "https://echopoznan.com"
        self.events_url = "https://echopoznan.com/wydarzenia/"
        self.headless = headless
        self.driver = None
        self.seen_events = set()  # Zbiór do śledzenia duplikatów
        self.setup_driver()

    def setup_driver(self):
        """Konfiguruje driver Selenium"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            print("webdriver-manager nie zainstalowany, próbuję lokalny ChromeDriver...")
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                print(f"Nie można uruchomić ChromeDriver: {e}")
                print("Zainstaluj: pip install webdriver-manager")
                raise
        except Exception as e:
            print(f"Błąd konfiguracji driver: {e}")
            raise

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def create_event_hash(self, title, date, location):
        """Tworzy hash wydarzenia do wykrywania duplikatów"""
        # Normalizuj dane do porównania
        title_norm = re.sub(r'\s+', ' ', str(title).lower().strip())
        date_norm = re.sub(r'\s+', ' ', str(date).lower().strip())
        location_norm = re.sub(r'\s+', ' ', str(location).lower().strip())

        # Stwórz unikalny identyfikator
        combined = f"{title_norm}|{date_norm}|{location_norm}"
        return hashlib.md5(combined.encode()).hexdigest()

    def wait_for_page_load(self, timeout=20):
        """Czeka aż strona się załaduje z lepszą detekcją"""
        try:
            # Podstawowe oczekiwanie na załadowanie DOM
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Czekaj na jQuery jeśli istnieje
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script(
                        "return typeof jQuery !== 'undefined' ? jQuery.active == 0 : true")
                )
            except:
                pass

            # Dodatkowe czekanie na możliwe AJAX
            time.sleep(2)

            # Sprawdź obecność wydarzeń - używaj bardziej specyficznych selektorów
            event_selectors = [
                'article[class*="post"]',
                '.event-item',
                '.entry',
                '[class*="card"]',
                '.post-content'
            ]

            for selector in event_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 0:
                        print(f"✅ Znaleziono {len(elements)} elementów z selektorem: {selector}")
                        return True
                except:
                    continue

            print("⚠️ Nie znaleziono wydarzeń ze standardowymi selektorami")
            return True

        except TimeoutException:
            print("⚠️ Timeout podczas ładowania strony")
            return False

    def get_page_structure_info(self):
        """Analizuje strukturę strony aby znaleźć najlepsze selektory"""
        print("🔍 Analizuję strukturę strony...")

        # Szukaj kontenerów wydarzeń
        potential_containers = [
            '#main', '#content', '.main-content', '.content',
            '.events-container', '.posts-container',
            '[class*="events"]', '[class*="posts"]'
        ]

        for container_selector in potential_containers:
            try:
                container = self.driver.find_element(By.CSS_SELECTOR, container_selector)
                if container:
                    print(f"📦 Znaleziono kontener: {container_selector}")

                    # Sprawdź elementy wewnątrz kontenera
                    child_elements = container.find_elements(By.CSS_SELECTOR, "*")
                    classes = set()
                    for elem in child_elements[:20]:  # Sprawdź pierwsze 20 elementów
                        elem_classes = elem.get_attribute('class')
                        if elem_classes:
                            classes.update(elem_classes.split())

                    print(f"🏷️ Częste klasy: {sorted(list(classes))[:10]}")
                    break
            except:
                continue

    def scroll_and_load_events(self, max_scrolls=8, scroll_pause=4):
        """Ulepszone przewijanie z lepszą detekcją nowych treści"""
        print(f"📜 Rozpoczynam inteligentne przewijanie (max {max_scrolls} razy)...")

        # Pobierz informacje o strukturze strony
        self.get_page_structure_info()

        previous_height = self.driver.execute_script("return document.body.scrollHeight")
        no_change_count = 0

        for scroll_num in range(max_scrolls):
            print(f"🔄 Scroll {scroll_num + 1}/{max_scrolls}")

            # Przewiń stopniowo zamiast od razu na dół
            current_position = self.driver.execute_script("return window.pageYOffset")
            scroll_step = 800  # Przewijaj po 800px

            for step in range(3):  # 3 kroki przewijania
                self.driver.execute_script(f"window.scrollTo(0, {current_position + scroll_step * (step + 1)});")
                time.sleep(1)

            # Przewiń na sam dół
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Czekaj na załadowanie
            time.sleep(scroll_pause)

            # Sprawdź czy wysokość strony się zmieniła
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height > previous_height:
                print(f"  ✅ Strona rozrosła się z {previous_height}px do {new_height}px")
                previous_height = new_height
                no_change_count = 0

                # Sprawdź czy są loadery
                self.wait_for_loaders()

            else:
                no_change_count += 1
                print(f"  ⏸️ Brak zmian wysokości ({no_change_count}/3)")

                if no_change_count >= 3:
                    print("  🏁 Prawdopodobnie załadowano wszystkie treści")
                    break

        final_count = self.count_events_on_page()
        print(f"🎯 Ukończono przewijanie. Wykryto około {final_count} elementów")
        return final_count

    def wait_for_loaders(self):
        """Czeka na zniknięcie loaderów/spinnerów"""
        loader_selectors = [
            '.loading', '.spinner', '.loader', '[class*="load"]',
            '.ajax-loader', '.preloader', '[data-loading]'
        ]

        for selector in loader_selectors:
            try:
                loader = self.driver.find_element(By.CSS_SELECTOR, selector)
                if loader.is_displayed():
                    print(f"  ⏳ Czekam na loader: {selector}")
                    WebDriverWait(self.driver, 10).until(
                        EC.invisibility_of_element(loader)
                    )
                    time.sleep(2)
                    break
            except (NoSuchElementException, TimeoutException):
                continue

    def count_events_on_page(self):
        """Poprawione liczenie wydarzeń z priorytetyzacją selektorów"""
        # Selektory uporządkowane według prawdopodobieństwa sukcesu
        prioritized_selectors = [
            'article[class*="post"]',  # Najczęstszy w WordPressie
            '.entry',  # Standardowy dla wpisów
            '.post-content',  # Treść posta
            '.event-item',  # Dedykowany dla wydarzeń
            'article',  # Ogólny artikel
            '.card',  # Karty
            '[class*="item"]'  # Elementy z 'item' w klasie
        ]

        for selector in prioritized_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 5:  # Musi być sensowna liczba
                    print(f"  📊 Używam selektora '{selector}': {len(elements)} elementów")
                    return len(elements)
            except:
                continue

        # Fallback - wszystkie artykuły i divy z tekstem
        all_elements = self.driver.find_elements(By.CSS_SELECTOR, "article, div")
        content_elements = []

        for elem in all_elements:
            try:
                text = elem.text.strip()
                if len(text) > 50 and len(text) < 2000:  # Rozsądna długość tekstu
                    content_elements.append(elem)
            except:
                continue

        return len(content_elements)

    def extract_all_events(self):
        """Ulepszona ekstrakcja z deduplikacją"""
        print("🔍 Rozpoczynam analizę strony...")

        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Zapisz debug
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("💾 Zapisano HTML do debug_page.html")

        # Znajdź najlepszy selektor
        best_selector, event_elements = self.find_best_selector(soup)

        if not event_elements:
            print("❌ Nie znaleziono wydarzeń")
            return []

        print(f"🎯 Używam selektora '{best_selector}' dla {len(event_elements)} elementów")

        events = []
        processed_count = 0
        duplicates_count = 0

        for i, element in enumerate(event_elements):
            try:
                event_data = self.parse_event_element(element, i + 1)

                if event_data and self.is_valid_event(event_data):
                    # Sprawdź duplikaty
                    event_hash = self.create_event_hash(
                        event_data['tytul'],
                        event_data['data'],
                        event_data['miejsce']
                    )

                    if event_hash not in self.seen_events:
                        self.seen_events.add(event_hash)
                        events.append(event_data)
                        processed_count += 1

                        if processed_count % 10 == 0:
                            print(f"  ✅ Przetworzono {processed_count} unikalnych wydarzeń...")
                    else:
                        duplicates_count += 1

            except Exception as e:
                print(f"  ❌ Błąd parsowania elementu {i + 1}: {e}")
                continue

        print(f"🎉 Zakończono: {len(events)} unikalnych wydarzeń")
        print(f"📊 Pominięto {duplicates_count} duplikatów")

        return events

    def find_best_selector(self, soup):
        """Znajduje najlepszy selektor dla wydarzeń"""
        selectors_to_test = [
            ('article[class*="post"]', 'Artykuły z post w klasie'),
            ('article.entry', 'Artykuły z klasą entry'),
            ('.entry', 'Elementy z klasą entry'),
            ('article', 'Wszystkie artykuły'),
            ('.post-content', 'Treści postów'),
            ('.event-item', 'Elementy wydarzeń'),
            ('.card', 'Karty'),
            ('[class*="item"]', 'Elementy z item w klasie')
        ]

        best_selector = None
        best_elements = []
        best_score = 0

        for selector, description in selectors_to_test:
            elements = soup.select(selector)

            if len(elements) == 0:
                continue

            # Ocena jakości selektora
            score = self.evaluate_selector_quality(elements)
            print(f"  📋 {description}: {len(elements)} elementów (jakość: {score})")

            if score > best_score and len(elements) > 3:
                best_score = score
                best_selector = selector
                best_elements = elements

        return best_selector, best_elements

    def evaluate_selector_quality(self, elements):
        """Ocenia jakość selektora na podstawie zawartości elementów"""
        if not elements:
            return 0

        score = 0
        sample_size = min(5, len(elements))

        for element in elements[:sample_size]:
            text = element.get_text().lower()
            text_length = len(text.strip())

            # Punkty za odpowiednią długość tekstu
            if 50 <= text_length <= 1000:
                score += 10
            elif text_length > 1000:
                score += 5

            # Punkty za słowa kluczowe
            keywords = ['wystawa', 'exhibition', 'galeria', 'muzeum', 'koncert', 'teatr', 'event']
            keyword_count = sum(1 for keyword in keywords if keyword in text)
            score += keyword_count * 3

            # Punkty za obecność dat
            if re.search(r'\d{1,2}[./\-]\d{1,2}[./\-]\d{4}', text):
                score += 5

            # Punkty za linki
            if element.find('a'):
                score += 2

        return score / sample_size if sample_size > 0 else 0

    def parse_event_element(self, element, index):
        """Ulepszone parsowanie elementu"""
        event_data = {
            'id': index,
            'tytul': '',
            'data': '',
            'miejsce': '',
            'opis': '',
            'link': '',
            'kategoria': '',
            'raw_text': element.get_text()[:200] + "..." if len(element.get_text()) > 200 else element.get_text()
        }

        # Wykorzystaj metody z oryginału ale z lepszą obsługą błędów
        try:
            event_data['tytul'] = self.extract_title(element)
        except Exception as e:
            print(f"    ⚠️ Błąd tytułu dla elementu {index}: {e}")
            event_data['tytul'] = "Bez tytułu"

        try:
            event_data['data'] = self.extract_date(element)
        except Exception as e:
            print(f"    ⚠️ Błąd daty dla elementu {index}: {e}")
            event_data['data'] = "Brak daty"

        try:
            event_data['miejsce'] = self.extract_location(element)
        except Exception as e:
            print(f"    ⚠️ Błąd miejsca dla elementu {index}: {e}")
            event_data['miejsce'] = "Brak miejsca"

        try:
            event_data['opis'] = self.extract_description(element)
        except Exception as e:
            print(f"    ⚠️ Błąd opisu dla elementu {index}: {e}")
            event_data['opis'] = "Brak opisu"

        try:
            event_data['link'] = self.extract_link(element)
        except Exception as e:
            print(f"    ⚠️ Błąd linku dla elementu {index}: {e}")
            event_data['link'] = ""

        try:
            event_data['kategoria'] = self.extract_category(element)
        except Exception as e:
            print(f"    ⚠️ Błąd kategorii dla elementu {index}: {e}")
            event_data['kategoria'] = "Wydarzenie"

        return event_data

    # Metody extract_* pozostają takie same jak w oryginale
    def extract_title(self, element):
        """Ekstraktuje tytuł wydarzenia"""
        # Strategia 1: Nagłówki
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
            title_elem = element.find(tag)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if len(title) > 3 and not title.isdigit():
                    return title

        # Strategia 2: Klasy z 'title'
        title_elem = element.find(class_=re.compile(r'title|name|heading', re.I))
        if title_elem:
            title = title_elem.get_text(strip=True)
            if len(title) > 3:
                return title

        # Strategia 3: Pierwszy link
        link_elem = element.find('a')
        if link_elem:
            title = link_elem.get_text(strip=True)
            if len(title) > 3 and not title.isdigit():
                return title

        # Strategia 4: Pierwszy długi tekst
        texts = [t.strip() for t in element.stripped_strings]
        for text in texts:
            if len(text) > 10 and len(text) < 100 and not text.isdigit():
                if not re.match(r'^\d+[./\-]\d+', text):
                    return text

        return "Bez tytułu"

    def extract_date(self, element):
        """Ekstraktuje datę wydarzenia"""
        # Strategia 1: Element time
        time_elem = element.find('time')
        if time_elem:
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                return datetime_attr
            return time_elem.get_text(strip=True)

        # Strategia 2: Klasy z 'date'
        date_elem = element.find(class_=re.compile(r'date|time|when', re.I))
        if date_elem:
            return date_elem.get_text(strip=True)

        # Strategia 3: Wzorce dat w tekście
        text = element.get_text()
        date_patterns = [
            r'\d{1,2}\.\d{1,2}\.\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2} \w+ \d{4}',
            r'\w+ \d{1,2}, \d{4}'
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]

        return "Brak daty"

    def extract_location(self, element):
        """Ekstraktuje lokalizację"""
        location_classes = [r'location', r'venue', r'place', r'address', r'where']
        for class_pattern in location_classes:
            loc_elem = element.find(class_=re.compile(class_pattern, re.I))
            if loc_elem:
                location = loc_elem.get_text(strip=True)
                if len(location) > 2:
                    return location

        text = element.get_text()
        location_keywords = [
            'galeria', 'muzeum', 'centrum', 'sala', 'teatr', 'kino',
            'gallery', 'museum', 'center', 'hall', 'theatre', 'cinema'
        ]

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in location_keywords):
                if len(line) < 100:
                    return line

        address_pattern = r'ul\.\s*[\w\s]+\d+|[\w\s]+\d+[,\s]*\d{2}-\d{3}'
        address_match = re.search(address_pattern, text, re.I)
        if address_match:
            return address_match.group().strip()

        return "Brak miejsca"

    def extract_description(self, element):
        """Ekstraktuje opis wydarzenia"""
        desc_classes = [r'desc', r'content', r'excerpt', r'summary', r'text']
        for class_pattern in desc_classes:
            desc_elem = element.find(class_=re.compile(class_pattern, re.I))
            if desc_elem:
                desc = desc_elem.get_text(strip=True)
                if len(desc) > 20:
                    return desc[:400] + "..." if len(desc) > 400 else desc

        paragraphs = element.find_all('p')
        longest_p = ""
        for p in paragraphs:
            p_text = p.get_text(strip=True)
            if len(p_text) > len(longest_p):
                longest_p = p_text

        if len(longest_p) > 20:
            return longest_p[:400] + "..." if len(longest_p) > 400 else longest_p

        all_text = element.get_text(strip=True)
        if len(all_text) > 50:
            return all_text[:300] + "..."

        return "Brak opisu"

    def extract_link(self, element):
        """Ekstraktuje link do wydarzenia"""
        link_elem = element.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if href.startswith('/'):
                return self.base_url + href
            elif href.startswith('http'):
                return href
        return ""

    def extract_category(self, element):
        """Ekstraktuje kategorię wydarzenia"""
        cat_elem = element.find(class_=re.compile(r'category|tag|type', re.I))
        if cat_elem:
            return cat_elem.get_text(strip=True)

        text = element.get_text().lower()
        if 'wystawa' in text or 'exhibition' in text:
            return "Wystawa"
        elif 'koncert' in text or 'concert' in text:
            return "Koncert"
        elif 'teatr' in text or 'theatre' in text:
            return "Teatr"
        elif 'film' in text or 'kino' in text:
            return "Film"

        return "Wydarzenie"

    def is_valid_event(self, event_data):
        """Sprawdza czy wydarzenie jest ważne"""
        title = event_data.get('tytul', '')

        if not title or title == "Bez tytułu" or len(title) < 5:
            return False

        if title.isdigit():
            return False

        nav_words = ['menu', 'nav', 'footer', 'header', 'sidebar', 'cookie', 'więcej', 'next', 'previous']
        if any(word in title.lower() for word in nav_words):
            return False

        # Dodatkowe sprawdzenie - czy to nie jest element nawigacyjny
        description = event_data.get('opis', '').lower()
        if len(description) < 20 and any(word in description for word in nav_words):
            return False

        return True

    def save_to_json(self, events_data, filename='echo_poznan_events_improved.json'):
        """Zapisuje dane do pliku JSON z metadanymi"""
        output_data = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_events': len(events_data),
                'source_url': self.events_url,
                'scraper_version': 'improved_v1.0'
            },
            'events': events_data
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Dane zapisane do pliku: {filename}")
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania: {e}")

    def print_events_summary(self, events_data):
        """Wyświetla podsumowanie"""
        print("\n" + "=" * 70)
        print("🎭 POPRAWIONE PODSUMOWANIE - ECHO POZNAŃ")
        print("=" * 70)

        total_events = len(events_data)
        print(f"📊 Łącznie unikalnych wydarzeń: {total_events}")

        if total_events > 0:
            # Statystyki kategorii
            categories = {}
            events_with_dates = 0
            events_with_locations = 0

            for event in events_data:
                cat = event.get('kategoria', 'Nieznana')
                categories[cat] = categories.get(cat, 0) + 1

                if event.get('data') and event['data'] != 'Brak daty':
                    events_with_dates += 1

                if event.get('miejsce') and event['miejsce'] != 'Brak miejsca':
                    events_with_locations += 1

            print(f"\n📈 Statystyki:")
            print(f"   📅 Z datami: {events_with_dates}/{total_events}")
            print(f"   📍 Z lokalizacjami: {events_with_locations}/{total_events}")
            print(f"   🏷️ Kategorie: {dict(list(categories.items())[:5])}")

            print(f"\n📝 Przykładowe wydarzenia:")
            for i, event in enumerate(events_data[:3], 1):
                print(f"\n{i}. 🎨 {event.get('tytul', 'Brak tytułu')}")
                print(f"   📅 Data: {event.get('data', 'Brak daty')}")
                print(f"   📍 Miejsce: {event.get('miejsce', 'Brak miejsca')}")
                print(f"   🏷️ Kategoria: {event.get('kategoria', 'Wydarzenie')}")
                if event.get('link'):
                    print(f"   🔗 Link: {event['link']}")

    def scrape_all_events(self):
        """Główna funkcja scrapingu"""
        print("🚀 Rozpoczynam poprawiony scraping Echo Poznań...")
        print(f"🌐 URL: {self.events_url}")

        try:
            self.driver.get(self.events_url)
            print("✅ Strona załadowana")

            if not self.wait_for_page_load():
                print("⚠️ Problemy z ładowaniem, ale kontynuuję...")

            total_elements = self.scroll_and_load_events(max_scrolls=6, scroll_pause=3)
            events = self.extract_all_events()

            return events

        except Exception as e:
            print(f"❌ Błąd podczas scrapingu: {e}")
            import traceback
            traceback.print_exc()
            return []

    def close(self):
        """Zamyka driver"""
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """Główna funkcja programu"""
    print("🎭 Echo Poznań - Poprawiony Scraper")
    print("=" * 70)

    try:
        with EchoPoznanImprovedScraper(headless=True) as scraper:
            # Pobierz wszystkie wydarzenia
            print("📡 Pobieranie wszystkich wydarzeń...")
            all_events = scraper.scrape_all_events()

            if not all_events:
                print("❌ Nie znaleziono żadnych wydarzeń")
                return

            print(f"✅ Pobrano {len(all_events)} unikalnych wydarzeń")

            # Wyświetl podsumowanie
            scraper.print_events_summary(all_events)

            # Zapisz dane
            scraper.save_to_json(all_events)

            # Statystyki końcowe
            print(f"\n📊 STATYSTYKI KOŃCOWE:")
            print(f"   🔢 Unikalnych wydarzeń: {len(all_events)}")
            print(
                f"   🚫 Duplikatów pominięto: {len(scraper.seen_events) - len(all_events) if len(scraper.seen_events) > len(all_events) else 0}")
            print(f"   💾 Zapisano do: echo_poznan_events_improved.json")
            print(f"   🐛 Debug HTML: debug_page.html")

    except KeyboardInterrupt:
        print("\n⏹️ Przerwano przez użytkownika")
    except Exception as e:
        print(f"❌ Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Wymagane instalacje:")
        print("   pip install selenium beautifulsoup4 webdriver-manager")
        print("   + Google Chrome")


if __name__ == "__main__":
    main()