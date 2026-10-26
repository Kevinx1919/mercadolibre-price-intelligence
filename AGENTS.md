# Mercado Libre Price Intelligence — guía de contribución

## Objetivo

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

## Convenciones de datos

- Nunca modificar un JSON raw descargado de la API.
- Cada corrida debe poder identificarse mediante `run_id`, fecha/hora UTC,
  parámetros de la petición y hash SHA-256.
- Mantener datos de ejecución fuera de Git; `data/raw/` está ignorado.
- Las transformaciones deben ser idempotentes: reejecutar una corrida no debe
  crear duplicados en las tablas analíticas.
- El precio se modela como un hecho histórico (`price_snapshot`), no como una
  dimensión SCD Tipo 2.

## Seguridad

- No versionar credenciales, tokens, archivos `.env` ni configuraciones locales.
- `config.toml` se trata como configuración local y permanece fuera del repositorio.
- Usar solo endpoints públicos de Mercado Libre mientras el proyecto no requiera
  autorización de vendedor.

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
