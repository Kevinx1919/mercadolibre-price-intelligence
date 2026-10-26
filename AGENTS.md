# AGENTS.md

## Project overview

Construir un lakehouse de precios de laptops de Mercado Libre Colombia (`MCO`)
que permita analizar tendencias, descuentos y vendedores mediante Databricks y
Power BI.

## Arquitectura acordada

```text
Mercado Libre API -> raw JSON -> Unity Catalog Volume -> Bronze Delta
-> Silver Delta -> Gold Delta -> Power BI
```

- **Extracción:** Python obtiene datos y conserva el payload original.
- **Volume `raw_marketplace`:** zona de archivos de aterrizaje; no es una tabla.
- **Tablas Delta:** constituyen las capas Bronze, Silver y Gold dentro del schema
  `workspace.meli_price_intelligence`.
- **n8n + Ollama:** revisan deriva de esquema y alertan; no realizan las
  transformaciones de datos ni modifican producción automáticamente.

## Development environment tips

- Usar Python 3.13 o superior.
- Crear un entorno virtual con `py -m venv .venv` y activarlo con
  `.\.venv\Scripts\Activate.ps1`.
- Instalar dependencias con `python -m pip install -r requirements.txt`.
- Ejecutar el extractor local con `python src\extract_marketplace.py`.
- Los archivos de `data/raw/` son datos de ejecución y están ignorados por Git.
- Mantener notebooks, jobs y configuraciones de Databricks en archivos
  versionados dentro del repositorio; no dejar la única versión en la UI.

## Convenciones de datos

- Nunca modificar un JSON raw descargado de la API.
- Cada corrida debe poder identificarse mediante `run_id`, fecha/hora UTC,
  parámetros de la petición y hash SHA-256.
- Mantener datos de ejecución fuera de Git; `data/raw/` está ignorado.
- Las transformaciones deben ser idempotentes: reejecutar una corrida no debe
  crear duplicados en las tablas analíticas.
- El precio se modela como un hecho histórico (`price_snapshot`), no como una
  dimensión SCD Tipo 2.

## Code style guidelines

- Usar type hints, funciones pequeñas y mensajes de error accionables.
- Separar llamadas HTTP, persistencia de archivos y lógica de transformación.
- Persistir timestamps en UTC.
- No codificar credenciales, tokens, URLs de workspace o rutas personales.
- Preferir transformaciones deterministas en PySpark; la IA solo asesora.

## Testing instructions

- Antes de cada commit de Python, ejecutar `py -m compileall -q src`.
- Validar cambios de CLI con `python src\extract_marketplace.py --help`.
- Cuando exista la suite, ejecutar todos los tests desde la raíz del repositorio.
- Añadir o actualizar pruebas para cambios en paginación, reintentos,
  validaciones, transformaciones e idempotencia.
- Nunca usar llamadas reales a la API como única prueba automatizada; usar
  fixtures o mocks.

## Seguridad

- No versionar credenciales, tokens, archivos `.env` ni configuraciones locales.
- `config.toml` se trata como configuración local y permanece fuera del repositorio.
- Usar solo endpoints públicos de Mercado Libre mientras el proyecto no requiera
  autorización de vendedor.

## Commit and pull request guidelines

- Usar commits cortos con estilo Conventional Commit, por ejemplo
  `feat: add bronze ingestion notebook`.
- Mantener cada commit limitado a un cambio lógico.
- No añadir al staging archivos locales no relacionados, como `codigo.py` o
  `config.toml`.
- Los PR deben indicar propósito de negocio, pruebas ejecutadas, impacto en el
  contrato de datos y pasos de despliegue en Databricks.

## Desarrollo local

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src\extract_marketplace.py
```

## Estado actual

La versión base implementa una extracción de una página de búsqueda de Mercado
Libre con reintentos, persistencia de payload raw y manifiesto de corrida. El
siguiente componente será la ingesta Bronze en Databricks.
