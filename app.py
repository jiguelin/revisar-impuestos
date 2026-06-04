import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO
from datetime import datetime, date

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
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════
UIT_POR_ANIO      = {2023:4950.0, 2024:5150.0, 2025:5350.0, 2026:5500.0, 2027:5500.0}
TIM_DIARIO        = 0.0004
CODIGOS_CON_MULTA = {"3052","3042","3022","5310"}

NOMBRE_TRIBUTO = {
    "1011":"IGV",
    "3031":"Renta 3ra (General)",
    "3111":"Renta RER (1.5%)",
    "3121":"Renta MYPE (1%)",
    "3038":"ITAN",
    "3052":"Renta 5ta Categoría",
    "3042":"Renta 4ta Categoría",
    "3022":"Renta 2da Categoría",
    "5210":"EsSalud",
    "5310":"ONP",
    "8021":"Fraccionamiento Art.36",
}

MESES_NUM = {
    "ENERO":1,"FEBRERO":2,"MARZO":3,"ABRIL":4,"MAYO":5,"JUNIO":6,
    "JULIO":7,"AGOSTO":8,"SETIEMBRE":9,"SEPTIEMBRE":9,
    "OCTUBRE":10,"NOVIEMBRE":11,"DICIEMBRE":12
}

CRONOGRAMA = {
    2024:{1:[15,16,19,19,20,20,21,21,22,22,23],2:[15,16,18,18,19,19,20,20,21,21,22],
          3:[15,18,19,19,20,20,21,21,22,22,25],4:[15,16,17,17,18,18,19,19,22,22,23],
          5:[14,15,16,16,17,17,20,20,21,21,22],6:[14,17,18,18,19,19,20,20,21,21,24],
          7:[15,16,17,17,18,18,19,19,22,22,23],8:[14,15,16,16,19,19,20,20,21,21,22],
          9:[13,16,17,17,18,18,19,19,20,20,23],10:[15,16,17,17,18,18,21,21,22,22,23],
          11:[14,15,18,18,19,19,20,20,21,21,22],12:[15,16,17,17,20,20,21,21,22,22,23]},
    2025:{1:[17,18,19,19,20,20,21,21,24,24,25],2:[17,18,19,19,20,20,21,21,24,24,25],
          3:[18,19,20,20,21,21,24,24,25,25,26],4:[17,22,23,23,24,24,25,25,28,28,29],
          5:[15,16,19,19,20,20,21,21,22,22,23],6:[16,17,18,18,19,19,20,20,23,23,24],
          7:[15,16,17,17,18,18,21,21,22,22,23],8:[18,19,20,20,21,21,22,22,25,25,26],
          9:[15,16,17,17,18,18,19,19,22,22,23],10:[15,16,17,17,20,20,21,21,22,22,23],
          11:[17,18,19,19,20,20,21,21,24,24,25],12:[15,16,17,17,18,18,19,19,22,22,23]},
    2026:{1:[16,17,18,18,19,19,20,20,23,23,24],2:[16,17,18,18,19,19,20,20,23,23,24],
          3:[17,20,21,21,22,22,23,23,24,24,27],4:[18,19,20,20,21,21,22,22,25,25,26],
          5:[15,16,17,17,18,18,19,19,22,22,23],6:[15,16,17,17,20,20,21,21,22,22,24],
          7:[18,19,20,20,21,21,24,24,25,25,26],8:[15,16,17,17,18,18,21,21,22,22,23],
          9:[16,19,20,20,21,21,22,22,23,23,26],10:[16,17,18,18,19,19,20,20,23,23,24],
          11:[17,18,21,21,22,22,23,23,24,24,28],12:[18,19,20,20,21,21,22,22,25,25,26]},
}

def fecha_venc_normal(anio:int, mes:int, digito:int) -> date:
    cron = CRONOGRAMA.get(anio, CRONOGRAMA[2026])
    dias = cron.get(mes,[28]*11)
    dia  = dias[min(digito,10)]
    mv,av = mes+1,anio
    if mv>12: mv,av=1,anio+1
    try:    return date(av,mv,dia)
    except: return date(av,mv,28)

def fecha_venc_igv_justo(anio:int, mes:int, digito:int) -> date:
    m2,a2 = mes+1,anio
    if m2>12: m2,a2=1,anio+1
    return fecha_venc_normal(a2,m2,digito)

def multa_5pct(anio:int) -> float:
    return UIT_POR_ANIO.get(anio,5500.0)*0.05

def calc_tim(importe:float, dias:int) -> float:
    return round(importe*TIM_DIARIO*max(dias,0),2)

def limpiar_numero(s:str) -> float:
    """Convierte string de número peruano a float. Ej: '2,360' → 2360.0"""
    try:
        # Quitar paréntesis (negativos), signos, espacios
        s = re.sub(r'[()S/\s]','',str(s))
        # Formato peruano: coma como miles, punto como decimal
        # Si tiene coma y punto: "1,234.56" o "1.234,56"
        if ',' in s and '.' in s:
            if s.index(',') < s.index('.'):
                s = s.replace(',','')  # "1,234.56" → "1234.56"
            else:
                s = s.replace('.','').replace(',','.')  # "1.234,56" → "1234.56"
        elif ',' in s:
            # Solo coma: puede ser miles "2,360" o decimal "0,50"
            partes = s.split(',')
            if len(partes)==2 and len(partes[1]) in [2,3]:
                if len(partes[1])==3:
                    s = s.replace(',','')  # miles
                else:
                    s = s.replace(',','.')  # decimal
            else:
                s = s.replace(',','')
        return float(s) if s else 0.0
    except:
        return 0.0

# ══════════════════════════════════════════════════════════════════════════════
# PARSEO PDF SUNAT
# ══════════════════════════════════════════════════════════════════════════════
def parsear_pdf_sunat(pdf_bytes:bytes) -> pd.DataFrame:
    """Lee el PDF 'Reporte de Declaraciones y Pagos' de SUNAT."""
    filas = []
    CODIGOS = set(NOMBRE_TRIBUTO.keys())
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    if not table or len(table)<2: continue
                    header = [str(c or '').lower().replace('\n',' ')
                              for c in table[0]]
                    if not any('período' in h or 'periodo' in h for h in header):
                        continue
                    if not any('tributo' in h for h in header):
                        continue
                    for row in table[1:]:
                        if not row or len(row)<8: continue
                        vals = [str(v or '').strip().replace('\n',' ')
                                for v in row]
                        periodo   = vals[0]
                        n_orden   = vals[2]
                        fecha_str = vals[3]
                        cod_trib  = vals[5]
                        monto_str = vals[7]
                        if not re.match(r'^202[3-9]\d{2}$',periodo): continue
                        if cod_trib not in CODIGOS: continue
                        try:
                            importe = limpiar_numero(monto_str)
                        except: continue
                        if importe<=0: continue
                        fecha_pago=None
                        if re.match(r'\d{1,2}/\d{2}/\d{4}',fecha_str):
                            try:
                                fecha_pago=datetime.strptime(
                                    fecha_str.strip(),'%d/%m/%Y').date()
                            except: pass
                        filas.append({
                            'PERIODO':periodo,'N_ORDEN':n_orden,
                            'COD_TRIBUTO':cod_trib,'FECHA_PAGO':fecha_pago,
                            'IMPORTE':importe,
                        })
    except Exception as e:
        st.error(f"Error al leer el PDF: {e}")
        return pd.DataFrame()
    if not filas: return pd.DataFrame()
    df = pd.DataFrame(filas)
    df = df.drop_duplicates(subset=['N_ORDEN'],keep='first')
    return df.reset_index(drop=True)

def combinar_pdfs(archivos) -> tuple[pd.DataFrame, list[str]]:
    dfs, nombres = [], []
    for arch in archivos:
        arch.seek(0)
        df = parsear_pdf_sunat(arch.read())
        if not df.empty:
            df['_archivo']=arch.name
            dfs.append(df)
            nombres.append(arch.name)
        else:
            st.warning(f"⚠️ Sin datos en: **{arch.name}**")
    if not dfs: return pd.DataFrame(), nombres
    combinado = pd.concat(dfs,ignore_index=True)
    antes = len(combinado)
    combinado = combinado.drop_duplicates(subset=['N_ORDEN'],keep='first')
    dup = antes-len(combinado)
    if dup>0: st.info(f"ℹ️ {dup} pagos duplicados eliminados.")
    return combinado.reset_index(drop=True), nombres

# ══════════════════════════════════════════════════════════════════════════════
# LECTURA GOOGLE SHEET
# ══════════════════════════════════════════════════════════════════════════════
def extraer_sheet_id(url:str) -> str:
    m = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)',url)
    return m.group(1) if m else ''

def leer_sheet(sheet_id:str) -> dict:
    """Lee todas las pestañas posibles del Sheet."""
    base = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet='
    pestanas = []
    for a in [2023,2024,2025,2026,2027]:
        for t in ['IGV','RENTA','VENTAS']:
            pestanas.append(f'{t} {a}')
    pestanas += ['ESSALUD','ONP','RENTA_5TA','RENTA_4TA','ITAN',
                 'FRACCIONAMIENTOS','AFP_MANUAL','SIS_MANUAL',
                 'REPORTE DE IMPUESTOS']
    sheets = {}
    for p in pestanas:
        try:
            df = pd.read_csv(base+p.replace(' ','%20'),header=None,dtype=str)
            if not df.empty and len(df)>1:
                sheets[p]=df
        except: pass
    return sheets

def pago_ya_registrado(sheets:dict, pestana:str, mes_nom:str,
                        importe:float, n_orden:str) -> bool:
    """
    Verifica si un pago del PDF ya aparece registrado en el Sheet.
    Busca en la pestaña específica Y en 'REPORTE DE IMPUESTOS'.
    """
    buscar_en = [pestana, 'REPORTE DE IMPUESTOS']
    for p in buscar_en:
        if p not in sheets: continue
        df  = sheets[p]
        # Buscar por N° orden (más confiable)
        if n_orden and len(n_orden)>4:
            txt = df.to_string()
            if n_orden in txt: return True
        # Buscar por mes + importe en la misma fila
        imp1 = f'{importe:.0f}'
        imp2 = f'{importe:,.0f}'
        for _,row in df.iterrows():
            rs = ' '.join(str(v) for v in row
                         if pd.notna(v) and str(v)!='nan').upper()
            if mes_nom.upper() in rs and (imp1 in rs or imp2 in rs):
                return True
    return False

# ══════════════════════════════════════════════════════════════════════════════
# LEER SALDOS VENCIDOS DEL SHEET
# ══════════════════════════════════════════════════════════════════════════════
def leer_saldos_vencidos(sheets:dict, digito:int,
                          igv_justo:bool, hoy:date) -> list:
    """
    Lee el Sheet y detecta tributos declarados con saldo pendiente cuyo
    vencimiento ya pasó.
    
    REGLAS:
    1. Solo reporta tributos cuya SECCIÓN existe en el Sheet
       (no inventa ONP/R5ta si no hay sección para eso)
    2. Para IGV usa la fecha IGV Justo si está en el Sheet, sino calcula
    3. Solo si la fecha de vencimiento < hoy
    4. Un registro por (tributo, período) — sin duplicados
    """
    vencidos = []
    vistos   = set()

    # Pestaña a buscar según título del sheet
    # El Sheet de Contadeus tiene todo en "REPORTE DE IMPUESTOS"
    # o en pestañas separadas "IGV 2026", "RENTA 2026", etc.
    
    # Intentar pestaña "REPORTE DE IMPUESTOS" primero (formato Contadeus)
    sheet_texto = None
    if 'REPORTE DE IMPUESTOS' in sheets:
        df = sheets['REPORTE DE IMPUESTOS']
        # Convertir a texto plano para parsear secciones
        sheet_texto = '\n'.join(
            ','.join(str(v) if pd.notna(v) else '' for v in row)
            for _, row in df.iterrows()
        )
    
    if not sheet_texto:
        return vencidos  # Sin datos estructurados
    
    # Parsear secciones del Sheet
    # Cada sección tiene: TÍTULO → filas de MESES → TOTALES
    # Mapeo de palabras clave en títulos → código tributo
    TITULO_COD = [
        (r'IGV\b.*?(\d{4})',                '1011'),
        (r'RENTA.*?(\d{4})',                '3121'),  # MYPE/RER/General
        (r'ESSALUD.*?(\d{4})',              '5210'),
        (r'ONP.*?(\d{4})',                  '5310'),
        (r'RENTA.*?5TA|QUINTA.*?(\d{4})',   '3052'),
        (r'RENTA.*?4TA|CUARTA.*?(\d{4})',   '3042'),
    ]

    lineas = sheet_texto.split('\n')
    
    seccion_cod  = None
    seccion_anio = None
    
    for idx, linea in enumerate(lineas):
        l_upper = linea.upper().strip()
        if not l_upper: continue
        
        # ── Detectar título de sección ──────────────────────────────────────
        anio_en_linea = re.search(r'\b(20[23]\d)\b', linea)
        if anio_en_linea:
            anio_cand = int(anio_en_linea.group(1))
            for patron, cod in TITULO_COD:
                if re.search(patron, l_upper):
                    seccion_cod  = cod
                    seccion_anio = anio_cand
                    break
            continue
        
        if not seccion_cod or not seccion_anio:
            continue
        
        # ── Detectar fila de mes ─────────────────────────────────────────────
        mes_detectado = None
        for mes_nom, mes_num in MESES_NUM.items():
            # El mes puede estar al inicio de la celda
            celdas = [c.strip().upper() for c in linea.split(',')]
            for celda in celdas[:3]:  # solo primeras columnas
                if celda == mes_nom or celda.startswith(mes_nom+' '):
                    mes_detectado = (mes_nom, mes_num)
                    break
            if mes_detectado: break
        
        if not mes_detectado: continue
        mes_nom, mes_num = mes_detectado
        
        # Extraer todos los números de la fila
        celdas = linea.split(',')
        numeros = []
        fechas_igv = []
        for celda in celdas:
            c = celda.strip().strip('"').replace('"','')
            # Buscar fecha IGV Justo (formato DD/MM/YYYY)
            if re.match(r'\d{1,2}/\d{2}/\d{4}', c):
                try:
                    fechas_igv.append(datetime.strptime(c,'%d/%m/%Y').date())
                except: pass
            # Buscar números (ignorar negativos entre paréntesis = ya pagado)
            if re.match(r'^[\d,\.]+$', c) and len(c)>0:
                try:
                    v = limpiar_numero(c)
                    if 0 < v < 500_000:
                        numeros.append(v)
                except: pass
        
        # El PENDIENTE es el último número positivo de la fila
        # (las columnas son: IMPORTE, SE PAGÓ neg, SE COMP neg, INTERÉS, FECHA, PENDIENTE)
        if not numeros: continue
        saldo = numeros[-1]
        if saldo <= 0: continue
        
        # Deduplicar
        clave = (seccion_cod, mes_nom, seccion_anio)
        if clave in vistos: continue
        
        # ── Determinar fecha de vencimiento ──────────────────────────────────
        if seccion_cod == '1011' and igv_justo:
            # Usar fecha IGV Justo del Sheet si está disponible
            if fechas_igv:
                venc = fechas_igv[0]
            else:
                venc = fecha_venc_igv_justo(seccion_anio, mes_num, digito)
        else:
            venc = fecha_venc_normal(seccion_anio, mes_num, digito)
        
        # Solo reportar si ya venció
        if venc >= hoy: continue
        
        dias_v = (hoy - venc).days
        con_m  = seccion_cod in CODIGOS_CON_MULTA
        
        vistos.add(clave)
        vencidos.append({
            'estado':     'VENCIDO_SIN_PAGAR',
            'codigo':     seccion_cod,
            'nombre':     NOMBRE_TRIBUTO.get(seccion_cod,''),
            'periodo':    f'{mes_nom}-{seccion_anio}',
            'mes':        mes_nom,
            'anio':       seccion_anio,
            'importe':    saldo,
            'fecha_pago': None,
            'fecha_venc': venc,
            'tipo_venc':  'IGV Justo' if seccion_cod=='1011' and igv_justo else 'Normal',
            'dias_tarde': dias_v,
            'pagado_tarde':False,
            'con_multa':  con_m,
            'tim':        calc_tim(saldo, dias_v),
            'multa':      multa_5pct(seccion_anio) if con_m else 0,
            'n_orden':    '',
            'pestana':    f'IGV {seccion_anio}' if seccion_cod=='1011'
                          else f'RENTA {seccion_anio}' if seccion_cod in ['3121','3031','3111']
                          else 'ESSALUD' if seccion_cod=='5210'
                          else 'ONP',
            'instruccion': f'Saldo pendiente S/ {saldo:,.2f} — venció hace {dias_v} días',
            'ya_registrado': True,
        })
    
    return vencidos

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
def analizar(extracto:pd.DataFrame, sheets:dict,
             digito:int, igv_justo:bool, hoy:date) -> list:
    resultados = []
    vistos = set()

    # ── 1. Analizar pagos del PDF ────────────────────────────────────────────
    for _, fila in extracto.iterrows():
        periodo = str(fila.get('PERIODO','')).strip()
        if not re.match(r'^202[3-9]\d{2}$',periodo): continue
        anio,mes = int(periodo[:4]),int(periodo[4:6])

        codigo  = str(fila.get('COD_TRIBUTO','')).strip()
        if codigo not in NOMBRE_TRIBUTO: continue

        importe = float(fila.get('IMPORTE',0) or 0)
        if importe<=0: continue

        n_orden = str(fila.get('N_ORDEN','')).strip()
        clave   = (codigo,anio,mes,round(importe),n_orden[:8])
        if clave in vistos: continue
        vistos.add(clave)

        nombre  = NOMBRE_TRIBUTO[codigo]
        mes_nom = next((k for k,v in MESES_NUM.items() if v==mes and len(k)>4),
                       str(mes))
        fp      = fila.get('FECHA_PAGO')
        fecha_pago = fp if isinstance(fp,date) else None

        # Vencimientos
        if codigo=='1011' and igv_justo:
            venc      = fecha_venc_igv_justo(anio,mes,digito)
            tipo_venc = 'IGV Justo'
        else:
            venc      = fecha_venc_normal(anio,mes,digito)
            tipo_venc = 'Normal'

        # Pestaña del reporte
        if   codigo=='1011': pestana=f'IGV {anio}'
        elif codigo=='5210': pestana='ESSALUD'
        elif codigo=='5310': pestana='ONP'
        elif codigo=='3052': pestana='RENTA_5TA'
        elif codigo=='3042': pestana='RENTA_4TA'
        elif codigo=='3038': pestana='ITAN'
        elif codigo=='8021': pestana='FRACCIONAMIENTOS'
        else:                pestana=f'RENTA {anio}'

        ya_reg = pago_ya_registrado(sheets,pestana,mes_nom,importe,n_orden)

        dias_tarde   = max((fecha_pago-venc).days,0) if fecha_pago and venc else 0
        pagado_tarde = dias_tarde>0
        con_multa    = codigo in CODIGOS_CON_MULTA
        tim_calc     = calc_tim(importe,dias_tarde) if pagado_tarde else 0.0
        mult_calc    = multa_5pct(anio) if (pagado_tarde and con_multa) else 0.0

        if not ya_reg:     estado='NO_REGISTRADO'
        elif pagado_tarde: estado='REGISTRADO_TARDE'
        else:              estado='OK'

        instruccion = (f'Pestaña "{pestana}" → fila {mes_nom} → '
                       f'columna "SE PAGÓ" → S/ {importe:,.2f}')
        if fecha_pago:
            instruccion += f' · Fecha: {fecha_pago.strftime("%d/%m/%Y")}'

        resultados.append({
            'estado':estado,'codigo':codigo,'nombre':nombre,
            'periodo':f'{mes_nom}-{anio}','mes':mes_nom,'anio':anio,
            'importe':importe,'fecha_pago':fecha_pago,
            'fecha_venc':venc,'tipo_venc':tipo_venc,
            'dias_tarde':dias_tarde,'pagado_tarde':pagado_tarde,
            'con_multa':con_multa,'tim':tim_calc,'multa':mult_calc,
            'n_orden':n_orden,'pestana':pestana,
            'instruccion':instruccion,'ya_registrado':ya_reg,
        })

    # ── 2. Agregar vencidos sin pagar leídos del Sheet ───────────────────────
    # Solo si el Sheet tiene la pestaña "REPORTE DE IMPUESTOS"
    vencidos_sheet = leer_saldos_vencidos(sheets,digito,igv_justo,hoy)
    
    # Deduplicar: no agregar si ya está en resultados del PDF
    periodos_en_pdf = {(r['codigo'],r['mes'],r['anio'])
                       for r in resultados}
    
    for v in vencidos_sheet:
        clave_v = (v['codigo'],v['mes'],v['anio'])
        if clave_v not in periodos_en_pdf:
            resultados.append(v)

    return resultados

# ══════════════════════════════════════════════════════════════════════════════
# EXCEL DE REPORTE
# ══════════════════════════════════════════════════════════════════════════════
def generar_excel(empresa:str, ruc:str, resultados:list,
                  extracto:pd.DataFrame, archivos_n:list) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf,engine='openpyxl') as w:
        hoy_s     = datetime.now().strftime('%d/%m/%Y %H:%M')
        vencidos  = [r for r in resultados if r['estado']=='VENCIDO_SIN_PAGAR']
        pendientes= [r for r in resultados if r['estado']=='NO_REGISTRADO']
        con_atraso= [r for r in resultados if r['estado']=='REGISTRADO_TARDE']
        ok_items  = [r for r in resultados if r['estado']=='OK']
        t_multas  = sum(r['multa']+r['tim'] for r in resultados)
        m_pend    = sum(r['importe'] for r in pendientes+vencidos)
        anios     = sorted({r['anio'] for r in resultados})

        pd.DataFrame({'Campo':
            ['Empresa','RUC','Fecha análisis','PDFs procesados',
             'Años cubiertos','Total registros','Vencidos sin pagar',
             'Sin registrar','Pagados con atraso','Al día',
             'Monto pendiente/vencido S/','Multas + TIM estimado S/'],
            'Valor':[empresa,ruc,hoy_s,', '.join(archivos_n),
                     ', '.join(str(a) for a in anios),
                     len(resultados),len(vencidos),len(pendientes),
                     len(con_atraso),len(ok_items),
                     f'{m_pend:,.2f}',f'{t_multas:,.2f}']
        }).to_excel(w,sheet_name='RESUMEN',index=False)

        def fila(r,extra={}):
            d={'Año':r['anio'],'Tributo':r['nombre'],
               'Período':r['periodo'],'Importe S/':r['importe'],
               'Fecha pago':r['fecha_pago'].strftime('%d/%m/%Y')
                            if r['fecha_pago'] else '',
               'N° Orden':r['n_orden']}
            d.update(extra); return d

        if vencidos:
            pd.DataFrame([fila(r,{
                'Vencimiento':r['fecha_venc'].strftime('%d/%m/%Y') if r['fecha_venc'] else '',
                'Días vencido':r['dias_tarde'],
                'TIM estimado S/':r['tim'],
                'Multa S/':r['multa'] if r['multa'] else 'No aplica',
                'Total regularizar S/':r['importe']+r['tim']+r['multa'],
                'Acción':r['instruccion'],
            }) for r in sorted(vencidos,key=lambda x:x['dias_tarde'],reverse=True)]
            ).to_excel(w,sheet_name='🔴 VENCIDOS SIN PAGAR',index=False)

        if pendientes:
            pd.DataFrame([fila(r,{
                'Pagado tarde':'SÍ' if r['pagado_tarde'] else 'No',
                'Días tarde':r['dias_tarde'],
                'Multa S/':r['multa'] if r['multa'] else '',
                'TIM S/':r['tim'] if r['tim'] else '',
                'Dónde registrar':r['instruccion'],
            }) for r in pendientes]
            ).to_excel(w,sheet_name='🟡 REGISTRAR EN REPORTE',index=False)

        if con_atraso:
            pd.DataFrame([fila(r,{
                'Vencimiento':r['fecha_venc'].strftime('%d/%m/%Y') if r['fecha_venc'] else '',
                'Días tarde':r['dias_tarde'],
                'TIM S/':r['tim'],
                'Multa S/':r['multa'] if r['multa'] else 'No aplica',
                'Genera multa 5% UIT':'SÍ' if r['con_multa'] else 'No',
                'Tipo vencimiento':r['tipo_venc'],
            }) for r in con_atraso]
            ).to_excel(w,sheet_name='🟠 PAGADOS CON ATRASO',index=False)

        if ok_items:
            pd.DataFrame([fila(r,{'Estado':'✓ A tiempo y registrado'})
                         for r in ok_items]
            ).to_excel(w,sheet_name='✅ AL DÍA',index=False)

        extracto.to_excel(w,sheet_name='EXTRACTO PDF',index=False)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hdr">
  <h1>📊 Contadeus — Revisor Tributario</h1>
  <p>Sube el PDF de SUNAT · Detecta vencidos, pendientes de registro y multas automáticamente</p>
</div>
""", unsafe_allow_html=True)

for k,v in [('listo',False),('resultados',[]),('empresa',''),('ruc',''),
            ('extracto_df',pd.DataFrame()),('sheets',{}),('archivos_n',[])]:
    if k not in st.session_state: st.session_state[k]=v

HOY = date.today()

# ── RESULTADOS ─────────────────────────────────────────────────────────────
if st.session_state.listo and st.session_state.resultados:
    empresa    = st.session_state.empresa
    ruc        = st.session_state.ruc
    resultados = st.session_state.resultados
    archivos_n = st.session_state.archivos_n

    vencidos   = [r for r in resultados if r['estado']=='VENCIDO_SIN_PAGAR']
    pendientes = [r for r in resultados if r['estado']=='NO_REGISTRADO']
    con_atraso = [r for r in resultados if r['estado']=='REGISTRADO_TARDE']
    ok_items   = [r for r in resultados if r['estado']=='OK']
    t_multas   = sum(r['multa']+r['tim'] for r in resultados)
    anios      = sorted({r['anio'] for r in resultados},reverse=True)

    st.markdown(
        f'<div class="emp-badge">🏢 {empresa}'
        f'{f" · RUC {ruc}" if ruc else ""}'
        f' · Años: {" · ".join(str(a) for a in anios)}'
        f' · {len(archivos_n)} PDF(s)</div>',
        unsafe_allow_html=True
    )

    for col,num,lbl,color in zip(
        st.columns(5),
        [len(resultados),len(vencidos),len(pendientes),
         len(con_atraso),f'S/ {t_multas:,.0f}'],
        ['Total registros','Vencidos sin pagar','Sin registrar',
         'Pagados con atraso','Multas + TIM'],
        ['blu','red','amb','amb','red']
    ):
        with col:
            st.markdown(
                f'<div class="kpi"><div class="n {color}">{num}</div>'
                f'<div class="l">{lbl}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="div"></div>',unsafe_allow_html=True)

    for anio in anios:
        v_a=[r for r in vencidos   if r['anio']==anio]
        p_a=[r for r in pendientes if r['anio']==anio]
        c_a=[r for r in con_atraso if r['anio']==anio]
        o_a=[r for r in ok_items   if r['anio']==anio]
        if not any([v_a,p_a,c_a,o_a]): continue

        st.markdown(f'<div class="anio-banner">📅 AÑO {anio}</div>',
                    unsafe_allow_html=True)

        if v_a:
            st.markdown(f'**🔴 Vencidos sin pagar — {anio}**')
            for r in sorted(v_a,key=lambda x:x['dias_tarde'],reverse=True):
                costo=r['importe']+r['tim']+r['multa']
                mt=(f'<span class="tag tag-r">Multa S/ {r["multa"]:,.0f}</span>'
                    if r['multa'] else '')
                st.markdown(f"""<div class="box-r">
                    <strong>🚨 {r['nombre']} — {r['periodo']}</strong><br>
                    💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp;
                    Venció: <strong>{r['fecha_venc'].strftime('%d/%m/%Y') if r['fecha_venc'] else 'N/D'}</strong>
                    &nbsp;·&nbsp; <strong>{r['dias_tarde']} días vencido</strong><br>
                    {mt}<span class="tag tag-a">TIM S/ {r['tim']:,.2f}</span>
                    <span class="tag tag-r">Total regularizar: S/ {costo:,.2f}</span><br>
                    <span style="color:#991B1B">▶ {r['instruccion']}</span>
                </div>""",unsafe_allow_html=True)

        if p_a:
            st.markdown(f'**🟡 Pagados pero no registrados en el reporte — {anio}**')
            for r in p_a:
                box='box-r' if r['pagado_tarde'] else 'box-a'
                atr=''
                if r['pagado_tarde']:
                    ml=f'Multa S/ {r["multa"]:,.0f}' if r['con_multa'] else 'Solo TIM'
                    atr=(f'<br><span class="tag tag-r">{ml}</span>'
                         f' <span class="tag tag-a">TIM S/ {r["tim"]:,.2f}</span>'
                         f' — {r["dias_tarde"]} días tarde')
                st.markdown(f"""<div class="{box}">
                    <strong>📌 {r['nombre']} — {r['periodo']}</strong><br>
                    💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp;
                    Pagado: {r['fecha_pago'].strftime('%d/%m/%Y') if r['fecha_pago'] else 'N/D'}
                    {f'&nbsp;·&nbsp; N° {r["n_orden"]}' if r['n_orden'] else ''}
                    {atr}<br>
                    <span style="color:#92400E">▶ {r['instruccion']}</span>
                </div>""",unsafe_allow_html=True)

        if c_a:
            with st.expander(f'🟠 {len(c_a)} pagados con atraso — {anio}'):
                for r in c_a:
                    ml=f'⚠️ Multa S/ {r["multa"]:,.0f}' if r['con_multa'] else 'Solo TIM'
                    st.markdown(f"""<div class="box-a">
                        <strong>{r['nombre']} — {r['periodo']}</strong>
                        &nbsp;·&nbsp; S/ {r['importe']:,.2f}
                        &nbsp;·&nbsp; {r['dias_tarde']} días tarde
                        &nbsp;·&nbsp; {ml}
                        &nbsp;·&nbsp; TIM S/ {r['tim']:,.2f}
                        &nbsp;·&nbsp; ({r['tipo_venc']})
                    </div>""",unsafe_allow_html=True)

        if o_a:
            with st.expander(f'✅ {len(o_a)} al día — {anio}'):
                for r in o_a:
                    st.markdown(f"""<div class="box-g">
                        ✓ {r['nombre']} — {r['periodo']}
                        — S/ {r['importe']:,.2f}
                        — {r['fecha_pago'].strftime('%d/%m/%Y') if r['fecha_pago'] else ''}
                        — ({r['tipo_venc']})
                    </div>""",unsafe_allow_html=True)

    if not any([vencidos,pendientes,con_atraso]):
        st.markdown(
            '<div class="box-g">✅ <strong>Todo al día.</strong> '
            'No hay pendientes ni vencidos.</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="div"></div>',unsafe_allow_html=True)

    col_dl,col_nx = st.columns(2)
    with col_dl:
        excel_b=generar_excel(empresa,ruc,resultados,
                              st.session_state.extracto_df,archivos_n)
        n_emp=empresa[:20].replace(' ','_') if empresa else ruc
        fname=f'Reporte_{n_emp}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        st.download_button(
            '⬇️  Descargar reporte Excel completo',
            data=excel_b,file_name=fname,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,type='primary'
        )
    with col_nx:
        if st.button('➡️  Analizar otra empresa',use_container_width=True):
            for k in ['listo','resultados','empresa','ruc',
                      'extracto_df','sheets','archivos_n']:
                st.session_state[k]=(
                    False if k=='listo' else
                    [] if k in ['resultados','archivos_n'] else
                    pd.DataFrame() if k=='extracto_df' else
                    {} if k=='sheets' else ''
                )
            st.rerun()

    st.markdown(
        '<div class="box-b">💡 <strong>Descarga el Excel antes de analizar otra empresa.</strong> '
        'Contiene: Resumen · Vencidos · Sin registrar · Con atraso · Al día.</div>',
        unsafe_allow_html=True
    )

# ── FORMULARIO ──────────────────────────────────────────────────────────────
else:
    col_f,col_h = st.columns([3,2])

    with col_f:
        st.markdown('### Datos de la empresa')

        ruc_inp = st.text_input(
            'RUC (11 dígitos)',
            placeholder='Ej: 20613979779',
            help='El dígito y los vencimientos se calculan automáticamente desde el RUC.'
        )

        digito_calc=None
        if ruc_inp and len(ruc_inp.strip())==11 and ruc_inp.strip().isdigit():
            digito_calc=int(ruc_inp.strip()[-1])
            st.markdown(
                f'<div class="box-b" style="font-size:.82rem;margin-top:2px;">'
                f'✓ Dígito RUC: <strong>{digito_calc}</strong> — '
                f'vencimientos calculados automáticamente</div>',
                unsafe_allow_html=True
            )
        elif ruc_inp:
            st.warning('El RUC debe tener exactamente 11 dígitos.')

        empresa_inp=st.text_input(
            'Nombre de la empresa (opcional)',
            placeholder='Ej: TDD INVERSIONES S.A.C. — si no se pone, se usa el RUC'
        )

        igv_justo_chk=st.checkbox(
            '✅ Esta empresa usa IGV Justo (Ley 30524)',
            value=True,
            help='El vencimiento del IGV será el del período SIGUIENTE según cronograma SUNAT.'
        )

        st.markdown('')
        st.markdown('### Link del Google Sheet del cliente')
        sheet_url=st.text_input(
            '',label_visibility='collapsed',
            placeholder='https://docs.google.com/spreadsheets/d/...',
        )

        st.markdown('')
        st.markdown('### PDF de SUNAT — "Reporte de Declaraciones y Pagos"')
        st.caption(
            '📄 SUNAT SOL → Mis declaraciones y pagos → '
            '"Reporte electrónico de declaraciones y pagos" → Generar PDF. '
            'Puedes subir varios PDFs juntos (2024 + 2025 + 2026).'
        )
        archivos=st.file_uploader(
            '',type=['pdf'],
            accept_multiple_files=True,
            label_visibility='collapsed'
        )

        if archivos:
            st.markdown(
                f'<div class="box-g" style="font-size:.82rem;">'
                f'📄 {len(archivos)} PDF(s): '
                f'{" · ".join(a.name for a in archivos)}</div>',
                unsafe_allow_html=True
            )

        st.markdown('')
        if st.button('🔍  Analizar',type='primary',use_container_width=True):
            errores=[]
            if not ruc_inp.strip() or len(ruc_inp.strip())!=11:
                errores.append('Ingresa un RUC válido de 11 dígitos.')
            if not sheet_url.strip():
                errores.append('Ingresa el link del Google Sheet.')
            if not archivos:
                errores.append('Sube al menos un PDF del reporte SUNAT.')
            for e in errores: st.error(e)

            if not errores and digito_calc is not None:
                sid=extraer_sheet_id(sheet_url)
                if not sid:
                    st.error('Link de Google Sheet no válido.')
                else:
                    empresa_final=empresa_inp.strip() or ruc_inp.strip()

                    with st.spinner('Leyendo Google Sheet...'):
                        sheets=leer_sheet(sid)
                        if not sheets:
                            st.warning(
                                'No se pudo leer el Sheet. '
                                'Asegúrate de que esté compartido como '
                                '"Cualquier persona con el link puede ver".'
                            )

                    with st.spinner(f'Procesando {len(archivos)} PDF(s)...'):
                        extracto_df,nombres=combinar_pdfs(archivos)
                        if extracto_df.empty:
                            st.error(
                                'No se encontraron pagos en los PDFs. '
                                'Asegúrate de subir el "Reporte de Declaraciones '
                                'y Pagos" de SUNAT (no el formulario PDT).'
                            )
                            st.stop()

                    with st.spinner('Analizando...'):
                        resultados=analizar(
                            extracto_df,sheets,digito_calc,igv_justo_chk,HOY
                        )

                    if not resultados:
                        st.info('No se encontraron datos para analizar.')
                    else:
                        st.session_state.update({
                            'listo':True,'resultados':resultados,
                            'empresa':empresa_final,'ruc':ruc_inp.strip(),
                            'extracto_df':extracto_df,'sheets':sheets,
                            'archivos_n':nombres,
                        })
                        st.rerun()

    with col_h:
        st.markdown("""<div class="box-b" style="margin-top:8px;">
            <strong>📋 Cómo usar</strong><br><br>
            <strong>1.</strong> Pega el RUC — la app calcula todo sola<br>
            <strong>2.</strong> Nombre de empresa (opcional)<br>
            <strong>3.</strong> Marca si usa IGV Justo<br>
            <strong>4.</strong> Link del Google Sheet del cliente<br>
            <strong>5.</strong> Sube el PDF de SUNAT<br>
            &nbsp;&nbsp;&nbsp;&nbsp;Puedes subir 2024 + 2025 + 2026 juntos<br>
            <strong>6.</strong> Analizar → Descargar → Siguiente empresa
        </div>""",unsafe_allow_html=True)

        st.markdown("""<div class="box-a" style="margin-top:10px;">
            <strong>⚠️ Tributos con multa 5% UIT</strong><br>
            • ONP (5310) — S/ 275 por período<br>
            • Renta 5ta (3052) — S/ 275<br>
            • Renta 4ta (3042) — S/ 275<br>
            • Renta 2da (3022) — S/ 275<br><br>
            Los demás: solo TIM (0.04%/día)<br>
            UIT 2024=S/5,150 · 2025=S/5,350 · 2026=S/5,500
        </div>""",unsafe_allow_html=True)

        st.markdown("""<div class="box-b" style="margin-top:10px;">
            <strong>📅 IGV Justo (Ley 30524)</strong><br>
            Vence el período <strong>siguiente</strong> según el
            cronograma SUNAT y el dígito del RUC — no la fecha normal.
        </div>""",unsafe_allow_html=True)

        st.markdown("""<div class="box-g" style="margin-top:10px;">
            <strong>🔒 La app nunca modifica ningún Sheet</strong><br>
            Solo lee y compara. Tú decides qué actualizar.
        </div>""",unsafe_allow_html=True)

