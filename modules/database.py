import pandas as pd
import mysql.connector
from .utilerias import ConfigManager

class DatabaseManager:
    """
    Manages MySQL database connections, schema creation,
    and handles insertion of both Facturas and Scraped data.
    """

    def __init__(self, config_file_path: str):
        # We use the Singleton ConfigManager
        self.config_manager = ConfigManager()
        self.db_config = self.config_manager.load_config("db", config_file_path)
        
        # We establish connection using the config
        try:
            print("[*] Connecting to MySQL Database...")
            self.conn = mysql.connector.connect(
                host=self.db_config.get("host", "localhost"),
                user=self.db_config.get("user", "root"),
                password=self.db_config.get("password", ""),
                port=self.db_config.get("port", 3306)
            )
            self.cursor = self.conn.cursor()
            
            # Ensure the database exists and select it
            db_name = self.db_config.get("database", "facturas_db")
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            self.cursor.execute(f"USE {db_name}")
            print(f"[+] Connected to database '{db_name}'.")
            
        except mysql.connector.Error as err:
            print(f"[-] Error connecting to MySQL: {err}")
            raise

    def setup_schema(self):
        """
        Creates the required tables if they do not exist.
        """
        print("[*] Setting up database schema...")
        # Table for Facturas
        create_facturas_table = """
        CREATE TABLE IF NOT EXISTS facturas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            numero_factura_limpia VARCHAR(100),
            fecha DATE,
            fecha_pago DATE,
            importe FLOAT,
            impuesto FLOAT,
            subtotal FLOAT,
            total FLOAT,
            ajuste_total FLOAT,
            ruta_archivo_factura VARCHAR(255),
            semana_facturada INT,
            pines_consumidos INT
        )
        """
        self.cursor.execute(create_facturas_table)
        
        # Table for Scraped Chocolates
        create_chocolates_table = """
        CREATE TABLE IF NOT EXISTS chocolates_scraped (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            price FLOAT,
            delivery_date VARCHAR(100)
        )
        """
        self.cursor.execute(create_chocolates_table)
        self.conn.commit()
        print("[+] Database schema successfully set up.")

    def insert_facturas(self, df: pd.DataFrame):
        """
        Inserts the cleaned and transformed DataFrame into the MySQL database.
        """
        print("[*] Inserting Facturas into database...")
        insert_query = """
        INSERT INTO facturas (
            numero_factura_limpia, fecha, fecha_pago,
            importe, impuesto, subtotal, total, ajuste_total,
            ruta_archivo_factura, semana_facturada, pines_consumidos
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Convert DataFrame to list of tuples properly replacing NaNs with None
        df_clean = df.where(pd.notnull(df), None)
        
        bulk_data = []
        for _, row in df_clean.iterrows():
            bulk_data.append((
                row.get('numero_factura_limpia'),
                row.get('fecha'),
                row.get('fecha_pago'),
                row.get('importe'),
                row.get('impuesto'),
                row.get('subtotal'),
                row.get('total'),
                row.get('ajuste_total'),
                row.get('ruta_archivo_factura'),
                row.get('semana_facturada'),
                row.get('pines_consumidos')
            ))
            
        if not bulk_data:
            print("[-] No valid data to insert.")
            return

        try:
            # We use executemany for bulk insertion efficiency
            self.cursor.executemany(insert_query, bulk_data)
            self.conn.commit()
            print(f"[+] Successfully inserted {self.cursor.rowcount} rows into 'facturas'.")
        except mysql.connector.Error as err:
            print(f"[-] Error inserting facturas: {err}")
            self.conn.rollback()

    def insert_scraped_data(self, data_list: list):
        """
        Inserts a list of dictionaries containing web scraped results into the database.
        We will pass a list of dicts from Part 5.
        """
        insert_query = """
        INSERT INTO chocolates_scraped (title, price, delivery_date) 
        VALUES (%s, %s, %s)
        """
        
        bulk_data = []
        for item in data_list:
            bulk_data.append((
                item.get('title'),
                item.get('price'),
                item.get('delivery_date')
            ))
            
        try:
            self.cursor.executemany(insert_query, bulk_data)
            self.conn.commit()
            print(f"[+] Successfully inserted {self.cursor.rowcount} scraped items.")
        except mysql.connector.Error as err:
            print(f"[-] Error inserting scraped items: {err}")
            self.conn.rollback()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
