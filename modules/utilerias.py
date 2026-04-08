import re
import json
import pandas as pd
from datetime import datetime
from typing import Any, Dict

class ConfigManager:
    """
    Singleton class to manage configuration loading.
    Ensures that JSON config files are only read from the disk once
    during the pipeline execution, saving I/O resources.
    """
    _instance = None
    _configs: Dict[str, Any] = {}

    def __new__(cls):
        # Implementation of the Singleton pattern
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def load_config(self, name: str, file_path: str) -> dict:
        """
        Loads a JSON config into memory. Returns the cached version if already loaded.
        """
        if name not in self._configs:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._configs[name] = json.load(f)
                    print(f"[*] Config '{name}' loaded successfully.")
            except Exception as e:
                print(f"[-] Error loading config {name} at {file_path}: {e}")
                self._configs[name] = {}
                
        return self._configs[name]

    def get_config(self, name: str) -> dict:
        """
        Retrieves a loaded configuration by name.
        """
        return self._configs.get(name, {})


class DataCleaner:
    """
    Class responsible for cleaning and normalizing data.
    Provides utility methods to transform raw data from Excel into
    the desired clean format for the database.
    """

    @staticmethod
    def clean_numero_factura(invoice_number) -> str:
        """
        Removes fixed strange characters from the invoice number.
        We assume any character that is not alphanumeric or a dash is 'strange'.
        """
        if pd.isna(invoice_number):
            return ""
            
        # Remove anything that isn't a letter or a number
        # Note: I assume dashes are allowed, regex would be [^a-zA-Z0-9-]
        cleaned = re.sub(r'[^a-zA-Z0-9-]', '', str(invoice_number))
        return cleaned

    @staticmethod
    def parse_fecha(date_val) -> str:
        """
        Converts the date to a standard 'YYYY-MM-DD' format.
        """
        if pd.isna(date_val):
            return None
        
        try:
            # pandas to_datetime is very robust for various Excel date formats
            parsed_date = pd.to_datetime(date_val)
            return parsed_date.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"[-] Error parsing date '{date_val}': {e}")
            return None

    @staticmethod
    def clean_numeric(value) -> float:
        if pd.isna(value):
            return 0.0

        cleaned_str = str(value).strip()

        try:
            if ',' in cleaned_str and '.' in cleaned_str:
                if cleaned_str.rfind(',') > cleaned_str.rfind('.'):
                    cleaned_str = cleaned_str.replace('.', '').replace(',', '.')
                else:
                    cleaned_str = cleaned_str.replace(',', '')

            elif ',' in cleaned_str:
                cleaned_str = cleaned_str.replace(',', '.')

            return float(cleaned_str)

        except ValueError:
            print(f"[-] Warning: Could not convert '{value}' → '{cleaned_str}'")
            return 0.0

    @staticmethod
    def clean_ruta_archivo(file_path: str) -> str:
        """
        Cleans the file path by normalizing backslashes 
        and removing bad escape sequences.
        """
        if pd.isna(file_path):
            return ""
            
        path_str = str(file_path)
        # Often raw paths read from Excel with escape sequences (\n, \t) 
        # might be represented literally or as actual whitespace.
        # We replace newline/tab and standardize slashes.
        path_str = path_str.replace('\n', '').replace('\t', '').replace('\r', '').strip()
        # Convert backward slashes to forward slashes for cross-platform compatibility
        path_str = path_str.replace('\\', '/')
        return path_str

    @staticmethod
    def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies all column-level cleaning and creates derived fields based on business logic.
        """
        print("[*] Applying rules and data cleaning to DataFrame...")
        
        # Ensure we have a copy to avoid SettingWithCopyWarning
        df = df.copy()

        # 1. Clean core columns (if they exist in the Excel file)
        if 'numero_factura' in df.columns:
            df['numero_factura_limpia'] = df['numero_factura'].apply(DataCleaner.clean_numero_factura)
            
        if 'fecha' in df.columns:
            df['fecha'] = df['fecha'].apply(DataCleaner.parse_fecha)
            
        for col in ['importe', 'impuesto', 'subtotal', 'total']:
            if col in df.columns:
                df[col] = df[col].apply(DataCleaner.clean_numeric)
                
        if 'ruta_archivo_factura' in df.columns:
            df['ruta_archivo_factura'] = df['ruta_archivo_factura'].apply(DataCleaner.clean_ruta_archivo)

        # 2. Derived Field: fecha_pago from condiciones_pago (e.g. '30 días')
        def calc_fecha_pago(row):
            cond = str(row.get('condiciones_pago', ''))
            match = re.search(r'\d+', cond)
            if match and pd.notna(row.get('fecha')):
                days = int(match.group())
                try:
                    date_val = pd.to_datetime(row['fecha'])
                    return (date_val + pd.Timedelta(days=days)).strftime('%Y-%m-%d')
                except Exception as e:
                    print(f"Error: {e}")
            return row.get('fecha')
            
        if 'condiciones_pago' in df.columns and 'fecha' in df.columns:
            df['fecha_pago'] = df.apply(calc_fecha_pago, axis=1)

        # 3. Derived Field: ajuste_total
        if 'subtotal' in df.columns:
            df['ajuste_total'] = df['subtotal'] * 1.16 + 0.0254

        # 4. Derived Fields: semana_facturada & pines_consumidos from 'descripcion'
        def extract_semana(desc):
            pattern = r'del\s*(\d{1,2})\s*de\s*([a-záéíóúñ]+)\s*al\s*(\d{1,2})\s*de\s*([a-záéíóúñ]+)\s*del\s*(\d{4})'
            match = re.search(pattern, desc, re.IGNORECASE)

            if not match:
                return None

            dia_inicio = int(match.group(1))
            mes_inicio = match.group(2).lower()
            anio = int(match.group(5))

            meses = {
                "enero": 1, "febrero": 2, "marzo": 3,
                "abril": 4, "mayo": 5, "junio": 6,
                "julio": 7, "agosto": 8, "septiembre": 9,
                "octubre": 10, "noviembre": 11, "diciembre": 12
            }

            mes_num = meses.get(mes_inicio)

            if not mes_num:
                return None

            fecha = datetime(anio, mes_num, dia_inicio)

            return fecha.isocalendar().week
        def extract_pines(desc):
            match = re.search(r'Consumo de\s*(\d+)\s*pines', str(desc), re.IGNORECASE)
            return int(match.group(1)) if match else None

        if 'descripcion' in df.columns:
            df['semana_facturada'] = df['descripcion'].apply(extract_semana)
            df['pines_consumidos'] = df['descripcion'].apply(extract_pines)

        print("[+] DataFrame transformations applied successfully.")
        return df
