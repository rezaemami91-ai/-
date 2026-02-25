import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime
import logging

class OptionScanner:
    def __init__(self, config_path='config.json'):
        self.load_config(config_path)
        self.setup_logging()
        
    def load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.sites = self.config.get('sites_to_monitor', [])
        self.scan_interval = self.config.get('scan_interval', 300)
        self.alert_thresholds = self.config.get('alert_thresholds', {})
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_page(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_optionbaaz(self, html):
        options_data = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        option_data = {
                            'symbol': cols[0].text.strip(),
                            'type': cols[1].text.strip(),
                            'strike': cols[2].text.strip(),
                            'price': cols[3].text.strip(),
                            'volume': cols[4].text.strip(),
                            'change': cols[5].text.strip(),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'optionbaaz.ir'
                        }
                        options_data.append(option_data)
        except Exception as e:
            self.logger.error(f"Error parsing optionbaaz: {e}")
        
        return options_data
    
    def scan_all_sites(self):
        all_options = []
        
        for site in self.sites:
            self.logger.info(f"Scanning {site}")
            html = self.fetch_page(site)
            
            if html:
                if 'optionbaaz' in site:
                    data = self.parse_optionbaaz(html)
                else:
                    data = self.parse_generic(html)
                
                all_options.extend(data)
                time.sleep(2)
        
        return all_options
    
    def analyze_opportunities(self, options_data):
        opportunities = []
        
        for option in options_data:
            score = 0
            signals = []
            
            if 'volume' in option and option['volume'].isdigit():
                vol = int(option['volume'])
                if vol > 1000:
                    score += 2
                    signals.append("حجم معاملات بالا")
            
            if 'change' in option:
                try:
                    change = float(option['change'].replace('%', ''))
                    if abs(change) > 5:
                        score += 3
                        signals.append(f"تغییر قیمت قابل توجه: {change}%")
                except:
                    pass
            
            if score >= 3:
                opportunity = {
                    'option': option,
                    'score': score,
                    'signals': signals,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                opportunities.append(opportunity)
        
        return sorted(opportunities, key=lambda x: x['score'], reverse=True)[:10]
    
    def save_results(self, opportunities):
        filename = f"scan_results/opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(opportunities, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Results saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
