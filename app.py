"""
Solar QC — Control de calidad de irradiancia solar
Flujo: datos crudos → exploración global → análisis anual → flags BSRN

Convenio de flags (BSRN):
    0 = dato válido
    1 = dato descartado

Columnas de salida:
    flag_1   → altura solar < 7°   (filtro automático opcional)
    flag_2   → kt > 1.35           (filtro automático opcional)
    flag_3   → inspección visual   (Etapa 2, sombras manuales — reservado)
    flag_qc  → OR(flag_1, flag_2, flag_3) — resumen final
"""

#%%

# ```bash
# pip install -r requirements.txt
# streamlit run app.py
# ```

#%%

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ─── Página ───────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Solar QC",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilos ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #21262d; }

.solar-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.2rem; font-weight: 600; color: #e6edf3;
    line-height: 1.1; margin-bottom: 0.3rem;
}
.solar-sub { color: #8b949e; font-size: 1.1rem; margin-bottom: 1.5rem; }

.section-badge {
    display: inline-block; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem; font-weight: 600; color: #0d1117; background: #f0a500;
    padding: 0.12rem 0.45rem; border-radius: 3px;
    letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.4rem;
}
.section-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.05rem;
    font-weight: 500; color: #e6edf3; margin-bottom: 0.2rem;
}
.section-desc { color: #8b949e; font-size: 1.0rem; margin-bottom: 1rem; }

.metric-row { display: flex; gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }
.metric-card {
    background: #161b22; border: 1px solid #21262d; border-radius: 6px;
    padding: 0.8rem 1.1rem; flex: 1; min-width: 120px;
}
.metric-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; color: #8b949e;
    text-transform: uppercase; letter-spacing: 0.1em;
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.45rem;
    font-weight: 600; color: #f0a500;
}
.metric-sub { font-size: 0.85rem; color: #8b949e; }

.filter-box {
    background: #161b22; border: 1px solid #21262d; border-left: 3px solid #f0a500;
    border-radius: 4px; padding: 1rem 1.2rem; margin: 0.8rem 0;
}
.filter-box-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 600;
    color: #f0a500; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;
}
.filter-box-ref { font-size: 0.9rem; color: #8b949e; margin-top: 0.4rem; font-style: italic; }

.flag-summary {
    background: #0d1117; border: 1px solid #21262d; border-radius: 4px;
    padding: 0.8rem 1rem; margin-top: 0.8rem;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: #8b949e;
}
.flag-summary b  { color: #f0a500; }
.flag-summary .ok   { color: #3fb950; }
.flag-summary .disc { color: #f85149; }

.flag-legend {
    background: #161b22; border: 1px solid #21262d; border-radius: 4px;
    padding: 0.7rem 1rem; margin-bottom: 1rem; font-size: 0.8rem; color: #8b949e;
}
.flag-legend code {
    font-family: 'IBM Plex Mono', monospace; color: #e6edf3;
    background: #0d1117; padding: 0.1rem 0.35rem; border-radius: 3px;
}

.log-line {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: #8b949e;
    background: #0d1117; border: 1px solid #21262d; border-radius: 3px;
    padding: 0.6rem 0.9rem; margin: 0.4rem 0;
}
.log-line b { color: #f0a500; }

.stButton > button {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; font-weight: 500;
    letter-spacing: 0.05em; text-transform: uppercase; background: #f0a500;
    color: #0d1117; border: none; border-radius: 4px; padding: 0.45rem 1.1rem;
    transition: all 0.15s ease;
}
.stButton > button:hover { background: #d4920a; transform: translateY(-1px); }

.stTabs [data-baseweb="tab-list"] { background: #161b22; border-bottom: 1px solid #21262d; }
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    letter-spacing: 0.05em; color: #8b949e;
}
.stTabs [aria-selected="true"] {
    color: #f0a500 !important; border-bottom-color: #f0a500 !important;
}
hr { border-color: #21262d; margin: 1.2rem 0; }

/* Sidebar: Solar QC en Amarillo, etiquetas en Blanco */
[data-testid="stSidebar"] h3 { color: #f0a500 !important; font-family: 'IBM Plex Mono', monospace; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #ffffff !important; }
[data-testid="stSidebar"] .st-eb { color: #ffffff !important; }
[data-testid="stSidebar"] input { color: #0d1117 !important; }

</style>
""", unsafe_allow_html=True)

# ─── Constantes ───────────────────────────────────────────────────────────────

Gs = 1361.0
BG, BG2, GRID, AMBER, BLUE, GREEN, RED, MUTED = (
    "#0d1117", "#161b22", "#21262d",
    "#f0a500", "#58a6ff", "#3fb950", "#f85149", "#8b949e"
)
BASE_LAYOUT = dict(
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(family="IBM Plex Mono, monospace", color=MUTED, size=11),
    xaxis=dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID),
    yaxis=dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID),
    margin=dict(l=60, r=20, t=50, b=50),
)

# ─── Geometría solar ──────────────────────────────────────────────────────────

def calcular_geometria_solar(fechas: pd.DatetimeIndex, lat: float, lon: float, utc_offset: float) -> pd.DataFrame:
    doy   = fechas.dayofyear.values
    N     = np.where(fechas.is_leap_year, 366, 365)
    gamma = 2 * np.pi * (doy - 1) / N

    Fn = (1.000110
          + 0.034221 * np.cos(gamma) + 0.001280 * np.sin(gamma)
          + 0.000719 * np.cos(2*gamma) + 0.000077 * np.sin(2*gamma))
    decl = (0.006918
            - 0.399912 * np.cos(gamma) + 0.070257 * np.sin(gamma)
            - 0.006758 * np.cos(2*gamma) + 0.000907 * np.sin(2*gamma)
            - 0.002697 * np.cos(3*gamma) + 0.001480 * np.sin(3*gamma))
    E = 229.18 * (0.000075
                  + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
                  - 0.014615 * np.cos(2*gamma) - 0.040890 * np.sin(2*gamma))

    lon_ref  = utc_offset * 15.0
    hora_UTC = fechas.hour + fechas.minute / 60.0
    Ts       = hora_UTC + (lon - lon_ref) / 15.0 + E / 60.0
    w        = np.pi * ((Ts / 12.0) - 1.0)
    lat_rad  = np.radians(lat)
    CZ       = np.sin(decl)*np.sin(lat_rad) + np.cos(decl)*np.cos(lat_rad)*np.cos(w)
    alt_sol  = np.arcsin(np.clip(CZ, -1, 1))

    sin_sza = np.sin(np.arccos(np.clip(CZ, -1, 1)))
    with np.errstate(divide='ignore', invalid='ignore'):
        cos_az = np.where(
            sin_sza > 1e-6,
            (np.sin(decl) - CZ * np.sin(lat_rad)) / (sin_sza * np.cos(lat_rad)),
            0.0,
        )
    azimutal = np.sign(w) * np.abs(np.arccos(np.clip(cos_az, -1, 1)))

    return pd.DataFrame(
        {"CZ": CZ, "Fn": Fn, "altura_solar": alt_sol, "azimutal": azimutal},
        index=fechas,
    )


def calcular_kt(ghi: pd.Series, geo: pd.DataFrame) -> pd.Series:
    denom = Gs * geo["Fn"] * geo["CZ"]
    kt    = np.where(geo["CZ"] > 0, ghi.values / denom, np.nan)
    return pd.Series(kt, index=ghi.index, name="kt")


# ─── Sistema de flags ─────────────────────────────────────────────────────────

def inicializar_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega las columnas de flags al DataFrame. Todas en 0 (válido)."""
    df = df.copy()
    for col in ["flag_1", "flag_2", "flag_3"]:
        if col not in df.columns:
            df[col] = 0
    df["flag_qc"] = 0
    return df


def actualizar_flag_qc(df: pd.DataFrame) -> pd.DataFrame:
    """flag_qc = OR lógico de flag_1, flag_2, flag_3."""
    df["flag_qc"] = ((df["flag_1"] | df["flag_2"] | df["flag_3"]) > 0).astype(int)
    return df


def resumen_flags(df: pd.DataFrame) -> dict:
    n_total   = len(df)
    n_f1      = int(df["flag_1"].sum())
    n_f2      = int(df["flag_2"].sum())
    n_f3      = int(df["flag_3"].sum())
    n_qc      = int(df["flag_qc"].sum())
    n_validos = n_total - n_qc
    return dict(
        n_total=n_total, n_validos=n_validos, n_descartados=n_qc,
        n_f1=n_f1, n_f2=n_f2, n_f3=n_f3,
    )


# ─── Gráficos ─────────────────────────────────────────────────────────────────

def fig_serie(df: pd.DataFrame, titulo: str, año: int = None) -> go.Figure:
    ghi_h = df["GHI"].resample("1h").mean()
    cs_h  = df["GHI_CS"].resample("1h").mean() if "GHI_CS" in df.columns else None

    fig = go.Figure()
    if cs_h is not None:
        fig.add_trace(go.Scatter(
            x=cs_h.index, y=cs_h.values, name="Cielo claro",
            line=dict(color=AMBER, width=1, dash="dot"), opacity=0.55,
        ))
    fig.add_trace(go.Scatter(
        x=ghi_h.index, y=ghi_h.values, name="GHI medido",
        line=dict(color=BLUE, width=0.9), opacity=0.9,
    ))

    xaxis_cfg = {**BASE_LAYOUT["xaxis"],
                 "rangeslider": dict(visible=True, bgcolor=BG2, thickness=0.06)}

    updatemenus = []
    if año is not None:
        meses   = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        buttons = [dict(label="Año completo", method="relayout",
                        args=[{"xaxis.range": [f"{año}-01-01", f"{año}-12-31"]}])]
        for m, nm in enumerate(meses, 1):
            ini = pd.Timestamp(año, m, 1)
            fin = ini + pd.offsets.MonthEnd(1)
            buttons.append(dict(
                label=nm, method="relayout",
                args=[{"xaxis.range": [str(ini.date()), str(fin.date())]}],
            ))
        updatemenus = [dict(
            type="buttons", direction="right", x=0.0, y=1.14, xanchor="left",
            bgcolor=BG2, bordercolor=GRID, font=dict(color=MUTED, size=10),
            buttons=buttons,
        )]

    # Aplicamos primero la base
    fig.update_layout(BASE_LAYOUT)
    
    # Luego aplicamos lo que sobreescribe o añade información
    fig.update_layout(
        title=dict(text=titulo, font=dict(color="#e6edf3", size=12)),
        xaxis_title="Fecha", 
        yaxis_title="GHI (W m⁻²)",
        legend=dict(bgcolor=BG2, bordercolor=GRID, borderwidth=1),
        height=370, 
        xaxis=xaxis_cfg, # Ahora no hay conflicto
        updatemenus=updatemenus,
    )
    return fig


def fig_diagrama_solar(df_yr: pd.DataFrame, año: int, semestre: int) -> go.Figure:
    mask  = (df_yr.index.month <= 6) if semestre == 1 else (df_yr.index.month >= 7)
    label = "Enero–junio" if semestre == 1 else "Julio–diciembre"
    
    # 1. Filtro y limpieza de datos
    d = df_yr[mask & (df_yr["CZ"] > 0)].dropna(subset=["kt", "azimutal", "altura_solar"]).copy()

    if d.empty:
        fig = go.Figure()
        fig.update_layout(BASE_LAYOUT, height=430)
        return fig

    # 2. Tu lógica de ordenamiento: oscuros primero, claros encima
    # Esto asegura que los puntos de mayor irradiancia no queden tapados
    d = d.sort_values("kt", ascending=True)

    az  = np.degrees(d["azimutal"].values)
    alt = np.degrees(d["altura_solar"].values)
    kt  = d["kt"].values

    # 3. Definición de la escala YlOrBr invertida (similar a Matplotlib)
    # Usamos una interpolación que va de marrón oscuro a amarillo claro
    yl_or_br_rev = [
        [0.0, "#662506"], # Marrón oscuro (kt bajo/sombras)
        [0.2, "#993404"],
        [0.4, "#cc4c02"],
        [0.6, "#ec7014"],
        [0.8, "#fe9929"],
        [1.0, "#ffffd4"]  # Amarillo muy claro (kt alto)
    ]

    fig = go.Figure(go.Scattergl(
        x=az, y=alt, mode="markers",
        marker=dict(
            color=kt,
            colorscale=yl_or_br_rev,
            cmin=0.1, cmax=1.0, # Límites de tu código original
            size=2.2,           # 's' de tu código
            opacity=1,
            colorbar=dict(
                title=dict(text="kt (adim.)", font=dict(size=11)),
                thickness=15,
                len=0.9
            ),
        ),
        hovertemplate="az: %{x:.1f}°<br>alt: %{y:.1f}°<br>kt: %{marker.color:.3f}<extra></extra>",
    ))

def fig_diagrama_solar(df_yr, año, semestre):
    # Filtro estricto para evitar ValueErrors en Scattergl
    mask = (df_yr.index.month <= 6) if semestre == 1 else (df_yr.index.month >= 7)
    d = df_yr[mask & (df_yr["CZ"] > 0)].dropna(subset=["kt", "azimutal", "altura_solar"]).copy()
    
    if d.empty:
        return go.Figure().update_layout(BASE_LAYOUT, title="Sin datos")

    # Estilo tesis: Ordenar para resaltar sombras
    d = d.sort_values("kt", ascending=True)
    
    fig = go.Figure(go.Scattergl(
        x=np.degrees(d["azimutal"]), y=np.degrees(d["altura_solar"]),
        mode="markers",
        marker=dict(
            color=d["kt"], cmin=0.1, cmax=1.0, size=2.2,
            colorscale=[[0, "#662506"], [0.5, "#ec7014"], [1, "#ffffd4"]], # YlOrBr rev
            colorbar=dict(title=dict(text="kt", font=dict(size=10)))
        )
    ))
    fig.update_layout(BASE_LAYOUT)
    fig.update_layout(xaxis=dict(autorange="reversed"), height=430) # Eje invertido
    return fig

    

    # 4. Ajustes de Layout para imitar Matplotlib[cite: 1]
    alt_max_real = alt.max() if len(alt) > 0 else 85
    
    fig.update_layout(BASE_LAYOUT)
    fig.update_layout(
        title=dict(text=f"{label} {año}", font=dict(color="#e6edf3", size=13)),
        xaxis=dict(
            title="Azimut solar (°)",
            autorange="reversed", # EQUIVALENTE A ax.invert_xaxis()[cite: 1]
            gridcolor="rgba(128, 128, 128, 0.2)"
        ),
        yaxis=dict(
            title="Altitud solar (°)",
            range=[0, min(90, alt_max_real + 5)], # Límite dinámico[cite: 1]
            gridcolor="rgba(128, 128, 128, 0.2)"
        ),
        height=430,
        margin=dict(t=60, b=60, l=80, r=20)
    )
    
    return fig

def fig_kt_2d(df_yr: pd.DataFrame, año: int) -> go.Figure:
    # 1. Preparación de datos (reproduciendo tu lógica de plot_kt_2d)
    dfy = df_yr.copy()
    is_leap = pd.Timestamp(year=año, month=12, day=31).is_leap_year
    ndays = 366 if is_leap else 365
    
    # Parámetros definidos en tu función original
    hora_min, hora_max = 5.0, 22.0
    vmin, vmax = 0.0, 1.2
    min_min, min_max = int(hora_min * 60), int(hora_max * 60)

    # Filtrar CZ <= 0 para no ensuciar el kt nocturno
    dfy.loc[dfy["CZ"] <= 0, "kt"] = np.nan
    
    doy_arr = dfy.index.dayofyear
    min_arr = dfy.index.hour * 60 + dfy.index.minute
    
    # 2. Creación de la grilla (Pivot Table)
    # Esto asegura que cada minuto y cada día tengan su celda, igual que en tu imshow
    kt_grid = (
        pd.DataFrame({"doy": doy_arr, "min": min_arr, "kt": dfy["kt"].values})
        .pivot_table(index="min", columns="doy", values="kt", aggfunc="mean")
        .reindex(index=np.arange(min_min, min_max + 1), columns=np.arange(1, ndays + 1))
    )

    # Límites reales de datos para el eje X (como en tu ax.set_xlim)
    finite_kt = dfy["kt"].dropna()
    doy_min_data = finite_kt.index.dayofyear.min() if not finite_kt.empty else 1
    doy_max_data = finite_kt.index.dayofyear.max() if not finite_kt.empty else ndays

    # Configuración de etiquetas de tiempo (cada 120 min)
    yticks_vals = np.arange(min_min, min_max + 1, 120)
    yticks_text = [f"{m//60:02d}:{m%60:02d}" for m in yticks_vals]

    # 3. Creación del gráfico con Heatmap[cite: 1]
    fig = go.Figure(go.Heatmap(
        z=kt_grid.values,
        x=kt_grid.columns.values,
        y=kt_grid.index.values,
        colorscale='magma', # Tu escala de color original[cite: 1]
        zmin=vmin, zmax=vmax,
        colorbar=dict(
            title=dict(text="kt (adim.)", font=dict(size=11)),
            thickness=15,
            len=0.9
        ),
        hovertemplate="Día: %{x}<br>Minuto: %{y}<br>kt: %{z:.3f}<extra></extra>"
    ))

    # 4. Ajustes de Layout[cite: 1]
    fig.update_layout(BASE_LAYOUT)
    fig.update_layout(
        title=dict(text=f"Mapa de kt — {año}", font=dict(size=13)),
        xaxis=dict(
            title=f"Día del año (1–{ndays})",
            range=[doy_min_data, doy_max_data],
            tickvals=np.arange(1, ndays + 1, 30), # Ticks cada 30 días[cite: 1]
            gridcolor="rgba(128, 128, 128, 0.2)"
        ),
        yaxis=dict(
            title="Hora (hh:mm)",
            tickvals=yticks_vals,
            ticktext=yticks_text,
            gridcolor="rgba(128, 128, 128, 0.2)"
        ),
        height=450,
        margin=dict(t=60, b=60, l=80, r=20)
    )

    return fig


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🌞 Solar QC")
        variable = st.radio("Variable", ["GHI", "DHI", "DNI", "PAR"], index=0)
        if variable != "GHI":
            st.warning(f"Módulo **{variable}** en desarrollo.")
        st.divider()
        st.markdown("### Estación")
        nombre = st.text_input("Nombre", value="Mi Estación")
        lat    = st.number_input("Latitud (°)", value=-34.58, format="%.4f")
        lon    = st.number_input("Longitud (°)", value=-58.48, format="%.4f")
        alt    = st.number_input("Altitud (m s.n.m.)", value=15, step=1)
        utc    = st.number_input("UTC offset", value=-3, step=1, min_value=-12, max_value=14)
        st.divider()
        st.caption("Solar QC · v0.3 · Etapa 1")
    return variable, nombre, lat, lon, alt, utc


# ─── Panel de flags por año ───────────────────────────────────────────────────

def render_flags_anuales(año: int, df_yr: pd.DataFrame) -> pd.DataFrame:
    """
    Configuración de flags: 
    1. Explicación general
    2. FLAG_1: Inspección visual (Manual)
    3. FLAG_2: Altura solar (Auto/Ajustable)
    4. FLAG_3: Índice kt (Físico)
    """
    # ─── 1. EXPLICACIÓN INICIAL ──────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-badge">Flags</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">'
        'Activar un flag <b>no elimina</b> los datos — los marca con 1 en la columna correspondiente. '
        'El campo <code>flag_qc</code> consolida todos los flags. '
        'Podés descargar el CSV completo y filtrar por <code>flag_qc == 0</code> para quedarte solo con los datos válidos.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Leyenda de convenio (BSRN)
    st.markdown(
        '<div class="flag-legend">'
        'Convenio <b>BSRN</b>: &nbsp; <code>0</code> = válido &nbsp;·&nbsp; <code>1</code> = descartado<br>'
        '<code>flag_1</code> Inspección visual &nbsp;·&nbsp; '
        '<code>flag_2</code> Altura solar &nbsp;·&nbsp; '
        '<code>flag_3</code> Índice kt > 1.35'
        '</div>',
        unsafe_allow_html=True,
    )

    df_out = df_yr.copy()

    # ─── 2. FLAG_1: INSPECCIÓN VISUAL (MANUAL) ──────────────────────────
    st.markdown(
        '<div class="filter-box">'
        '<div class="filter-box-title">FLAG_1 — INSPECCIÓN VISUAL (MANUAL)</div>'
        'Filtro derivado de la selección manual con la herramienta Lasso/Box en los gráficos superiores. '
        'Ideal para eliminar sombras de obstáculos conocidos.'
        '</div>',
        unsafe_allow_html=True,
    )
    
    # Mapeo de la selección manual al FLAG_1
    df_out["flag_1"] = 0
    df_out.loc[df_out.index.isin(st.session_state["manual_flags"]), "flag_1"] = 1

    if st.button(f"Limpiar inspección visual de {año}", key=f"clear_{año}"):
        st.session_state["manual_flags"] = {t for t in st.session_state["manual_flags"] if t.year != año}
        st.rerun()

    # ─── 3. FLAG_2: ALTURA SOLAR MÍNIMA ──────────────────────────────────
    st.markdown(
        '<div class="filter-box">'
        '<div class="filter-box-title">FLAG_2 — Altura solar mínima</div>'
        'Registros con el Sol muy cerca del horizonte; la incertidumbre suele ser más alta.'
        '<div class="filter-box-ref">'
        'Ref.: Alonso-Suárez, R. et al. (2024) '
        '<i>Recomendaciones y Buenas Prácticas para la Medición y Registro de la Radiación Solar en Territorio.</i>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    
    col_f2_check, col_f2_num = st.columns([3, 1])
    with col_f2_check:
        st.markdown("<br>", unsafe_allow_html=True)
        apply_f2 = st.checkbox(f"Activar flag_2 [{año}]", key=f"f2_check_{año}")
    with col_f2_num:
        limite_altura = st.number_input("Límite (°)", 0.0, 25.0, 7.0, key=f"f2_val_{año}")

    df_out["flag_2"] = np.where(apply_f2 & (df_out["altura_solar"] < np.radians(limite_altura)), 1, 0)

    # ─── 4. FLAG_3: ÍNDICE DE CLARIDAD kt ───────────────────────────────
    st.markdown(
        '<div class="filter-box">'
        '<div class="filter-box-title">FLAG_3 — Índice de claridad kt > 1.35</div>'
        'Suele indicar reflexiones especulares o fallas del sensor.'
        '<div class="filter-box-ref">'
        'Ref. 1: Geuder, N. et al. (2015) <a href="https://doi.org/10.1016/j.egypro.2015.03.205" target="_blank">DOI</a><br>'
        'Ref. 2: Gueymard, C. A. (2017) <a href="https://doi.org/10.1016/j.solener.2017.05.004" target="_blank">DOI</a>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    apply_f3 = st.checkbox(f"Activar flag_3 — kt > 1.35 [{año}]", key=f"f3_check_{año}")
    df_out["flag_3"] = np.where(apply_f3 & (df_out["kt"] > 1.35), 1, 0)

    # Actualizar flag_qc consolidado
    df_out = actualizar_flag_qc(df_out)

    # Resumen visual al final de la sección
    r = resumen_flags(df_out)
    pct_desc = 100 * r["n_descartados"] / r["n_total"] if r["n_total"] > 0 else 0
    st.markdown(
        f'<div class="flag-summary">'
        f'<b>Resumen {año}</b> — {r["n_total"]:,} registros<br>'
        f'&nbsp;&nbsp;flag_1 (Visual): <b>{r["n_f1"]:,}</b> &nbsp;·&nbsp; '
        f'flag_2 (Altura): <b>{r["n_f2"]:,}</b> &nbsp;·&nbsp; '
        f'flag_3 (kt): <b>{r["n_f3"]:,}</b><br>'
        f'<br>'
        f'&nbsp;&nbsp;flag_qc = 0 <span class="ok">✓ válidos</span>: <b>{r["n_validos"]:,}</b> &nbsp;·&nbsp; '
        f'flag_qc = 1 <span class="disc">✗ descartados</span>: <b>{r["n_descartados"]:,}</b> ({pct_desc:.1f} %)'
        f'</div>',
        unsafe_allow_html=True,
    )

    return df_out


# ─── App principal ────────────────────────────────────────────────────────────

def main():
    st.markdown('<div class="solar-title">🌞 Solar QC</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="solar-sub">Control de calidad de series de irradiancia solar — '
        'GHI · DHI · DNI · PAR</div>',
        unsafe_allow_html=True,
    )

    variable, nombre, lat, lon, alt, utc = render_sidebar()

    if variable != "GHI":
        st.info(f"El módulo **{variable}** está en desarrollo. Seleccioná **GHI** para continuar.")
        return

    st.divider()

    # ── Paso 1: Carga ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-badge">Paso 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Cargá tu archivo CSV</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Resolución minutal. Cualquier nombre de columnas — '
        'las mapeás en el paso siguiente.</div>',
        unsafe_allow_html=True,
    )

    with st.expander("¿Cómo debe ser el archivo?"):
        st.markdown("""
**Columnas mínimas:** fecha/hora · GHI · modelo cielo claro (opcional)

**Valores faltantes aceptados:** vacío · `NaN` · `-9999`

**Ejemplo:**
```
datetime,ghi_wm2,clear_sky
2020-06-15 06:00,0.0,0.0
2020-06-15 06:01,1.2,0.8
2020-06-15 06:02,3.5,2.1
```
""")

    uploaded = st.file_uploader("Archivo CSV", type=["csv"], label_visibility="collapsed")

    if uploaded is None:
        st.markdown(
            '<div style="text-align:center;padding:3rem 0;color:#8b949e;'
            'font-family:\'IBM Plex Mono\',monospace;font-size:0.82rem;">'
            '↑ cargá un CSV para comenzar</div>',
            unsafe_allow_html=True,
        )
        return

    df_raw = None
    for sep in [",", ";"]:
        try:
            _df = pd.read_csv(uploaded, sep=sep)
            if _df.shape[1] >= 2:
                df_raw = _df
                break
        except Exception:
            pass
    if df_raw is None:
        st.error("No se pudo leer el archivo. Verificá separador coma o punto y coma.")
        return

    st.success(f"✓ {uploaded.name} — {df_raw.shape[0]:,} filas · {df_raw.shape[1]} columnas")
    st.divider()

    # ── Paso 2: Mapeo ──────────────────────────────────────────────────────────
    if "manual_flags" not in st.session_state:
        st.session_state["manual_flags"] = set() # Guardaremos los timestamps marcados
    st.markdown('<div class="section-badge">Paso 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Mapeá las columnas</div>', unsafe_allow_html=True)

    cols = list(df_raw.columns)
    c1, c2, c3 = st.columns(3)
    with c1:
        col_dt  = st.selectbox("📅 Fecha y hora", cols, index=0)
    with c2:
        col_ghi = st.selectbox("☀ GHI (W m⁻²)", cols, index=min(1, len(cols)-1))
    with c3:
        col_cs  = st.selectbox("🔵 Modelo cielo claro (opcional)", ["— ninguna —"] + cols, index=0)
    col_cs = None if col_cs == "— ninguna —" else col_cs

    st.divider()

    # ── Procesamiento base (sin filtros, sin flags) ────────────────────────────
    with st.spinner("Calculando geometría solar…"):
        try:
            df = pd.DataFrame()
            df["GHI"] = pd.to_numeric(df_raw[col_ghi], errors="coerce")
            if col_cs:
                df["GHI_CS"] = pd.to_numeric(df_raw[col_cs], errors="coerce")
            fechas = pd.to_datetime(df_raw[col_dt], dayfirst=True, errors="coerce")
            df.index = fechas
            df = df[~df.index.isna()].sort_index()
            df = df[~df.index.duplicated(keep="first")]
            df.replace(-9999, np.nan, inplace=True)

            geo = calcular_geometria_solar(df.index, lat, lon, utc)
            df["CZ"]           = geo["CZ"].values
            df["Fn"]           = geo["Fn"].values
            df["altura_solar"] = geo["altura_solar"].values
            df["azimutal"]     = geo["azimutal"].values
            df["kt"]           = calcular_kt(df["GHI"], geo).values
            df.loc[df["CZ"] <= 0, "GHI"] = 0.0

            # Inicializar flags en 0
            df = inicializar_flags(df)

        except Exception as e:
            st.error(f"Error al procesar los datos: {e}")
            st.exception(e)
            return

    años    = sorted(df.index.year.unique())
    n_total = len(df)

    # Métricas globales
    st.markdown(
        f'<div class="metric-row">'
        f'<div class="metric-card"><div class="metric-label">Registros totales</div>'
        f'<div class="metric-value">{n_total:,}</div>'
        f'<div class="metric-sub">sin flags aplicados</div></div>'
        f'<div class="metric-card"><div class="metric-label">Período</div>'
        f'<div class="metric-value">{años[0]}–{años[-1]}</div>'
        f'<div class="metric-sub">{len(años)} año(s)</div></div>'
        f'<div class="metric-card"><div class="metric-label">Estación</div>'
        f'<div class="metric-value" style="font-size:1rem;padding-top:0.35rem">{nombre}</div>'
        f'<div class="metric-sub">{lat:.3f}° · {lon:.3f}°</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Paso 3: Serie global cruda ─────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="section-badge">Paso 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Serie completa — datos crudos</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Sin ningún flag. Rangeslider para zoom temporal.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        fig_serie(df, f"Serie completa — {nombre} (sin flags)"),
        use_container_width=True,
    )

    # ── Paso 4: Análisis anual ─────────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="section-badge">Paso 4</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Análisis anual</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">'
        'Un tab por año. Serie con zoom por mes → diagrama solar por semestre → '
        'kt 2D → flags opcionales al final de cada año.'
        '</div>',
        unsafe_allow_html=True,
    )

    if "dfs_flagged" not in st.session_state:
        st.session_state["dfs_flagged"] = {}

    tabs = st.tabs([str(a) for a in años])

    for tab, año in zip(tabs, años):
        with tab:
            df_yr = df[df.index.year == año].copy()
            n_yr  = int((df_yr["GHI"] > 0).sum())

            st.markdown(
                f'<div class="log-line">Año <b>{año}</b> · '
                f'<b>{len(df_yr):,}</b> registros totales · '
                f'<b>{n_yr:,}</b> con GHI &gt; 0 · sin flags</div>',
                unsafe_allow_html=True,
            )

            # Serie anual con zoom por mes
            st.plotly_chart(
                fig_serie(df_yr, f"{año} — GHI (sin flags)", año=año),
                use_container_width=True,
            )
            st.caption("Botones superiores: zoom rápido por mes. Rangeslider: zoom libre.")

            # Diagramas solares con SELECCIÓN ACTIVA
            col_s1, col_s2 = st.columns(2)
            
            # --- Semestre 1 ---
            with col_s1:
                fig1 = fig_diagrama_solar(df_yr, año, 1)
                sel1 = st.plotly_chart(fig1, on_select="rerun", key=f"sel1_{año}", use_container_width=True)
                
                # Si seleccionas puntos, los agregamos a la lista negra
                if sel1 and sel1["selection"]["point_indices"]:
                    # Necesitamos el mismo DF ordenado que usa el gráfico para mapear índices
                    d_plot = df_yr[(df_yr.index.month <= 6) & (df_yr["CZ"] > 0)].dropna(subset=["kt", "azimutal", "altura_solar"]).sort_values("kt")
                    puntos = d_plot.index[sel1["selection"]["point_indices"]]
                    st.session_state["manual_flags"].update(puntos)

            # --- Semestre 2 ---
            with col_s2:
                fig2 = fig_diagrama_solar(df_yr, año, 2)
                sel2 = st.plotly_chart(fig2, on_select="rerun", key=f"sel2_{año}", use_container_width=True)
                
                if sel2 and sel2["selection"]["point_indices"]:
                    d_plot = df_yr[(df_yr.index.month >= 7) & (df_yr["CZ"] > 0)].dropna(subset=["kt", "azimutal", "altura_solar"]).sort_values("kt")
                    puntos = d_plot.index[sel2["selection"]["point_indices"]]
                    st.session_state["manual_flags"].update(puntos)

            # kt 2D
            st.plotly_chart(fig_kt_2d(df_yr, año), use_container_width=True)
            st.caption(
                "Promedio de kt por hora y día del año. "
            )

            # Flags opcionales
            df_yr_flagged = render_flags_anuales(año, df_yr)
            st.session_state["dfs_flagged"][año] = df_yr_flagged

    # ── Descarga ───────────────────────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="section-badge">Exportar</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Descargar dataset con flags</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">'
        'El CSV incluye <b>todos los datos originales</b> más las columnas '
        '<code>flag_1</code>, <code>flag_2</code>, <code>flag_3</code>, <code>flag_qc</code>. '
        'Filtrá por <code>flag_qc == 0</code> para quedarte con los datos válidos.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Consolidar todos los años
    if st.session_state.get("dfs_flagged"):
        df_final = pd.concat(st.session_state["dfs_flagged"].values()).sort_index()
    else:
        df_final = df.copy()

    # ── Resumen global de flags (Final de main) ───────────────────────────────
    r_global = resumen_flags(df_final)
    pct = 100 * r_global["n_descartados"] / r_global["n_total"] if r_global["n_total"] > 0 else 0
    
    st.markdown(
        f'<div class="flag-summary">'
        f'<b>Resumen global del dataset</b> — {r_global["n_total"]:,} registros totales<br>'
        f'&nbsp;&nbsp;flag_1 (Inspección Visual): <b>{r_global["n_f1"]:,}</b> marcados<br>'
        f'&nbsp;&nbsp;flag_2 (Altura Solar): <b>{r_global["n_f2"]:,}</b> marcados<br>'
        f'&nbsp;&nbsp;flag_3 (Índice kt > 1.35): <b>{r_global["n_f3"]:,}</b> marcados<br>'
        f'<br>'
        f'&nbsp;&nbsp;flag_qc = 0 <span class="ok">✓ Válidos</span>: <b>{r_global["n_validos"]:,}</b>'
        f' &nbsp;·&nbsp; '
        f'flag_qc = 1 <span class="disc">✗ Descartados</span>: <b>{r_global["n_descartados"]:,}</b>'
        f' ({pct:.1f} %)'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.download_button(
        label="⬇ Descargar CSV con flags",
        data=df_final.to_csv().encode("utf-8"),
        file_name=f"{nombre.lower().replace(' ', '_')}_flags.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()

# %%
