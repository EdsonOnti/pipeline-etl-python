import os
import pandas as pd
from modules.operaciones_excel import ExcelManager
from modules.utilerias import DataCleaner
from modules.database import DatabaseManager
from modules.organizaciones import EmpresaProveedor, EmpresaCliente, parse_empresa_string
from modules.scraping import AmazonScraper

class MainApp:
    """
    Clase que contiene el método Main y unifica todo el código para realizar 
    las partes del proyecto. Ejecuta el programa en modo consola.
    """
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.excel_path = os.path.join(base_dir, "Test- ASDI", "datos_prueba.xlsx")
        self.config_dir = os.path.join(base_dir, "config")
        
    def ejecutar(self):
        print("\n" + "="*50)
        print("=== INICIANDO PIPELINE DE DATOS ===")
        print("="*50 + "\n")
        
        # 1. Operaciones Excel (Parte 1)
        print(">>> PARTE 1: OPERACIONES EXCEL")
        excel = ExcelManager(self.excel_path)
        try:
            excel.refresh_excel_data()
        except Exception as e:
            print("[!] Aviso: No se pudo refrescar Excel via COM, continuando con la lectura...")
            
        df = excel.load_to_dataframe()
        
        # 2. Limpieza de Datos y Transformaciones (Parte 2 y 3)
        print("\n>>> PARTE 2: LIMPIEZA DE DATOS Y TRANSFORMACIONES")
        df_clean = DataCleaner.transform_dataframe(df)
        
        # 3. OOP y Entrega de Resultados (Parte 4)
        print("\n>>> PARTE 4: ENTREGA DE RESULTADOS (MODO CONSOLA)")
        
        # Determinamos las columnas
        col_proveedor = 'empresa_proveedor'
        col_cliente = 'empresa'
        
        for index, row in df_clean.iterrows():
            str_proveedor = row.get(col_proveedor, "") if col_proveedor in df_clean.columns else ""
            str_cliente = row.get(col_cliente, "") if col_cliente in df_clean.columns else ""
            
            # Parse strings like "Recargas Latinas..., Calle Falsa 1234..."
            nom_prov, dir_prov = parse_empresa_string(str_proveedor)
            nom_cli, dir_cli = parse_empresa_string(str_cliente)
            
            proveedor = EmpresaProveedor(nom_prov, dir_prov)
            cliente = EmpresaCliente(nom_cli, dir_cli)
            
            # Imprimir resultado exacto esperado:
            print("-" * 60)
            print(proveedor.mostrarEmpresa())
            print(cliente.mostrarEmpresa())
            
            # Imprimir el resto de los campos solicitados
            print(f"Fecha de Pago:         {row.get('fecha_pago')}")
            print(f"Ajuste Total:          {row.get('ajuste_total')}")
            print(f"Semana Facturada:      {row.get('semana_facturada')}")
            print(f"Pines Consumidos:      {row.get('pines_consumidos')}")
            print(f"Número de Fact.:       {row.get('numero_factura_limpia')}")

        print("-" * 60)
        
        # 4. Base de Datos (Parte 3)
        print("\n>>> PARTE 3: INSERCIÓN EN BASE DE DATOS")
        db_config_path = os.path.join(self.config_dir, "db_config.json")
        try:
            db = DatabaseManager(db_config_path)
            db.setup_schema()
            db.insert_facturas(df_clean)
            
            # 5. Webscraping (Parte 5)
            print("\n>>> PARTE 5: WEBSCRAPING (AMAZON)")
            scraper = AmazonScraper(self.config_dir)
            scraped_data = scraper.run_scraper()
            
            print("\n[*] Insertando datos del webscraping en Base de Datos...")
            db.insert_scraped_data(scraped_data)
            
            db.close()
            print("\n=== PROCESO FINALIZADO CON ÉXITO ===")
        except Exception as e:
            print(f"[-] Error en el proceso: {e}")

if __name__ == "__main__":
    app = MainApp()
    app.ejecutar()
