import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright
from modules.utilerias import ConfigManager

class AmazonScraper:
    """
    Handles Playwright automation to scrape Amazon search results, 
    interact with browser UI filters (checkboxes), and export to CSV.
    """
    def __init__(self, config_dir: str):
        self.config_manager = ConfigManager()
        self.scraping_config = self.config_manager.load_config("scraping", os.path.join(config_dir, "scraping_config.json"))
        self.xpaths = self.config_manager.load_config("xpaths", os.path.join(config_dir, "xpaths.json"))
        
        self.url = self.scraping_config.get("url", "https://www.amazon.com.mx")
        self.search_term = self.scraping_config.get("search_term", "CHOCOLATES")
        self.output_file = self.scraping_config.get("output_file", "chocolates_data.csv")

    def extract_items(self, page, max_items) -> list:
        """
        Helper method to wait for and extract up to max_items from the current page state.
        """
        container_xpath = self.xpaths.get("amazon_results_container")
        page.wait_for_selector(container_xpath, timeout=15000)
        # Small sleep to ensure the DOM is fully settled after any AJAX updates
        page.wait_for_timeout(2000)
        
        items = page.locator(container_xpath).all()
        results = []
        
        for i, item in enumerate(items):
            if len(results) >= max_items:
                break
                
            try:
                title_loc = item.locator(self.xpaths.get("item_title"))
                title = title_loc.first.text_content().strip() if title_loc.count() > 0 else ""
                
                if not title:
                    continue
                    
                price_loc = item.locator(self.xpaths.get("item_price"))
                
                price_str = "0.0"
                if price_loc.count() > 0:
                    raw_price = price_loc.first.text_content().strip()
                    import re
                    match = re.search(r'[\d,]+\.?\d*', raw_price)
                    if match:
                        price_str = match.group(0).replace(',', '')
                        
                try:
                    price = float(price_str)
                except ValueError:
                    price = 0.0
                    
                delivery_loc = item.locator(self.xpaths.get("item_delivery"))
                delivery = delivery_loc.first.text_content().strip() if delivery_loc.count() > 0 else "No disponible"
                delivery = " ".join(delivery.split())
                
                results.append({
                    "title": title,
                    "price": price,
                    "delivery_date": delivery
                })
            except Exception as e:
                print(f"[-] Error extrayendo item {i}: {e}")
                
        return results

    def run_scraper(self) -> list:
        print("\n[*] Iniciando Web Scraping con Playwright (automatización de la UI)...")
        all_data = []

        with sync_playwright() as p:
            # We use headless=False to avoid Amazon bot detection and for interview presentation.
            browser = p.chromium.launch(headless=False, slow_mo=100)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            # 1. Navigate to Amazon
            print(f"[*] 1. Navegando a {self.url}...")
            page.goto(self.url, timeout=60000)
            
            # 2. Search for CHOCOLATES
            print(f"[*] 2. Buscando '{self.search_term}'...")
            search_box = self.xpaths.get("amazon_search_box")
            search_btn = self.xpaths.get("amazon_search_button")
            
            # Wait explicitly for the search box to exist (bypassing slow loads)
            page.wait_for_selector(search_box, timeout=20000)
            page.fill(search_box, self.search_term)
            page.click(search_btn)
            
            # 3. Extract first 25 general items
            print("[*] 3. Extrayendo los primeros 25 resultados...")
            general_items = self.extract_items(page, 25)
            all_data.extend(general_items)
            print(f"[+] Se extrajeron {len(general_items)} items generales.")
            
            # 4. Filter by Turin and extract 10
            print("[*] 4. Seleccionando la casilla de marca 'Turin' en la interfaz...")
            try:
                # Force click the sidebar element using raw Javascript to bypass Playwright's restrictive visibility tests.
                page.evaluate('''() => {
                    let items = Array.from(document.querySelectorAll('#s-refinements li, #brandsRefinements li, #filters li'));
                    for (let item of items) {
                        if (item.innerText.toLowerCase().includes('turin')) {
                            let link = item.querySelector('a') || item.querySelector('input');
                            if (link) { link.click(); return; }
                        }
                    }
                    // Si no se encuentra, tal vez esté en "Ver más". Hacemos clic si existe.
                    let seeMore = document.querySelector('#brandsRefinements .a-expander-prompt');
                    if(seeMore) seeMore.click();
                }''')
                page.wait_for_timeout(1500)
                # Attempt again if it was hidden
                page.evaluate('''() => {
                    let items = Array.from(document.querySelectorAll('#s-refinements li, #brandsRefinements li, #filters li'));
                    for (let item of items) {
                        if (item.innerText.toLowerCase().includes('turin')) {
                            let link = item.querySelector('a') || item.querySelector('input');
                            if (link) { link.click(); return; }
                        }
                    }
                }''')
                page.wait_for_timeout(4000)
                
                print("[*] Extrayendo los primeros 10 resultados de Turin...")
                turin_items = self.extract_items(page, 10)
                all_data.extend(turin_items)
                print(f"[+] Se extrajeron {len(turin_items)} items de Turin.")
                
                # Deselect Turin (Clicks it again to uncheck)
                print("[*] Deseleccionando la casilla 'Turin'...")
                page.evaluate('''() => {
                    let items = Array.from(document.querySelectorAll('#s-refinements li, #brandsRefinements li, #filters li'));
                    for (let item of items) {
                        if (item.innerText.toLowerCase().includes('turin')) {
                            let link = item.querySelector('a') || item.querySelector('input');
                            if (link) { link.click(); return; }
                        }
                    }
                }''')
                page.wait_for_timeout(4000)
            except Exception as e:
                print(f"[-] Error al interactuar con el filtro Turin: {e}")

            # 5. Filter by Nestlé and extract 10
            print("[*] 5. Seleccionando la casilla de marca 'Nestlé' en la interfaz...")
            try:
                page.evaluate('''() => {
                    let items = Array.from(document.querySelectorAll('#s-refinements li, #brandsRefinements li, #filters li'));
                    for (let item of items) {
                        if (item.innerText.toLowerCase().includes('nestl')) {
                            let link = item.querySelector('a') || item.querySelector('input');
                            if (link) { link.click(); return; }
                        }
                    }
                    // Ver más
                    let seeMore = document.querySelector('#brandsRefinements .a-expander-prompt');
                    if(seeMore) seeMore.click();
                }''')
                page.wait_for_timeout(1500)
                page.evaluate('''() => {
                    let items = Array.from(document.querySelectorAll('#s-refinements li, #brandsRefinements li, #filters li'));
                    for (let item of items) {
                        if (item.innerText.toLowerCase().includes('nestl')) {
                            let link = item.querySelector('a') || item.querySelector('input');
                            if (link) { link.click(); return; }
                        }
                    }
                }''')
                page.wait_for_timeout(4000)
                
                print("[*] Extrayendo los primeros 10 resultados de Nestlé...")
                nestle_items = self.extract_items(page, 10)
                all_data.extend(nestle_items)
                print(f"[+] Se extrajeron {len(nestle_items)} items de Nestlé.")
            except Exception as e:
                print(f"[-] Error al interactuar con el filtro Nestlé: {e}")

            browser.close()

        print(f"\n[+] Extracción finalizada. Total de productos extraídos y consolidados: {len(all_data)}")
        
        # 6. Save data to CSV with specific encoding and separator
        if all_data:
            df = pd.DataFrame(all_data)
            try:
                # Se guarda en encoding Windows-1252 y separador '|'
                df.to_csv(self.output_file, index=False, encoding='cp1252', sep='|', errors='replace')
                print(f"[+] Archivo CSV generado exitosamente: {os.path.abspath(self.output_file)}")
            except Exception as e:
                print(f"[-] Error guardando CSV: {e}")
                
        return all_data
