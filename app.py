import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, date
import subprocess, tempfile, os

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Contadeus — Revisor Tributario",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  .main{background:#F8FAFC;}
  .block-container{padding-top:1.5rem;}
  .hdr{background:linear-gradient(135deg,#1B2A8C,#2563EB);
       padding:22px 28px;border-radius:12px;margin-bottom:20px;color:#fff;}
  .hdr h1{margin:0;font-size:1.7rem;font-weight:700;}
  .hdr p{margin:4px 0 0;opacity:.85;font-size:.92rem;}
  .kpi{background:#fff;border-radius:10px;padding:14px 16px;text-align:center;
       border:1px solid #E5E7EB;box-shadow:0 1px 4px rgba(0,0,0,.06);}
  .kpi .n{font-size:1.9rem;font-weight:700;}
  .kpi .l{font-size:.75rem;color:#6B7280;margin-top:2px;}
  .red{color:#DC2626;}.grn{color:#16A34A;}.amb{color:#D97706;}.blu{color:#1B2A8C;}
  .box-r{background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;
         padding:10px 14px;margin:6px 0;font-size:.86rem;line-height:1.6;}
  .box-a{background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;
         padding:10px 14px;margin:6px 0;font-size:.86rem;line-height:1.6;}
  .box-g{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
         padding:10px 14px;margin:6px 0;font-size:.86rem;line-height:1.6;}
  .box-b{background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;
         padding:10px 14px;margin:6px 0;font-size:.86rem;line-height:1.6;}
  .tag{display:inline-block;padding:2px 8px;border-radius:20px;
       font-size:.75rem;font-weight:600;margin-right:4px;}
  .tag-r{background:#FEE2E2;color:#991B1B;}
  .tag-a{background:#FEF3C7;color:#92400E;}
  .tag-g{background:#D1FAE5;color:#065F46;}
  .tag-b{background:#EEF2FF;color:#1B2A8C;}
  .div{height:1px;background:#E5E7EB;margin:18px 0;}
  .emp-badge{background:#EEF2FF;border:1.5px solid #1B2A8C;color:#1B2A8C;
             padding:5px 14px;border-radius:20px;font-weight:600;
             font-size:.88rem;display:inline-block;margin-bottom:12px;}
  .anio-banner{background:#374151;color:#fff;padding:6px 14px;
               border-radius:6px;font-weight:600;font-size:.85rem;
               margin:14px 0 6px;display:inline-block;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES TRIBUTARIAS
# ══════════════════════════════════════════════════════════════════════════════
UIT_POR_ANIO  = {2023: 4950.0, 2024: 5150.0, 2025: 5350.0, 2026: 5500.0, 2027: 5500.0}
TIM_DIARIO    = 0.0004   # 0.04% diario — actualizar si SUNAT cambia
CODIGOS_CON_MULTA = {"3052", "3042", "3022", "5310"}  # Retenciones → multa 5% UIT

NOMBRE_TRIBUTO = {
    "1011": "IGV",
    "3031": "Renta 3ra (General)",
    "3111": "Renta RER (1.5%)",
    "3121": "Renta MYPE (1%)",
    "3038": "ITAN",
    "3052": "Renta 5ta Categoría",
    "3042": "Renta 4ta Categoría",
    "3022": "Renta 2da Categoría",
    "5210": "EsSalud",
    "5310": "ONP",
    "8021": "Fraccionamiento Art.36",
}

MESES = {
    1:"ENERO", 2:"FEBRERO", 3:"MARZO", 4:"ABRIL",
    5:"MAYO",  6:"JUNIO",   7:"JULIO", 8:"AGOSTO",
    9:"SETIEMBRE", 10:"OCTUBRE", 11:"NOVIEMBRE", 12:"DICIEMBRE"
}

# Cronograma SUNAT completo — índice 0-9 = dígito RUC, índice 10 = buenos contrib.
CRONOGRAMA = {
    2024: {
        1:[15,16,19,19,20,20,21,21,22,22,23],2:[15,16,18,18,19,19,20,20,21,21,22],
        3:[15,18,19,19,20,20,21,21,22,22,25],4:[15,16,17,17,18,18,19,19,22,22,23],
        5:[14,15,16,16,17,17,20,20,21,21,22],6:[14,17,18,18,19,19,20,20,21,21,24],
        7:[15,16,17,17,18,18,19,19,22,22,23],8:[14,15,16,16,19,19,20,20,21,21,22],
        9:[13,16,17,17,18,18,19,19,20,20,23],10:[15,16,17,17,18,18,21,21,22,22,23],
        11:[14,15,18,18,19,19,20,20,21,21,22],12:[15,16,17,17,20,20,21,21,22,22,23],
    },
    2025: {
        1:[17,18,19,19,20,20,21,21,24,24,25],2:[17,18,19,19,20,20,21,21,24,24,25],
        3:[18,19,20,20,21,21,24,24,25,25,26],4:[17,22,23,23,24,24,25,25,28,28,29],
        5:[15,16,19,19,20,20,21,21,22,22,23],6:[16,17,18,18,19,19,20,20,23,23,24],
        7:[15,16,17,17,18,18,21,21,22,22,23],8:[18,19,20,20,21,21,22,22,25,25,26],
        9:[15,16,17,17,18,18,19,19,22,22,23],10:[15,16,17,17,20,20,21,21,22,22,23],
        11:[17,18,19,19,20,20,21,21,24,24,25],12:[15,16,17,17,18,18,19,19,22,22,23],
    },
    2026: {
        1:[16,17,18,18,19,19,20,20,23,23,24],2:[16,17,18,18,19,19,20,20,23,23,24],
        3:[17,20,21,21,22,22,23,23,24,24,27],4:[18,19,20,20,21,21,22,22,25,25,26],
        5:[15,16,17,17,18,18,19,19,22,22,23],6:[15,16,17,17,20,20,21,21,22,22,24],
        7:[18,19,20,20,21,21,24,24,25,25,26],8:[15,16,17,17,18,18,21,21,22,22,23],
        9:[16,19,20,20,21,21,22,22,23,23,26],10:[16,17,18,18,19,19,20,20,23,23,24],
        11:[17,18,21,21,22,22,23,23,24,24,28],12:[18,19,20,20,21,21,22,22,25,25,26],
    },
}

def fecha_venc_normal(anio: int, mes: int, digito: int) -> date:
    cron = CRONOGRAMA.get(anio, CRONOGRAMA[2026])
    dias = cron.get(mes, [28]*11)
    dia  = dias[min(digito, 10)]
    mes_v, anio_v = mes + 1, anio
    if mes_v > 12: mes_v, anio_v = 1, anio + 1
    try:    return date(anio_v, mes_v, dia)
    except: return date(anio_v, mes_v, 28)

def fecha_venc_igv_justo(anio: int, mes: int, digito: int) -> date:
    """IGV Justo = vencimiento del período SIGUIENTE según cronograma."""
    mes2, a2 = mes + 1, anio
    if mes2 > 12: mes2, a2 = 1, anio + 1
    return fecha_venc_normal(a2, mes2, digito)

def multa_5pct(anio: int) -> float:
    return UIT_POR_ANIO.get(anio, 5500.0) * 0.05

def calc_tim(importe: float, dias: int) -> float:
    return round(importe * TIM_DIARIO * max(dias, 0), 2)

# ══════════════════════════════════════════════════════════════════════════════
# PARSEO EXTRACTO SUNAT — formato real confirmado
# ══════════════════════════════════════════════════════════════════════════════
# Formato real del extracto SUNAT:
# Filas 0-11: encabezado (RUC, nombre, período, etc.)
# Fila 12: encabezados de columnas
# PERIODO | N°FORM | N°ORDEN | DESCRIPCION | BANCO | FECHA_PAGO | COD_TRIBUTO | DESC_TRIBUTO | IMPORTE

def xls_a_csv(archivo_bytes: bytes, nombre: str) -> str | None:
    """Convierte XLS a CSV usando LibreOffice (necesario para .xls binario)."""
    try:
        with tempfile.NamedTemporaryFile(suffix='.xls', delete=False) as f:
            f.write(archivo_bytes)
            tmp_xls = f.name
        tmp_dir = tempfile.mkdtemp()
        result = subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'csv',
             tmp_xls, '--outdir', tmp_dir],
            capture_output=True, text=True, timeout=30
        )
        csv_files = [f for f in os.listdir(tmp_dir) if f.endswith('.csv')]
        if csv_files:
            csv_path = os.path.join(tmp_dir, csv_files[0])
            with open(csv_path, 'r', encoding='latin-1') as f:
                contenido = f.read()
            os.unlink(tmp_xls)
            return contenido
    except Exception as e:
        st.warning(f"Conversión XLS: {e}")
    return None

def parsear_sunat(archivo_bytes: bytes, nombre_archivo: str) -> pd.DataFrame:
    """
    Parsea el extracto real de SUNAT.
    Formato confirmado con extracto real TDD:
    Col 1: PERIODO (202601), Col 2: N°FORM, Col 3: N°ORDEN,
    Col 4: DESCRIPCION, Col 5: BANCO, Col 6: FECHA_PAGO,
    Col 7: COD_TRIBUTO, Col 8: DESC_TRIBUTO, Col 9: IMPORTE
    """
    ext = nombre_archivo.lower().split('.')[-1]

    # ── Intentar leer según extensión ────────────────────────────────────────
    df_raw = None

    if ext == 'xlsx':
        try:
            df_raw = pd.read_csv(BytesIO(archivo_bytes), header=None, dtype=str,
                                 encoding='latin-1', sep=None, engine='python')
        except:
            pass
        if df_raw is None:
            try:
                df_raw = pd.read_excel(BytesIO(archivo_bytes), header=None, dtype=str)
            except: pass

    elif ext == 'xls':
        # XLS binario → convertir con LibreOffice
        csv_str = xls_a_csv(archivo_bytes, nombre_archivo)
        if csv_str:
            from io import StringIO
            df_raw = pd.read_csv(StringIO(csv_str), header=None, dtype=str)
        if df_raw is None:
            # Fallback: intentar leer como CSV directamente
            try:
                df_raw = pd.read_csv(BytesIO(archivo_bytes), header=None,
                                     dtype=str, encoding='latin-1',
                                     sep=None, engine='python')
            except: pass

    elif ext == 'csv':
        for enc in ['latin-1', 'utf-8', 'cp1252']:
            try:
                df_raw = pd.read_csv(BytesIO(archivo_bytes), header=None,
                                     dtype=str, encoding=enc,
                                     sep=None, engine='python')
                break
            except: pass

    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    # ── Detectar fila de encabezados ─────────────────────────────────────────
    # El extracto SUNAT tiene: PERIODO | N°FORMULARIO | N°ORDEN | DESCRIPCION...
    header_row = None
    for i, row in df_raw.iterrows():
        vals = [str(v).lower().strip() for v in row if pd.notna(v) and str(v) != 'nan']
        joined = ' '.join(vals)
        if ('periodo' in joined and 'orden' in joined) or \
           ('periodo' in joined and 'tributo' in joined):
            header_row = i
            break

    if header_row is None:
        # Si no encuentra encabezado, asumir fila 12 (formato estándar SUNAT)
        header_row = 12

    # ── Asignar columnas según estructura real SUNAT ──────────────────────────
    ncols = len(df_raw.columns)
    # Mapear por posición (más confiable que por nombre para el extracto SUNAT)
    # Formato: _, PERIODO, N_FORM, N_ORDEN, DESCRIPCION, BANCO, FECHA_PAGO,
    #          COD_TRIBUTO, DESC_TRIBUTO, IMPORTE, _
    if ncols >= 10:
        col_names = ['_0','PERIODO','N_FORM','N_ORDEN','DESCRIPCION',
                     'BANCO','FECHA_PAGO','COD_TRIBUTO','DESC_TRIBUTO','IMPORTE']
        col_names += [f'_x{i}' for i in range(ncols - len(col_names))]
    else:
        # Formato alternativo — detectar por contenido
        col_names = [f'c{i}' for i in range(ncols)]

    df = df_raw.iloc[header_row+1:].copy()
    df.columns = col_names[:ncols]
    df = df.dropna(how='all').reset_index(drop=True)

    # ── Limpiar y filtrar ─────────────────────────────────────────────────────
    # Solo filas con PERIODO válido (6 dígitos numéricos como 202601)
    if 'PERIODO' in df.columns:
        df = df[df['PERIODO'].astype(str).str.match(r'^\s*\d{6}\s*$')]

    # Limpiar importe
    if 'IMPORTE' in df.columns:
        df['IMPORTE'] = pd.to_numeric(
            df['IMPORTE'].astype(str).str.replace(',','').str.strip(),
            errors='coerce'
        ).fillna(0)

    # Parsear fecha
    if 'FECHA_PAGO' in df.columns:
        df['FECHA_PAGO'] = pd.to_datetime(
            df['FECHA_PAGO'], dayfirst=True, errors='coerce'
        )

    # Solo pagos reales (importe > 0 y código tributo válido)
    if 'IMPORTE' in df.columns:
        df = df[df['IMPORTE'] > 0]
    if 'COD_TRIBUTO' in df.columns:
        df = df[df['COD_TRIBUTO'].astype(str).str.strip().isin(NOMBRE_TRIBUTO.keys())]

    return df.reset_index(drop=True)

def combinar_extractos(archivos) -> tuple[pd.DataFrame, list[str]]:
    """Combina múltiples extractos eliminando duplicados por N° de orden."""
    dfs, nombres = [], []
    for arch in archivos:
        arch.seek(0)
        b = arch.read()
        df = parsear_sunat(b, arch.name)
        if not df.empty:
            df['_archivo'] = arch.name
            dfs.append(df)
            nombres.append(arch.name)
        else:
            st.warning(f"⚠️  No se pudieron leer datos de: **{arch.name}**")

    if not dfs:
        return pd.DataFrame(), nombres

    combinado = pd.concat(dfs, ignore_index=True)

    # Deduplicar por N° de orden
    if 'N_ORDEN' in combinado.columns:
        antes = len(combinado)
        combinado = combinado.drop_duplicates(subset=['N_ORDEN'], keep='first')
        dup = antes - len(combinado)
        if dup > 0:
            st.info(f"ℹ️  Se eliminaron {dup} pagos duplicados entre extractos.")

    return combinado.reset_index(drop=True), nombres

# ══════════════════════════════════════════════════════════════════════════════
# LECTURA GOOGLE SHEET
# ══════════════════════════════════════════════════════════════════════════════
def extraer_sheet_id(url: str) -> str:
    m = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
    return m.group(1) if m else ''

def leer_sheet(sheet_id: str) -> dict:
    """Lee todas las pestañas posibles del Google Sheet público."""
    base = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet='
    pestanas = []
    for anio in [2023, 2024, 2025, 2026, 2027]:
        for t in ['IGV', 'RENTA', 'VENTAS']:
            pestanas.append(f'{t} {anio}')
    pestanas += [
        'ESSALUD', 'ONP', 'RENTA_5TA', 'RENTA_4TA',
        'ITAN', 'FRACCIONAMIENTOS', 'AFP_MANUAL', 'SIS_MANUAL',
        'REPORTE DE IMPUESTOS',  # formato alternativo
    ]
    sheets = {}
    for p in pestanas:
        try:
            url_csv = base + p.replace(' ', '%20')
            df = pd.read_csv(url_csv, header=None, dtype=str)
            if not df.empty and len(df) > 1:
                sheets[p] = df
        except: pass
    return sheets

def buscar_en_sheet(sheets: dict, pestana: str, mes_nom: str,
                    importe: float, n_orden: str) -> bool:
    """Verifica si un pago ya aparece en el sheet."""
    if pestana not in sheets:
        return False
    df  = sheets[pestana]
    txt = df.to_string().upper()

    # 1. Buscar por N° de orden (más confiable)
    if n_orden and str(n_orden).strip() not in ['', 'nan'] and len(str(n_orden)) > 4:
        if str(n_orden).strip() in txt:
            return True

    # 2. Buscar por mes + importe en la misma fila
    imp1 = f'{importe:.0f}'
    imp2 = f'{importe:,.0f}'
    for _, row in df.iterrows():
        rs = ' '.join(str(v) for v in row
                      if pd.notna(v) and str(v) != 'nan').upper()
        if mes_nom.upper() in rs and (imp1 in rs or imp2 in rs):
            return True
    return False

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
def analizar(extracto: pd.DataFrame, sheets: dict,
             digito: int, igv_justo: bool, hoy: date) -> list:
    resultados = []
    vistos = set()

    for _, fila in extracto.iterrows():
        periodo = str(fila.get('PERIODO', '')).strip()
        if len(periodo) < 6: continue
        try:
            anio, mes = int(periodo[:4]), int(periodo[4:6])
            if not (2020 <= anio <= 2030 and 1 <= mes <= 12): continue
        except: continue

        codigo  = str(fila.get('COD_TRIBUTO', '')).strip()
        if codigo not in NOMBRE_TRIBUTO: continue

        importe = float(fila.get('IMPORTE', 0) or 0)
        if importe <= 0: continue

        n_orden = str(fila.get('N_ORDEN', '')).strip()

        # Deduplicar
        clave = (codigo, anio, mes, round(importe), n_orden[:8])
        if clave in vistos: continue
        vistos.add(clave)

        nombre  = NOMBRE_TRIBUTO[codigo]
        mes_nom = MESES.get(mes, str(mes))
        fp_raw  = fila.get('FECHA_PAGO')
        fecha_pago = None
        if pd.notna(fp_raw):
            try: fecha_pago = pd.Timestamp(fp_raw).date()
            except: pass

        # ── Fechas de vencimiento ────────────────────────────────────────────
        if codigo == '1011' and igv_justo:
            venc      = fecha_venc_igv_justo(anio, mes, digito)
            tipo_venc = 'IGV Justo'
        else:
            venc      = fecha_venc_normal(anio, mes, digito)
            tipo_venc = 'Normal'

        # ── Pestaña del reporte donde debe estar ─────────────────────────────
        if   codigo == '1011': pestana = f'IGV {anio}'
        elif codigo == '5210': pestana = 'ESSALUD'
        elif codigo == '5310': pestana = 'ONP'
        elif codigo == '3052': pestana = 'RENTA_5TA'
        elif codigo == '3042': pestana = 'RENTA_4TA'
        elif codigo == '3038': pestana = 'ITAN'
        elif codigo == '8021': pestana = 'FRACCIONAMIENTOS'
        else:                  pestana = f'RENTA {anio}'

        # También buscar en "REPORTE DE IMPUESTOS" (formato alternativo)
        pestanas_buscar = [pestana, 'REPORTE DE IMPUESTOS']

        ya_reg = any(
            buscar_en_sheet(sheets, p, mes_nom, importe, n_orden)
            for p in pestanas_buscar
        )

        # ── Atraso y multas ──────────────────────────────────────────────────
        dias_tarde   = max((fecha_pago - venc).days, 0) if fecha_pago and venc else 0
        pagado_tarde = dias_tarde > 0
        con_multa    = codigo in CODIGOS_CON_MULTA
        tim_calc     = calc_tim(importe, dias_tarde) if pagado_tarde else 0.0
        mult_calc    = multa_5pct(anio) if (pagado_tarde and con_multa) else 0.0

        # ── Estado final ─────────────────────────────────────────────────────
        if not ya_reg:
            estado = 'NO_REGISTRADO'
        elif pagado_tarde:
            estado = 'REGISTRADO_TARDE'
        else:
            estado = 'OK'

        instruccion = (
            f'Pestaña "{pestana}" → fila {mes_nom} → '
            f'columna "SE PAGÓ" → S/ {importe:,.2f}'
        )
        if fecha_pago:
            instruccion += f' · Fecha: {fecha_pago.strftime("%d/%m/%Y")}'

        resultados.append({
            'estado': estado, 'codigo': codigo, 'nombre': nombre,
            'periodo': f'{mes_nom}-{anio}', 'mes': mes_nom, 'anio': anio,
            'importe': importe, 'fecha_pago': fecha_pago,
            'fecha_venc': venc, 'tipo_venc': tipo_venc,
            'dias_tarde': dias_tarde, 'pagado_tarde': pagado_tarde,
            'con_multa': con_multa, 'tim': tim_calc, 'multa': mult_calc,
            'n_orden': n_orden, 'pestana': pestana,
            'instruccion': instruccion, 'ya_registrado': ya_reg,
        })

    # ── Detectar declarados sin pagar desde el Sheet ─────────────────────────
    if sheets:
        vistos_cod = {(r['codigo'], r['mes'], r['anio']) for r in resultados}
        mapa_pestana_cod = {}
        for anio in [2024, 2025, 2026]:
            mapa_pestana_cod[f'IGV {anio}']   = ('1011', anio)
            mapa_pestana_cod[f'RENTA {anio}'] = ('3121', anio)
        mapa_pestana_cod.update({
            'ESSALUD': ('5210', 2026), 'ONP': ('5310', 2026),
            'RENTA_5TA': ('3052', 2026), 'RENTA_4TA': ('3042', 2026),
        })

        for pestana, (cod_est, anio_p) in mapa_pestana_cod.items():
            if pestana not in sheets: continue
            df_s = sheets[pestana]
            for _, row in df_s.iterrows():
                rs = ' '.join(
                    str(v) for v in row
                    if pd.notna(v) and str(v) not in ['nan','']
                ).upper()
                for mes_n, mes_nm in MESES.items():
                    if mes_nm not in rs: continue
                    if (cod_est, mes_nm, anio_p) in vistos_cod: continue
                    nums = [float(n.replace(',',''))
                            for n in re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b', rs)
                            if float(n.replace(',','')) > 50]
                    if len(nums) < 2: continue
                    saldo = nums[-1]
                    if saldo <= 0: continue
                    venc = fecha_venc_normal(anio_p, mes_n, digito)
                    if venc >= hoy: continue   # Aún no vence — no alertar
                    dias_v = (hoy - venc).days
                    con_m  = cod_est in CODIGOS_CON_MULTA
                    resultados.append({
                        'estado': 'VENCIDO_SIN_PAGAR',
                        'codigo': cod_est,
                        'nombre': NOMBRE_TRIBUTO.get(cod_est, ''),
                        'periodo': f'{mes_nm}-{anio_p}',
                        'mes': mes_nm, 'anio': anio_p,
                        'importe': saldo, 'fecha_pago': None,
                        'fecha_venc': venc, 'tipo_venc': 'Normal',
                        'dias_tarde': dias_v, 'pagado_tarde': False,
                        'con_multa': con_m,
                        'tim': calc_tim(saldo, dias_v),
                        'multa': multa_5pct(anio_p) if con_m else 0,
                        'n_orden': '', 'pestana': pestana,
                        'instruccion': (
                            f'Saldo pendiente S/ {saldo:,.0f} — '
                            f'venció hace {dias_v} días — '
                            f'pagar impuesto + intereses en SUNAT'
                        ),
                        'ya_registrado': True,
                    })
                    vistos_cod.add((cod_est, mes_nm, anio_p))

    return resultados

# ══════════════════════════════════════════════════════════════════════════════
# GENERADOR EXCEL
# ══════════════════════════════════════════════════════════════════════════════
def generar_excel(empresa: str, ruc: str, resultados: list,
                  extracto: pd.DataFrame, archivos_n: list) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        hoy_s    = datetime.now().strftime('%d/%m/%Y %H:%M')
        vencidos  = [r for r in resultados if r['estado'] == 'VENCIDO_SIN_PAGAR']
        pendientes= [r for r in resultados if r['estado'] == 'NO_REGISTRADO']
        con_atraso= [r for r in resultados if r['estado'] == 'REGISTRADO_TARDE']
        ok_items  = [r for r in resultados if r['estado'] == 'OK']
        t_multas  = sum(r['multa'] + r['tim'] for r in resultados)
        m_pend    = sum(r['importe'] for r in pendientes + vencidos)
        anios     = sorted({r['anio'] for r in resultados})

        # RESUMEN
        pd.DataFrame({
            'Campo': ['Empresa','RUC','Fecha análisis','Extractos procesados',
                      'Años cubiertos','Total pagos extracto',
                      'Vencidos sin pagar','Pendientes de registrar',
                      'Pagados con atraso','Al día',
                      'Monto pendiente/vencido S/','Multas + TIM estimado S/'],
            'Valor': [empresa, ruc, hoy_s, ', '.join(archivos_n),
                      ', '.join(str(a) for a in anios),
                      len(resultados), len(vencidos), len(pendientes),
                      len(con_atraso), len(ok_items),
                      f'{m_pend:,.2f}', f'{t_multas:,.2f}']
        }).to_excel(w, sheet_name='RESUMEN', index=False)

        def fila(r, extra={}):
            d = {'Año': r['anio'], 'Tributo': r['nombre'],
                 'Período': r['periodo'], 'Importe S/': r['importe'],
                 'Fecha pago': r['fecha_pago'].strftime('%d/%m/%Y') if r['fecha_pago'] else '',
                 'N° Orden': r['n_orden']}
            d.update(extra)
            return d

        if vencidos:
            pd.DataFrame([fila(r, {
                'Vencimiento': r['fecha_venc'].strftime('%d/%m/%Y') if r['fecha_venc'] else '',
                'Días vencido': r['dias_tarde'],
                'TIM estimado S/': r['tim'],
                'Multa S/': r['multa'] if r['multa'] else 'No aplica',
                'Total regularizar S/': r['importe'] + r['tim'] + r['multa'],
                'Acción': r['instruccion'],
            }) for r in sorted(vencidos, key=lambda x: x['dias_tarde'], reverse=True)]
            ).to_excel(w, sheet_name='🔴 VENCIDOS SIN PAGAR', index=False)

        if pendientes:
            pd.DataFrame([fila(r, {
                'Pagado tarde': 'SÍ' if r['pagado_tarde'] else 'No',
                'Días tarde': r['dias_tarde'],
                'Multa S/': r['multa'] if r['multa'] else '',
                'TIM S/': r['tim'] if r['tim'] else '',
                'Dónde registrar': r['instruccion'],
            }) for r in pendientes]
            ).to_excel(w, sheet_name='🟡 REGISTRAR EN REPORTE', index=False)

        if con_atraso:
            pd.DataFrame([fila(r, {
                'Vencimiento': r['fecha_venc'].strftime('%d/%m/%Y') if r['fecha_venc'] else '',
                'Días tarde': r['dias_tarde'],
                'TIM S/': r['tim'],
                'Multa S/': r['multa'] if r['multa'] else 'No aplica',
                'Genera multa 5% UIT': 'SÍ' if r['con_multa'] else 'No',
                'Tipo vencimiento': r['tipo_venc'],
            }) for r in con_atraso]
            ).to_excel(w, sheet_name='🟠 PAGADOS CON ATRASO', index=False)

        if ok_items:
            pd.DataFrame([fila(r, {'Estado': '✓ A tiempo y registrado'})
                         for r in ok_items]
            ).to_excel(w, sheet_name='✅ AL DÍA', index=False)

        extracto.to_excel(w, sheet_name='EXTRACTO COMBINADO', index=False)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hdr">
  <h1>📊 Contadeus — Revisor Tributario</h1>
  <p>Multi-año · Multi-extracto · Detecta vencidos, pendientes y multas automáticamente</p>
</div>
""", unsafe_allow_html=True)

# Estado sesión
for k, v in [('listo', False), ('resultados', []), ('empresa', ''),
             ('ruc', ''), ('extracto_df', pd.DataFrame()),
             ('sheets', {}), ('archivos_n', [])]:
    if k not in st.session_state:
        st.session_state[k] = v

HOY = date.today()

# ── PANTALLA RESULTADOS ────────────────────────────────────────────────────
if st.session_state.listo and st.session_state.resultados:
    empresa    = st.session_state.empresa
    ruc        = st.session_state.ruc
    resultados = st.session_state.resultados
    archivos_n = st.session_state.archivos_n

    vencidos   = [r for r in resultados if r['estado'] == 'VENCIDO_SIN_PAGAR']
    pendientes = [r for r in resultados if r['estado'] == 'NO_REGISTRADO']
    con_atraso = [r for r in resultados if r['estado'] == 'REGISTRADO_TARDE']
    ok_items   = [r for r in resultados if r['estado'] == 'OK']
    t_multas   = sum(r['multa'] + r['tim'] for r in resultados)
    anios      = sorted({r['anio'] for r in resultados}, reverse=True)

    st.markdown(
        f'<div class="emp-badge">🏢 {empresa} &nbsp;·&nbsp; RUC {ruc} &nbsp;·&nbsp;'
        f' Años: {" · ".join(str(a) for a in anios)} &nbsp;·&nbsp;'
        f' {len(archivos_n)} extracto(s)</div>',
        unsafe_allow_html=True
    )

    # KPIs
    for col, num, lbl, color in zip(
        st.columns(5),
        [len(resultados), len(vencidos), len(pendientes),
         len(con_atraso), f'S/ {t_multas:,.0f}'],
        ['Total en extracto', 'Vencidos sin pagar', 'Sin registrar',
         'Pagados con atraso', 'Multas + TIM'],
        ['blu', 'red', 'amb', 'amb', 'red']
    ):
        with col:
            st.markdown(
                f'<div class="kpi"><div class="n {color}">{num}</div>'
                f'<div class="l">{lbl}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="div"></div>', unsafe_allow_html=True)

    # Resultados agrupados por año
    for anio in anios:
        v_a = [r for r in vencidos    if r['anio'] == anio]
        p_a = [r for r in pendientes  if r['anio'] == anio]
        c_a = [r for r in con_atraso  if r['anio'] == anio]
        o_a = [r for r in ok_items    if r['anio'] == anio]
        if not any([v_a, p_a, c_a, o_a]): continue

        st.markdown(f'<div class="anio-banner">📅 AÑO {anio}</div>',
                    unsafe_allow_html=True)

        # Vencidos sin pagar
        if v_a:
            st.markdown(f'**🔴 Vencidos sin pagar — {anio}**')
            for r in sorted(v_a, key=lambda x: x['dias_tarde'], reverse=True):
                costo   = r['importe'] + r['tim'] + r['multa']
                m_tag   = (f'<span class="tag tag-r">Multa S/ {r["multa"]:,.0f}</span>'
                           if r['multa'] else '')
                st.markdown(f"""<div class="box-r">
                    <strong>🚨 {r['nombre']} — {r['periodo']}</strong><br>
                    💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp;
                    Venció: <strong>{r['fecha_venc'].strftime('%d/%m/%Y') if r['fecha_venc'] else 'N/D'}</strong>
                    &nbsp;·&nbsp; <strong>{r['dias_tarde']} días vencido</strong><br>
                    {m_tag}<span class="tag tag-a">TIM S/ {r['tim']:,.2f}</span>
                    <span class="tag tag-r">Total regularizar: S/ {costo:,.2f}</span><br>
                    <span style="color:#991B1B">▶ {r['instruccion']}</span>
                </div>""", unsafe_allow_html=True)

        # Sin registrar
        if p_a:
            st.markdown(f'**🟡 Pagados pero no registrados en el reporte — {anio}**')
            for r in p_a:
                box = 'box-r' if r['pagado_tarde'] else 'box-a'
                atr = ''
                if r['pagado_tarde']:
                    m_lbl = f'Multa S/ {r["multa"]:,.0f}' if r['con_multa'] else 'Solo TIM'
                    atr = (f'<br><span class="tag tag-r">{m_lbl}</span>'
                           f' <span class="tag tag-a">TIM S/ {r["tim"]:,.2f}</span>'
                           f' — {r["dias_tarde"]} días tarde')
                st.markdown(f"""<div class="{box}">
                    <strong>📌 {r['nombre']} — {r['periodo']}</strong><br>
                    💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp;
                    Pagado: {r['fecha_pago'].strftime('%d/%m/%Y') if r['fecha_pago'] else 'N/D'}
                    {f'&nbsp;·&nbsp; N° {r["n_orden"]}' if r['n_orden'] else ''}
                    {atr}<br>
                    <span style="color:#92400E">▶ {r['instruccion']}</span>
                </div>""", unsafe_allow_html=True)

        # Pagados con atraso (registrados)
        if c_a:
            with st.expander(f'🟠 {len(c_a)} pagados con atraso — {anio}'):
                for r in c_a:
                    m_lbl = f'⚠️ Multa S/ {r["multa"]:,.0f}' if r['con_multa'] else 'Solo TIM'
                    st.markdown(f"""<div class="box-a">
                        <strong>{r['nombre']} — {r['periodo']}</strong>
                        &nbsp;·&nbsp; S/ {r['importe']:,.2f}
                        &nbsp;·&nbsp; {r['dias_tarde']} días tarde
                        &nbsp;·&nbsp; {m_lbl}
                        &nbsp;·&nbsp; TIM S/ {r['tim']:,.2f}
                        &nbsp;·&nbsp; ({r['tipo_venc']})
                    </div>""", unsafe_allow_html=True)

        # Al día
        if o_a:
            with st.expander(f'✅ {len(o_a)} al día — {anio}'):
                for r in o_a:
                    st.markdown(f"""<div class="box-g">
                        ✓ {r['nombre']} — {r['periodo']}
                        — S/ {r['importe']:,.2f}
                        — {r['fecha_pago'].strftime('%d/%m/%Y') if r['fecha_pago'] else ''}
                        — ({r['tipo_venc']})
                    </div>""", unsafe_allow_html=True)

    if not any([vencidos, pendientes, con_atraso]):
        st.markdown(
            '<div class="box-g">✅ <strong>Todo al día en todos los años.</strong> '
            'No hay pendientes ni vencidos.</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="div"></div>', unsafe_allow_html=True)

    # Botones
    col_dl, col_nx = st.columns(2)
    with col_dl:
        excel_b = generar_excel(empresa, ruc, resultados,
                                st.session_state.extracto_df, archivos_n)
        fname = (f'Reporte_{empresa[:20].replace(" ","_")}_'
                 f'{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx')
        st.download_button(
            '⬇️  Descargar reporte Excel completo',
            data=excel_b, file_name=fname,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True, type='primary'
        )
    with col_nx:
        if st.button('➡️  Analizar otra empresa', use_container_width=True):
            for k in ['listo','resultados','empresa','ruc',
                      'extracto_df','sheets','archivos_n']:
                st.session_state[k] = (
                    False if k == 'listo' else
                    [] if k in ['resultados','archivos_n'] else
                    pd.DataFrame() if k == 'extracto_df' else
                    {} if k == 'sheets' else ''
                )
            st.rerun()

    st.markdown(
        '<div class="box-b">💡 <strong>Descarga el reporte antes de pasar '
        'a otra empresa.</strong> Incluye todos los años: vencidos, '
        'pendientes, con atraso y al día.</div>',
        unsafe_allow_html=True
    )

# ── PANTALLA FORMULARIO ────────────────────────────────────────────────────
else:
    col_f, col_h = st.columns([3, 2])

    with col_f:
        st.markdown('### Datos de la empresa')

        c1, c2 = st.columns(2)
        with c1:
            empresa_inp = st.text_input(
                'Nombre de la empresa',
                placeholder='Ej: TDD INVERSIONES S.A.C.'
            )
        with c2:
            ruc_inp = st.text_input(
                'RUC (11 dígitos)',
                placeholder='Ej: 20613979779',
                help='Pega el RUC. El dígito y los vencimientos se calculan solos.'
            )

        digito_calc = None
        if ruc_inp and len(ruc_inp.strip()) == 11 and ruc_inp.strip().isdigit():
            digito_calc = int(ruc_inp.strip()[-1])
            st.markdown(
                f'<div class="box-b" style="font-size:.82rem;margin-top:2px;">'
                f'✓ Dígito RUC: <strong>{digito_calc}</strong> — '
                f'vencimientos calculados automáticamente</div>',
                unsafe_allow_html=True
            )
        elif ruc_inp:
            st.warning('El RUC debe tener exactamente 11 dígitos.')

        igv_justo_chk = st.checkbox(
            '✅ Esta empresa usa IGV Justo (Ley 30524)',
            value=True,
            help='El vencimiento del IGV será el del período SIGUIENTE según cronograma SUNAT.'
        )

        st.markdown('')
        st.markdown('### Link del Google Sheet del cliente')
        sheet_url = st.text_input(
            '', label_visibility='collapsed',
            placeholder='https://docs.google.com/spreadsheets/d/...',
            help='El Sheet debe estar compartido como "Cualquier persona con el link puede ver".'
        )

        st.markdown('')
        st.markdown('### Extractos SUNAT')
        st.caption(
            '📎 Puedes subir varios a la vez — 2024, 2025, 2026. '
            'El sistema los combina y elimina duplicados automáticamente.'
        )
        archivos = st.file_uploader(
            '', type=['xls', 'xlsx', 'csv'],
            accept_multiple_files=True,
            label_visibility='collapsed'
        )

        if archivos:
            st.markdown(
                f'<div class="box-g" style="font-size:.82rem;">'
                f'📎 {len(archivos)} archivo(s): '
                f'{" · ".join(a.name for a in archivos)}</div>',
                unsafe_allow_html=True
            )

        st.markdown('')
        if st.button('🔍  Analizar', type='primary', use_container_width=True):
            errores = []
            if not empresa_inp.strip():
                errores.append('Ingresa el nombre de la empresa.')
            if not ruc_inp.strip() or len(ruc_inp.strip()) != 11:
                errores.append('El RUC debe tener 11 dígitos.')
            if not sheet_url.strip():
                errores.append('Ingresa el link del Google Sheet.')
            if not archivos:
                errores.append('Sube al menos un extracto XLS de SUNAT.')
            for e in errores:
                st.error(e)

            if not errores and digito_calc is not None:
                sid = extraer_sheet_id(sheet_url)
                if not sid:
                    st.error('Link de Google Sheet no válido.')
                else:
                    with st.spinner('Leyendo Google Sheet del cliente...'):
                        sheets = leer_sheet(sid)
                        if not sheets:
                            st.warning(
                                'No se pudo leer el Sheet. Verifica que esté '
                                'compartido como "Cualquier persona con el link puede ver".'
                            )

                    with st.spinner(f'Procesando {len(archivos)} extracto(s)...'):
                        extracto_df, nombres = combinar_extractos(archivos)
                        if extracto_df.empty:
                            st.error(
                                'No se encontraron datos en los extractos. '
                                'Verifica que los archivos sean los correctos '
                                '(descargados de SUNAT → Mis Declaraciones y Pagos).'
                            )
                            st.stop()

                    with st.spinner('Analizando...'):
                        resultados = analizar(
                            extracto_df, sheets, digito_calc, igv_justo_chk, HOY
                        )

                    if not resultados:
                        st.info(
                            'No se encontraron pagos para analizar. '
                            'Verifica que el extracto tenga datos del período correcto.'
                        )
                    else:
                        st.session_state.update({
                            'listo': True,
                            'resultados': resultados,
                            'empresa': empresa_inp.strip(),
                            'ruc': ruc_inp.strip(),
                            'extracto_df': extracto_df,
                            'sheets': sheets,
                            'archivos_n': nombres,
                        })
                        st.rerun()

    with col_h:
        st.markdown("""<div class="box-b" style="margin-top:36px;">
            <strong>📋 Cómo usar</strong><br><br>
            <strong>1.</strong> Nombre de la empresa<br>
            <strong>2.</strong> Pega el RUC — la app calcula el dígito sola<br>
            <strong>3.</strong> Marca si usa IGV Justo<br>
            <strong>4.</strong> Pega el link del Google Sheet<br>
            <strong>5.</strong> Sube los extractos XLS de SUNAT<br>
            &nbsp;&nbsp;&nbsp;&nbsp;(puedes subir 2024 + 2025 + 2026 juntos)<br>
            <strong>6.</strong> Analizar → descargar → siguiente empresa
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="box-a" style="margin-top:10px;">
            <strong>⚠️ Tributos con multa 5% UIT (S/275)</strong><br>
            • ONP (5310)<br>
            • Renta 5ta Categoría (3052)<br>
            • Renta 4ta Categoría (3042)<br>
            • Renta 2da Categoría (3022)<br><br>
            Los demás: solo TIM (0.04%/día)<br>
            UIT: 2024=S/5,150 · 2025=S/5,350 · 2026=S/5,500
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="box-b" style="margin-top:10px;">
            <strong>📅 IGV Justo (Ley 30524)</strong><br>
            Vence el período <strong>siguiente</strong> según el 
            cronograma SUNAT y el dígito del RUC — no la fecha normal.
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="box-g" style="margin-top:10px;">
            <strong>🔒 Seguridad</strong><br>
            Esta app <strong>nunca modifica</strong> ningún Google Sheet.<br>
            Solo lee y compara. Tú decides qué actualizar.
        </div>""", unsafe_allow_html=True)

