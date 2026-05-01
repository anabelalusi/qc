# Solar QC — Control de calidad de irradiancia solar

Herramienta web interactiva para el control de calidad de series de irradiancia solar.

## Etapa 1 — GHI (exploración + filtros automáticos)

**Funcionalidades:**
- Carga de CSV con mapeo flexible de columnas
- Cálculo de geometría solar (declinación, CZ, kt, altura solar, azimut)
- Filtros automáticos universales: altura solar < 7° y kt > 1.35
- Gráficos interactivos: serie temporal, CZ vs GHI, CZ vs kt
- Exportación del CSV procesado

## Estructura

```
solar_qc/
├── app.py              # App principal Streamlit
├── requirements.txt    # Dependencias Python
└── README.md
```

## Correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy gratuito en Streamlit Community Cloud

1. Subí esta carpeta a un repositorio público en GitHub
2. Entrá a https://share.streamlit.io
3. Conectá tu cuenta de GitHub
4. Seleccioná el repo y el archivo `app.py`
5. ¡Listo! La app queda disponible en una URL pública

## Deploy alternativo: Hugging Face Spaces

1. Creá un Space en https://huggingface.co/spaces
2. Elegí SDK: **Streamlit**
3. Subí los archivos
4. La URL pública queda activa automáticamente

## Variables soportadas (roadmap)

| Variable | Estado     |
|----------|------------|
| GHI      | ✅ Etapa 1  |
| DHI      | 🔜 Próximo |
| DNI      | 🔜 Próximo |
| PAR      | 🔜 Próximo |
