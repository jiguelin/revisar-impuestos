import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO
from datetime import datetime, date

st.set_page_config(page_title="Contadeus — Revisor Tributario",
                   page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
  .main{background:#F8FAFC;} .block-container{padding-top:1.5rem;}
  .hdr{background:linear-gradient(135deg,#1B2A8C,#2563EB);padding:22px 28px;
       border-radius:12px;margin-bottom:20px;color:#fff;}
  .hdr h1{margin:0;font-size:1.7rem;font-weight:700;}
  .hdr p{margin:4px 0 0;opacity:.85;font-size:.92rem;}
  .kpi{background:#fff;border-radius:10px;padding:14px 16px;text-align:center;
       border:1px solid #E5E7EB;box-shadow:0 1px 4px rgba(0,0,0,.06);}
  .kpi .n{font-size:1.9rem;font-weight:700;} .kpi .l{font-size:.75rem;color:#6B7280;margin-top:2px;}
  .red{color:#DC2626;}.grn{color:#16A34A;}.amb{color:#D97706;}.blu{color:#1B2A8C;}
  .box-r{background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px 14px;margin:6px 0;font-size:.86rem;line-height:1.6;}
  .box-a{background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:10px 14px;margin:6px 0;font-size:.86rem;line-height:1.6;}
  .box-g{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:10px 14px;margin:6px 0;font-size:.86rem;line-height:1.6;}
  .box-b{background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:10px 14px;margin:6px 0;font-size:.86rem;line-height:1.6;}
  .tag{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.75rem;font-weight:600;margin-right:4px;}
  .tag-r{background:#FEE2E2;color:#991B1B;} .tag-a{background:#FEF3C7;color:#92400E;}
  .tag-g{background:#D1FAE5;color:#065F46;}
  .div{height:1px;background:#E5E7EB;margin:18px 0;}
  .emp-badge{background:#EEF2FF;border:1.5px solid #1B2A8C;color:#1B2A8C;
             padding:5px 14px;border-radius:20px;font-weight:600;font-size:.88rem;
             display:inline-block;margin-bottom:12px;}
  .anio-banner{background:#374151;color:#fff;padding:6px 14px;border-radius:6px;
               font-weight:600;font-size:.85rem;margin:14px 0 6px;display:inline-block;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════
UIT_POR_ANIO      = {2023:4950.0,2024:5150.0,2025:5350.0,2026:5500.0,2027:5500.0}
TIM_DIARIO        = 0.0004
CODIGOS_CON_MULTA = {"3052","3042","3022","5310"}

NOMBRE_TRIBUTO = {
    "1011":"IGV","3031":"Renta 3ra (General)","3111":"Renta RER (1.5%)",
    "3121":"Renta MYPE (1%)","3038":"ITAN","3052":"Renta 5ta Categoría",
    "3042":"Renta 4ta Categoría","3022":"Renta 2da Categoría",
    "5210":"EsSalud","5310":"ONP","8021":"Fraccionamiento Art.36",
}

MESES_NUM = {
    "ENERO":1,"FEBRERO":2,"MARZO":3,"ABRIL":4,"MAYO":5,"JUNIO":6,
    "JULIO":7,"AGOSTO":8,"SETIEMBRE":9,"SEPTIEMBRE":9,
    "OCTUBRE":10,"NOVIEMBRE":11,"DICIEMBRE":12
}
MESES_NOM = {1:"ENERO",2:"FEBRERO",3:"MARZO",4:"ABRIL",5:"MAYO",6:"JUNIO",
             7:"JULIO",8:"AGOSTO",9:"SETIEMBRE",10:"OCTUBRE",
             11:"NOVIEMBRE",12:"DICIEMBRE"}

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

def fecha_venc_normal(anio,mes,digito):
    cron=CRONOGRAMA.get(anio,CRONOGRAMA[2026])
    dias=cron.get(mes,[28]*11); dia=dias[min(digito,10)]
    mv,av=mes+1,anio
    if mv>12: mv,av=1,anio+1
    try:    return date(av,mv,dia)
    except: return date(av,mv,28)

def fecha_venc_igv_justo(anio,mes,digito):
    m2,a2=mes+1,anio
    if m2>12: m2,a2=1,anio+1
    return fecha_venc_normal(a2,m2,digito)

def multa_5pct(anio): return UIT_POR_ANIO.get(anio,5500.0)*0.05
def calc_tim(imp,dias): return round(imp*TIM_DIARIO*max(dias,0),2)

def limpiar_num(s):
    """
    Convierte número peruano/español a float.
    2,681 → 2681  |  2.681 → 2681  |  2,681.50 → 2681.5
    (321) → 321   |  -321  → 321   |  0.00 → 0
    """
    s=str(s).strip().strip('()').lstrip('-').replace(' ','')
    # Detectar formato: coma=miles+punto=decimal  VS  punto=miles+coma=decimal
    has_comma = ',' in s
    has_dot   = '.' in s
    if has_comma and has_dot:
        # "1,234.56" (inglés) o "1.234,56" (español)
        if s.index(',') < s.index('.'):
            s = s.replace(',','')           # "1,234.56" → "1234.56"
        else:
            s = s.replace('.','').replace(',','.')  # "1.234,56" → "1234.56"
    elif has_comma:
        p = s.split(',')
        if len(p)==2 and len(p[1])==3:
            s = s.replace(',','')          # "2,360" → "2360" (miles)
        else:
            s = s.replace(',','.')         # "0,50" → "0.50" (decimal)
    elif has_dot:
        p = s.split('.')
        if len(p)==2 and len(p[1])==3:
            s = s.replace('.','')          # "2.360" → "2360" (miles)
        # else: "0.00" o "102.50" → dejar como está (decimal)
    try:    return float(s)
    except: return 0.0

# ══════════════════════════════════════════════════════════════════════════════
# PDF 1 — SUNAT: Reporte de Declaraciones y Pagos
# ══════════════════════════════════════════════════════════════════════════════
def parsear_pdf_sunat(pdf_bytes):
    filas=[]; CODIGOS=set(NOMBRE_TRIBUTO.keys())
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    if not table or len(table)<2: continue
                    header=[str(c or '').lower().replace('\n',' ') for c in table[0]]
                    if not any('período' in h or 'periodo' in h for h in header): continue
                    if not any('tributo' in h for h in header): continue
                    for row in table[1:]:
                        if not row or len(row)<8: continue
                        vals=[str(v or '').strip().replace('\n',' ') for v in row]
                        periodo,n_orden,fecha_str,cod,monto_str = \
                            vals[0],vals[2],vals[3],vals[5],vals[7]
                        if not re.match(r'^202[3-9]\d{2}$',periodo): continue
                        if cod not in CODIGOS: continue
                        importe=limpiar_num(monto_str)
                        if importe<=0: continue
                        fecha_pago=None
                        if re.match(r'\d{1,2}/\d{2}/\d{4}',fecha_str):
                            try: fecha_pago=datetime.strptime(fecha_str.strip(),'%d/%m/%Y').date()
                            except: pass
                        filas.append({'PERIODO':periodo,'N_ORDEN':n_orden,
                                      'COD_TRIBUTO':cod,'FECHA_PAGO':fecha_pago,
                                      'IMPORTE':importe})
    except Exception as e:
        st.error(f"Error leyendo PDF SUNAT: {e}"); return pd.DataFrame()
    if not filas: return pd.DataFrame()
    df=pd.DataFrame(filas)
    df=df.drop_duplicates(subset=['N_ORDEN'],keep='first')
    return df.reset_index(drop=True)

def combinar_pdfs_sunat(archivos):
    dfs,nombres=[],[]
    for arch in archivos:
        arch.seek(0); df=parsear_pdf_sunat(arch.read())
        if not df.empty:
            df['_arch']=arch.name; dfs.append(df); nombres.append(arch.name)
        else: st.warning(f"⚠️ Sin datos en: **{arch.name}**")
    if not dfs: return pd.DataFrame(),nombres
    combinado=pd.concat(dfs,ignore_index=True)
    antes=len(combinado)
    combinado=combinado.drop_duplicates(subset=['N_ORDEN'],keep='first')
    dup=antes-len(combinado)
    if dup>0: st.info(f"ℹ️ {dup} pagos duplicados eliminados.")
    return combinado.reset_index(drop=True),nombres

# ══════════════════════════════════════════════════════════════════════════════
# PDF 2 — Reporte de Impuestos (Google Sheet exportado como PDF)
# ══════════════════════════════════════════════════════════════════════════════

# Tipo A (IGV): col1=MES, col2=IMPORTE, col3=FECHA_IGV_JUSTO, col4..=negat, col_last=PENDIENTE
# Tipo B (RENTA): col1=MES, col2=IMPORTE, col3..=negat/fecha, col_last=PENDIENTE
# Tipo C (ESSALUD/AFP/ONP): col1=MES, col2=MONTO, col3=IMPORTE_PAGADO(neg), ..., col_last=SALDO

SECCION_TITULO_COD = [
    (r'SALDO IGV|^IGV\b',                                        '1011','A'),
    (r'IMPUESTO A LA RENTA|RENTA.*MYPE|RENTA.*RER|RENTA.*GENE', '3121','B'),
    (r'RENTA.*4TA|CUARTA|4TA.*CATEG',                           '3042','B'),
    (r'RENTA.*5TA|QUINTA|5TA.*CATEG',                           '3052','B'),
    (r'RENTA.*2DA|SEGUNDA|2DA.*CATEG',                          '3022','B'),
    (r'ESSALUD',                                                 '5210','C'),
    (r'\bONP\b',                                                 '5310','C'),
    (r'\bITAN\b',                                                '3038','B'),
    (r'FRACCIONAMIENTO|FRACC.*ART',                              '8021','F'),
]

def detectar_seccion_titulo(texto):
    t=texto.upper().strip()
    anio_m=re.search(r'\b(20[23]\d)\b',t)
    # Fraccionamiento puede no tener año 20XX en el título (ej: "IGV DE AGOSTO-25")
    # Detectar por patrón y asignar año 2026 por defecto
    if not anio_m:
        for patron,cod,tipo in SECCION_TITULO_COD:
            if re.search(patron,t):
                return cod,2026,tipo
        return None,None,None
    anio=int(anio_m.group(1))
    for patron,cod,tipo in SECCION_TITULO_COD:
        if re.search(patron,t): return cod,anio,tipo
    return None,None,None

def parsear_fila_fracc(vals):
    """
    Parsea una fila del fraccionamiento.
    Estructura: N°CUOTA | VENCIM. | AMORTIZA. | INTERÉS | TOTAL | PAGO | SALDO
    Retorna dict compatible con parsear_fila_reporte, o None si no es cuota válida.
    PAGO entre paréntesis = pagado y registrado.
    PAGO vacío = no pagado aún.
    """
    v=[c.strip() for c in vals]
    if not v: return None
    
    cuota_id=v[0].strip().upper()
    # Solo procesar filas de cuota: IA, 1, 2, 3, 4, 5...
    if not (cuota_id=='IA' or (cuota_id.isdigit() and 1<=int(cuota_id)<=99)):
        return None
    
    # Mapear cuota a "mes virtual" para el sistema
    # IA → mes 0 especial, cuotas 1-12 → meses 1-12
    # Usamos un identificador único: cuota_id como mes_nom
    mes_nom = f'CUOTA_{cuota_id}'
    mes_num = 0 if cuota_id=='IA' else int(cuota_id)
    
    # Total (col 4)
    total=0.0
    if len(v)>4:
        try:
            t=limpiar_num(v[4])
            if 0<t<100000: total=t
        except: pass
    
    # Pago registrado (col 5): entre paréntesis = pagado
    pago_monto=0.0; pagada=False
    if len(v)>5:
        p=v[5].strip()
        # Pago registrado: entre paréntesis (45) O negativo -45
        if (p.startswith('(') and p.endswith(')')) or p.startswith('-'):
            try:
                pago_monto=float(p.strip('()').lstrip('-').replace(',',''))
                pagada=True
            except: pass
    
    if total<=0 and pago_monto<=0: return None
    
    importe = pago_monto if pagada else total
    
    return {
        'mes_nom':        mes_nom,
        'mes_num':        mes_num,
        'importe_decl':   total,
        'pendiente':      0.0 if pagada else total,
        'fecha_igv_justo': None,
        'pago_monto':     pago_monto,
        'pagada':         pagada,
    }

def parsear_fila_reporte(vals, tipo, seccion_cod):
    """
    Extrae datos de una fila del reporte de impuestos.
    Retorna dict con mes_nom, mes_num, importe_decl, pendiente, fecha_igv_justo
    o None si la fila no es de mes.
    """
    v=[c.strip() for c in vals]

    # Detectar mes en cols 0-2
    mes_d=None
    for celda in v[:3]:
        cu=celda.upper().strip()
        for mn,mv in MESES_NUM.items():
            if cu==mn or cu.startswith(mn+' '): mes_d=(mn,mv); break
        if mes_d: break
    if not mes_d: return None

    mes_nom,mes_num=mes_d

    # Columna PENDIENTE/SALDO: último valor numérico no-negativo de la fila
    # (de derecha a izquierda, ignorar vacíos, FRACCIONADO, negativos)
    pendiente=None
    for i in range(len(v)-1,-1,-1):
        c=v[i].strip()
        if not c or c in ['FRACCIONADO','-']: continue
        if c.startswith('(') or c.startswith('-'): continue  # negativo/paréntesis = pagado
        n=limpiar_num(c)
        if n>=0:
            pendiente=n; break

    if pendiente is None: pendiente = 0.0

    # Columna IMPORTE declarado: primera celda numérica positiva (col 2+)
    importe_decl=0.0
    for c in v[2:5]:
        if c and not c.startswith('(') and not c.startswith('-') and c not in ['FRACCIONADO','-']:
            n=limpiar_num(c)
            if n>0: importe_decl=n; break
    if importe_decl==0.0: importe_decl=pendiente

    # Fecha IGV Justo: SOLO tipo A, col índice 3 (0-based desde el inicio de la fila original)
    fecha_igv_justo=None
    if tipo=='A':
        # En la fila real: ['', MES, IMPORTE, FECHA_IGV_JUSTO, ...]
        # v ya viene sin la primera celda vacía, entonces v[2] = FECHA_IGV_JUSTO
        if len(v)>2:
            c=v[2].strip()
            if re.match(r'\d{1,2}/\d{2}/\d{4}$',c):
                try: fecha_igv_justo=datetime.strptime(c,'%d/%m/%Y').date()
                except: pass

    return {'mes_nom':mes_nom,'mes_num':mes_num,
            'importe_decl':importe_decl,'pendiente':pendiente,
            'fecha_igv_justo':fecha_igv_justo}

def parsear_pdf_reporte(pdf_bytes):
    """
    Lee el PDF del reporte de impuestos.
    Devuelve lista de dicts con saldos pendientes > 0.
    """
    saldos=[]; vistos=set()
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            seccion_cod=None; seccion_anio=None; seccion_tipo=None

            for page in pdf.pages:
                for table in page.extract_tables():
                    if not table: continue
                    for row in table:
                        if not row: continue
                        vals=[str(v or '').strip().replace('\n',' ') for v in row]
                        texto=' '.join(v for v in vals if v)

                        # ── Detectar título de sección ──────────────────────
                        cod_d,anio_d,tipo_d=detectar_seccion_titulo(texto)
                        if cod_d:
                            seccion_cod=cod_d; seccion_anio=anio_d; seccion_tipo=tipo_d
                            continue

                        # ── Ignorar encabezados de columnas ──────────────────
                        tu=texto.upper()
                        if any(kw in tu for kw in
                               ['MESES','PERIODO','SE PAGÓ','SE PAGO',
                                'PENDIENTE','IMPORTE PAGADO','N° DE CUOTAS',
                                'AMORTIZA','VENCIM.']):
                            continue

                        if not seccion_cod or not seccion_anio: continue

                        # ── Parsear fila de mes o cuota fraccionamiento ──────
                        v=vals[1:] if vals and vals[0]=='' else vals
                        
                        # Tipo F: fraccionamiento — filas son IA, 1, 2, 3...
                        if seccion_tipo=='F':
                            r=parsear_fila_fracc(v)
                        else:
                            r=parsear_fila_reporte(v, seccion_tipo, seccion_cod)
                        if not r: continue

                        clave=(seccion_cod,r['mes_nom'],seccion_anio)
                        if clave in vistos: continue

                        vistos.add(clave)
                        saldos.append({
                            'codigo':        seccion_cod,
                            'nombre':        NOMBRE_TRIBUTO.get(seccion_cod,''),
                            'mes_nom':       r['mes_nom'],
                            'mes_num':       r['mes_num'],
                            'anio':          seccion_anio,
                            'importe_decl':  r['importe_decl'],
                            'pendiente':     r['pendiente'],
                            'fecha_igv_justo': r['fecha_igv_justo'],
                            'tipo':          seccion_tipo,
                            # Para fraccionamiento: monto pagado registrado
                            'pago_monto':    r.get('pago_monto', 0.0),
                            'pagada':        r.get('pagada', None),  # None = no es fracc
                        })
    except Exception as e:
        st.error(f"Error leyendo PDF reporte: {e}")
    return saldos

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
def analizar(extracto, saldos_reporte, digito, igv_justo, hoy):
    resultados=[]; vistos_pdf=set()

    # ── 1. Pagos del PDF SUNAT ────────────────────────────────────────────────
    for _,fila in extracto.iterrows():
        periodo=str(fila.get('PERIODO','')).strip()
        if not re.match(r'^202[3-9]\d{2}$',periodo): continue
        anio,mes=int(periodo[:4]),int(periodo[4:6])
        codigo=str(fila.get('COD_TRIBUTO','')).strip()
        if codigo not in NOMBRE_TRIBUTO: continue
        importe=float(fila.get('IMPORTE',0) or 0)
        if importe<=0: continue

        n_orden=str(fila.get('N_ORDEN','')).strip()
        clave=(codigo,anio,mes,round(importe),n_orden[:8])
        if clave in vistos_pdf: continue

        nombre=NOMBRE_TRIBUTO[codigo]
        mes_nom=MESES_NOM.get(mes,str(mes))
        fp=fila.get('FECHA_PAGO')
        fecha_pago=fp if isinstance(fp,date) else None

        # Vencimiento
        if codigo=='1011' and igv_justo:
            # Usar fecha IGV Justo del reporte si disponible
            fij=next((s['fecha_igv_justo'] for s in saldos_reporte
                      if s['codigo']=='1011' and s['mes_num']==mes
                      and s['anio']==anio and s['fecha_igv_justo']),None)
            venc=fij or fecha_venc_igv_justo(anio,mes,digito)
            tipo_venc='IGV Justo'
        else:
            venc=fecha_venc_normal(anio,mes,digito)
            tipo_venc='Normal'

        # Pestaña
        if   codigo=='1011': pestana=f'IGV {anio}'
        elif codigo=='5210': pestana='ESSALUD'
        elif codigo=='5310': pestana='ONP'
        elif codigo=='3052': pestana='RENTA_5TA'
        elif codigo=='3042': pestana='RENTA_4TA'
        elif codigo=='3038': pestana='ITAN'
        elif codigo=='8021': pestana='FRACCIONAMIENTOS'
        else:                pestana=f'RENTA {anio}'

        # ¿Ya registrado en el reporte PDF?
        ya_reg=False
        if codigo=='8021':
            # Fraccionamiento: buscar si alguna cuota pagada tiene ese monto
            for s in saldos_reporte:
                if (s['codigo']=='8021' and s['anio']==anio and
                    s.get('pagada') and abs(s.get('pago_monto',0)-importe)<1.0):
                    ya_reg=True; break
        else:
            for s in saldos_reporte:
                if s['codigo']==codigo and s['mes_num']==mes and s['anio']==anio:
                    ya_reg=True; break

        dias_tarde=max((fecha_pago-venc).days,0) if fecha_pago and venc else 0
        pagado_tarde=dias_tarde>0
        con_multa=codigo in CODIGOS_CON_MULTA
        tim_calc=calc_tim(importe,dias_tarde) if pagado_tarde else 0.0
        mult_calc=multa_5pct(anio) if (pagado_tarde and con_multa) else 0.0

        if not ya_reg:     estado='NO_REGISTRADO'
        elif pagado_tarde: estado='REGISTRADO_TARDE'
        else:              estado='OK'

        instruccion=(f'Pestaña "{pestana}" → fila {mes_nom} → '
                     f'columna "SE PAGÓ" → S/ {importe:,.2f}')
        if fecha_pago: instruccion+=f' · Fecha: {fecha_pago.strftime("%d/%m/%Y")}'

        vistos_pdf.add((codigo,mes_nom,anio))
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

    # ── 2. Vencidos del reporte PDF ───────────────────────────────────────────
    for s in saldos_reporte:
        cod=s['codigo']; mes_nom=s['mes_nom']; mes_num=s['mes_num']
        anio=s['anio'];  saldo=s['pendiente']
        if saldo<=0: continue
        if (cod,mes_nom,anio) in vistos_pdf: continue  # ya procesado del SUNAT

        if cod=='1011' and igv_justo and s.get('fecha_igv_justo'):
            venc=s['fecha_igv_justo']; tipo_venc='IGV Justo'
        elif cod=='1011' and igv_justo:
            venc=fecha_venc_igv_justo(anio,mes_num,digito); tipo_venc='IGV Justo'
        else:
            venc=fecha_venc_normal(anio,mes_num,digito); tipo_venc='Normal'

        if venc>=hoy: continue  # aún no vence → no alertar

        dias_v=(hoy-venc).days
        con_m=cod in CODIGOS_CON_MULTA
        if   cod=='1011': pestana=f'IGV {anio}'
        elif cod=='5210': pestana='ESSALUD'
        elif cod=='5310': pestana='ONP'
        elif cod=='3052': pestana='RENTA_5TA'
        elif cod=='3042': pestana='RENTA_4TA'
        else:             pestana=f'RENTA {anio}'

        resultados.append({
            'estado':'VENCIDO_SIN_PAGAR',
            'codigo':cod,'nombre':NOMBRE_TRIBUTO.get(cod,''),
            'periodo':f'{mes_nom}-{anio}','mes':mes_nom,'anio':anio,
            'importe':saldo,'fecha_pago':None,
            'fecha_venc':venc,'tipo_venc':tipo_venc,
            'dias_tarde':dias_v,'pagado_tarde':False,'con_multa':con_m,
            'tim':calc_tim(saldo,dias_v),
            'multa':multa_5pct(anio) if con_m else 0,
            'n_orden':'','pestana':pestana,
            'instruccion':(f'Saldo pendiente S/ {saldo:,.2f} — '
                          f'venció hace {dias_v} días — regularizar en SUNAT'),
            'ya_registrado':True,
        })

    return resultados

# ══════════════════════════════════════════════════════════════════════════════
# EXCEL
# ══════════════════════════════════════════════════════════════════════════════
def generar_excel(empresa,ruc,resultados,extracto,nombres_sunat,nombre_reporte):
    buf=BytesIO()
    with pd.ExcelWriter(buf,engine='openpyxl') as w:
        hoy_s=datetime.now().strftime('%d/%m/%Y %H:%M')
        vencidos  =[r for r in resultados if r['estado']=='VENCIDO_SIN_PAGAR']
        pendientes=[r for r in resultados if r['estado']=='NO_REGISTRADO']
        con_atraso=[r for r in resultados if r['estado']=='REGISTRADO_TARDE']
        ok_items  =[r for r in resultados if r['estado']=='OK']
        t_multas  =sum(r['multa']+r['tim'] for r in resultados)
        m_pend    =sum(r['importe'] for r in pendientes+vencidos)
        anios     =sorted({r['anio'] for r in resultados})

        pd.DataFrame({'Campo':
            ['Empresa','RUC','Fecha análisis','PDF SUNAT','PDF Reporte impuestos',
             'Años cubiertos','Total registros','Vencidos sin pagar',
             'Sin registrar','Pagados con atraso','Al día',
             'Monto pendiente/vencido S/','Multas + TIM estimado S/'],
            'Valor':[empresa,ruc,hoy_s,', '.join(nombres_sunat),nombre_reporte,
                     ', '.join(str(a) for a in anios),len(resultados),len(vencidos),
                     len(pendientes),len(con_atraso),len(ok_items),
                     f'{m_pend:,.2f}',f'{t_multas:,.2f}']
        }).to_excel(w,sheet_name='RESUMEN',index=False)

        def fila(r,extra={}):
            d={'Año':r['anio'],'Tributo':r['nombre'],'Período':r['periodo'],
               'Importe S/':r['importe'],
               'Fecha pago':r['fecha_pago'].strftime('%d/%m/%Y') if r['fecha_pago'] else '',
               'N° Orden':r['n_orden']}
            d.update(extra); return d

        if vencidos:
            pd.DataFrame([fila(r,{
                'Vencimiento':r['fecha_venc'].strftime('%d/%m/%Y') if r['fecha_venc'] else '',
                'Días vencido':r['dias_tarde'],'TIM S/':r['tim'],
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
                'Días tarde':r['dias_tarde'],'TIM S/':r['tim'],
                'Multa S/':r['multa'] if r['multa'] else 'No aplica',
                'Genera multa':'SÍ' if r['con_multa'] else 'No',
                'Tipo vencimiento':r['tipo_venc'],
            }) for r in con_atraso]
            ).to_excel(w,sheet_name='🟠 PAGADOS CON ATRASO',index=False)

        if ok_items:
            pd.DataFrame([fila(r,{'Estado':'✓ A tiempo y registrado'})
                         for r in ok_items]
            ).to_excel(w,sheet_name='✅ AL DÍA',index=False)

        extracto.to_excel(w,sheet_name='EXTRACTO SUNAT',index=False)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hdr">
  <h1>📊 Contadeus — Revisor Tributario</h1>
  <p>Sube los 2 PDFs · Detecta vencidos, sin registrar y multas automáticamente</p>
</div>""", unsafe_allow_html=True)

for k,v in [('listo',False),('resultados',[]),('empresa',''),('ruc',''),
            ('extracto_df',pd.DataFrame()),('archivos_n',[]),('nombre_reporte','')]:
    if k not in st.session_state: st.session_state[k]=v

HOY=date.today()

# ── RESULTADOS ──────────────────────────────────────────────────────────────
if st.session_state.listo and st.session_state.resultados:
    empresa=st.session_state.empresa; ruc=st.session_state.ruc
    resultados=st.session_state.resultados; archivos_n=st.session_state.archivos_n

    vencidos  =[r for r in resultados if r['estado']=='VENCIDO_SIN_PAGAR']
    pendientes=[r for r in resultados if r['estado']=='NO_REGISTRADO']
    con_atraso=[r for r in resultados if r['estado']=='REGISTRADO_TARDE']
    ok_items  =[r for r in resultados if r['estado']=='OK']
    t_multas  =sum(r['multa']+r['tim'] for r in resultados)
    anios     =sorted({r['anio'] for r in resultados},reverse=True)

    st.markdown(
        f'<div class="emp-badge">🏢 {empresa}'
        f'{f" · RUC {ruc}" if ruc else ""}'
        f' · Años: {" · ".join(str(a) for a in anios)}</div>',
        unsafe_allow_html=True)

    for col,num,lbl,color in zip(
        st.columns(5),
        [len(resultados),len(vencidos),len(pendientes),
         len(con_atraso),f'S/ {t_multas:,.0f}'],
        ['Total registros','Vencidos sin pagar','Sin registrar',
         'Pagados con atraso','Multas + TIM'],
        ['blu','red','amb','amb','red']):
        with col:
            st.markdown(f'<div class="kpi"><div class="n {color}">{num}</div>'
                        f'<div class="l">{lbl}</div></div>',unsafe_allow_html=True)

    st.markdown('<div class="div"></div>',unsafe_allow_html=True)

    for anio in anios:
        v_a=[r for r in vencidos   if r['anio']==anio]
        p_a=[r for r in pendientes if r['anio']==anio]
        c_a=[r for r in con_atraso if r['anio']==anio]
        o_a=[r for r in ok_items   if r['anio']==anio]
        if not any([v_a,p_a,c_a,o_a]): continue

        st.markdown(f'<div class="anio-banner">📅 AÑO {anio}</div>',unsafe_allow_html=True)

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
        st.markdown('<div class="box-g">✅ <strong>Todo al día.</strong></div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="div"></div>',unsafe_allow_html=True)

    col_dl,col_nx=st.columns(2)
    with col_dl:
        excel_b=generar_excel(empresa,ruc,resultados,
                              st.session_state.extracto_df,
                              archivos_n,st.session_state.nombre_reporte)
        n=empresa[:20].replace(' ','_') if empresa else ruc
        fname=f'Reporte_{n}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        st.download_button('⬇️  Descargar reporte Excel completo',
                           data=excel_b,file_name=fname,
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           use_container_width=True,type='primary')
    with col_nx:
        if st.button('➡️  Analizar otra empresa',use_container_width=True):
            for k in ['listo','resultados','empresa','ruc',
                      'extracto_df','archivos_n','nombre_reporte']:
                st.session_state[k]=(
                    False if k=='listo' else
                    [] if k in ['resultados','archivos_n'] else
                    pd.DataFrame() if k=='extracto_df' else '')
            st.rerun()

    st.markdown('<div class="box-b">💡 <strong>Descarga el Excel antes de analizar otra empresa.</strong></div>',
                unsafe_allow_html=True)

# ── FORMULARIO ──────────────────────────────────────────────────────────────
else:
    col_f,col_h=st.columns([3,2])

    with col_f:
        st.markdown('### Datos de la empresa')
        ruc_inp=st.text_input('RUC (11 dígitos)',placeholder='Ej: 20613979779',
                              help='El dígito y los vencimientos se calculan automáticamente.')
        digito_calc=None
        if ruc_inp and len(ruc_inp.strip())==11 and ruc_inp.strip().isdigit():
            digito_calc=int(ruc_inp.strip()[-1])
            st.markdown(f'<div class="box-b" style="font-size:.82rem;margin-top:2px;">'
                        f'✓ Dígito RUC: <strong>{digito_calc}</strong> — '
                        f'vencimientos calculados automáticamente</div>',
                        unsafe_allow_html=True)
        elif ruc_inp:
            st.warning('El RUC debe tener 11 dígitos.')

        empresa_inp=st.text_input('Nombre de la empresa (opcional)',
                                  placeholder='Ej: TDD INVERSIONES S.A.C.')
        igv_justo_chk=st.checkbox('✅ Esta empresa usa IGV Justo (Ley 30524)',value=True)

        st.markdown('')
        st.markdown('### 📄 PDF 1 — SUNAT: Reporte de Declaraciones y Pagos')
        st.caption('SUNAT SOL → Mis declaraciones y pagos → Reporte electrónico → Generar PDF. Puedes subir varios (2024+2025+2026).')
        archivos_sunat=st.file_uploader('',type=['pdf'],accept_multiple_files=True,
                                        label_visibility='collapsed',key='sunat_pdfs')
        if archivos_sunat:
            st.markdown(f'<div class="box-g" style="font-size:.82rem;">'
                        f'📄 {len(archivos_sunat)} PDF(s): '
                        f'{" · ".join(a.name for a in archivos_sunat)}</div>',
                        unsafe_allow_html=True)

        st.markdown('')
        st.markdown('### 📊 PDF 2 — Reporte de Impuestos del cliente')
        st.caption('En Google Sheets del cliente → Archivo → Descargar → PDF.')
        archivo_reporte=st.file_uploader('',type=['pdf'],accept_multiple_files=False,
                                         label_visibility='collapsed',key='reporte_pdf')
        if archivo_reporte:
            st.markdown(f'<div class="box-g" style="font-size:.82rem;">'
                        f'📊 {archivo_reporte.name}</div>',unsafe_allow_html=True)

        st.markdown('')
        if st.button('🔍  Analizar',type='primary',use_container_width=True):
            errores=[]
            if not ruc_inp.strip() or len(ruc_inp.strip())!=11:
                errores.append('Ingresa un RUC válido de 11 dígitos.')
            if not archivos_sunat:
                errores.append('Sube el PDF de SUNAT (Reporte de Declaraciones y Pagos).')
            if not archivo_reporte:
                errores.append('Sube el PDF del Reporte de Impuestos del cliente.')
            for e in errores: st.error(e)

            if not errores and digito_calc is not None:
                empresa_final=empresa_inp.strip() or ruc_inp.strip()

                with st.spinner('Procesando PDFs SUNAT...'):
                    extracto_df,nombres_sunat=combinar_pdfs_sunat(archivos_sunat)
                    if extracto_df.empty:
                        st.error('No se encontraron pagos en el PDF de SUNAT.'); st.stop()

                with st.spinner('Leyendo reporte de impuestos...'):
                    archivo_reporte.seek(0)
                    saldos_reporte=parsear_pdf_reporte(archivo_reporte.read())
                    if not saldos_reporte:
                        st.warning('No se leyeron saldos del reporte. '
                                   'Verificar que sea el PDF correcto.')

                with st.spinner('Analizando...'):
                    resultados=analizar(extracto_df,saldos_reporte,
                                        digito_calc,igv_justo_chk,HOY)

                if not resultados:
                    st.info('No se encontraron datos para analizar.')
                else:
                    st.session_state.update({
                        'listo':True,'resultados':resultados,
                        'empresa':empresa_final,'ruc':ruc_inp.strip(),
                        'extracto_df':extracto_df,'archivos_n':nombres_sunat,
                        'nombre_reporte':archivo_reporte.name,
                    })
                    st.rerun()

    with col_h:
        st.markdown("""<div class="box-b" style="margin-top:8px;">
            <strong>📋 Cómo usar</strong><br><br>
            <strong>1.</strong> Pega el RUC — la app calcula el dígito sola<br>
            <strong>2.</strong> Nombre de empresa (opcional)<br>
            <strong>3.</strong> Marca si usa IGV Justo<br>
            <strong>4.</strong> Sube PDF de SUNAT<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<em>SUNAT SOL → Mis declaraciones → Reporte electrónico</em><br>
            &nbsp;&nbsp;&nbsp;&nbsp;Puedes subir varios años juntos<br>
            <strong>5.</strong> Sube PDF del reporte de impuestos<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<em>Google Sheets → Archivo → Descargar → PDF</em><br>
            <strong>6.</strong> Analizar → Descargar Excel → Siguiente empresa
        </div>""",unsafe_allow_html=True)

        st.markdown("""<div class="box-a" style="margin-top:10px;">
            <strong>⚠️ Tributos con multa 5% UIT</strong><br>
            • ONP (5310) — S/ 275<br>
            • Renta 5ta (3052) — S/ 275<br>
            • Renta 4ta (3042) — S/ 275<br>
            • Renta 2da (3022) — S/ 275<br><br>
            Los demás: solo TIM (0.04%/día)<br>
            UIT 2024=S/5,150 · 2025=S/5,350 · 2026=S/5,500
        </div>""",unsafe_allow_html=True)

        st.markdown("""<div class="box-g" style="margin-top:10px;">
            <strong>🔒 La app nunca modifica ningún archivo</strong><br>
            Solo lee y compara. Tú decides qué actualizar.
        </div>""",unsafe_allow_html=True)

