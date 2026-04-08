# Pipeline ETL — Automatización

Proyecto de prueba técnica que implementa un pipeline de datos completo en Python, cubriendo extracción desde Excel, limpieza y transformación, persistencia en base de datos MySQL y web scraping con automatización de navegador.

---

## Funcionalidades

| Módulo | Descripción |
|---|---|
| **Operaciones Excel** | Carga y refresca datos desde `.xlsx` usando `openpyxl` y `pandas` |
| **Limpieza de Datos** | Normalización, validación y transformación de campos con `pandas` |
| **OOP / Modelo de Negocio** | Clases `EmpresaProveedor` y `EmpresaCliente` para estructurar entidades |
| **Base de Datos (MySQL)** | Creación de esquema, inserción y consulta de facturas con `mysql-connector-python` |
| **Web Scraping** | Automatización de búsqueda en Amazon con `Playwright`, filtrado por marca y exportación a CSV |

---

## Arquitectura del Proyecto

```
├── main.py                  # Orquestador principal del pipeline
├── requirements.txt
├── config/
│   ├── db_config.example.json   # Plantilla de credenciales (copiar a db_config.json)
│   ├── scraping_config.json     # Parámetros del scraper (URL, marcas, límites)
│   └── xpaths.json              # Selectores XPath para Playwright
├── modules/
│   ├── operaciones_excel.py     # Clase ExcelManager
│   ├── utilerias.py             # DataCleaner y ConfigManager
│   ├── database.py              # Clase DatabaseManager
│   ├── organizaciones.py        # Clases EmpresaProveedor / EmpresaCliente
│   └── scraping.py              # Clase AmazonScraper (Playwright)
└── Test- ASDI/
    └── datos_prueba.xlsx        # Dataset de entrada
```

---

## Tecnologías Utilizadas

- **Python 3.11+**
- **pandas** — Transformación y análisis de datos
- **openpyxl / pywin32** — Operaciones sobre archivos Excel
- **mysql-connector-python** — Conexión y operaciones en MySQL
- **Playwright** — Automatización de navegador para web scraping
- **JSON** — Configuración modular y flexible

---

## Cómo ejecutar

### 1. Clonar el repositorio

```bash
git clone https://github.com/EdsonOnti/pipeline-etl-python.git
cd pipeline-etl-python
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configurar la base de datos

```bash
cp config/db_config.example.json config/db_config.json
# Editar db_config.json con tus credenciales de MySQL
```

### 4. Ejecutar el pipeline

```bash
python main.py
```

---

## Flujo del Pipeline

```
datos_prueba.xlsx
      │
      ▼
ExcelManager → carga el archivo a DataFrame
      │
      ▼
DataCleaner → limpieza, normalización y transformación
      │
      ├──► DatabaseManager → inserta facturas en MySQL
      │
      └──► AmazonScraper (Playwright) → scraping por marcas
                  │
                  ▼
         chocolates_output.csv + inserción en DB
```

---

## Autor

**Edson Ontiveros Lima**
[LinkedIn](https://www.linkedin.com/in/edson-martin-ontiveros-lima-673b5b148/) · [GitHub](https://github.com/EdsonOnti)
"# pipeline-etl-python" 
