import streamlit as st
import pandas as pd
import pdfplumber
import re
import requests
from io import BytesIO, StringIO
from datetime import datetime, date

st.set_page_config(
    page_title="Contadeus — Revisor Tributario",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  .main{background:#F8FAFC;} .block-container{padding-top:1.5rem;}
  .hdr{background:linear-gradient(135deg,#1B2A8C,#2563EB);padding:24px 30px;
       border-radius:14px;margin-bottom:24px;color:#fff;}
  .hdr h1{margin:0;font-size:1.75rem;font-weight:800;}
  .hdr p{margin:5px 0 0;opacity:.82;font-size:.93rem;}
  .kpi{background:#fff;border-radius:12px;padding:16px 18px;text-align:center;
       border:1px solid #E5E7EB;box-shadow:0 2px 6px rgba(0,0,0,.05);}
  .kpi .n{font-size:2rem;font-weight:800;line-height:1.1;}
  .kpi .l{font-size:.73rem;color:#6B7280;margin-top:3px;}
  .red{color:#DC2626;}.grn{color:#16A34A;}.amb{color:#D97706;}.blu{color:#1B2A8C;}
  .card{border-radius:10px;padding:12px 16px;margin:5px 0;font-size:.87rem;line-height:1.65;}
  .cr{background:#FEF2F2;border-left:4px solid #DC2626;}
  .ca{background:#FFFBEB;border-left:4px solid #F59E0B;}
  .co{background:#FFF7ED;border-left:4px solid #EA580C;}
  .cg{background:#F0FDF4;border-left:4px solid #16A34A;}
  .cb{background:#EFF6FF;border-left:4px solid #2563EB;}
  .cp{background:#FDF4FF;border-left:4px solid #9333EA;}
  .badge{display:inline-block;padding:2px 8px;border-radius:20px;
         font-size:.72rem;font-weight:700;margin:0 3px 2px 0;}
  .br{background:#FEE2E2;color:#991B1B;} .ba{background:#FEF3C7;color:#92400E;}
  .bg{background:#D1FAE5;color:#065F46;} .bb{background:#DBEAFE;color:#1E40AF;}
  .bo{background:#FFEDD5;color:#9A3412;} .bp{background:#F3E8FF;color:#6B21A8;}
  .sep{height:1px;background:#E5E7EB;margin:18px 0;}
  .emp{background:#EEF2FF;border:2px solid #1B2A8C;color:#1B2A8C;padding:6px 16px;
       border-radius:22px;font-weight:700;font-size:.9rem;display:inline-block;margin-bottom:14px;}
  .yr{background:#1F2937;color:#fff;padding:6px 14px;border-radius:7px;
      font-weight:700;font-size:.87rem;margin:14px 0 7px;display:inline-block;}
  .stitle{font-size:1rem;font-weight:700;margin:16px 0 6px;color:#111827;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES TRIBUTARIAS
# ══════════════════════════════════════════════════════════════════════════════
UIT = {2022:4600, 2023:4950, 2024:5150, 2025:5350, 2026:5500, 2027:5500}
TIM_D = 0.0004
CON_MULTA = {"3052","3042","3022","5310"}

TRIBUTO = {
    "1011":"IGV","3031":"Renta 3ra","3111":"Renta RER (1.5%)",
    "3121":"Renta MYPE (1%)","3038":"ITAN","3052":"Renta 5ta Categoría",
    "3042":"Renta 4ta Categoría","3022":"Renta 2da Categoría",
    "5210":"EsSalud","5310":"ONP","8021":"Fraccionamiento Art.36",
    "AFP":"AFP","SIS":"SIS",
}

MESES = {
    "ENERO":1,"FEBRERO":2,"MARZO":3,"ABRIL":4,"MAYO":5,"JUNIO":6,
    "JULIO":7,"AGOSTO":8,"SETIEMBRE":9,"SEPTIEMBRE":9,
    "OCTUBRE":10,"NOVIEMBRE":11,"DICIEMBRE":12
}
MNom = {
    1:"ENERO",2:"FEBRERO",3:"MARZO",4:"ABRIL",5:"MAYO",6:"JUNIO",
    7:"JULIO",8:"AGOSTO",9:"SETIEMBRE",10:"OCTUBRE",11:"NOVIEMBRE",12:"DICIEMBRE"
}

# ── CRONOGRAMAS SUNAT OFICIALES 2022-2026 ─────────────────────────────────────
# 2022: RS 189-2021/SUNAT — fuente: sunat.gob.pe/orientacion/cronogramas/2022
# 2023: RS 281-2022/SUNAT — fuente: sunat.gob.pe/orientacion/cronogramas/2023
# 2024: RS 281-2022/SUNAT — fuente: sunat.gob.pe/orientacion/cronogramas/2024
# 2025: RS 281-2022/SUNAT — fuente: El Peruano (confirmado Contadeus)
# 2026: RS 281-2022/SUNAT — fuente: sunat.gob.pe/orientacion/cronogramas/2026
# Índices: 0-9 = dígito RUC, 10 = buenos contribuyentes/UESP
CRON = {
    2022:{
        1: [15,16,17,17,18,18,21,21,22,22,23],2: [15,16,17,17,18,18,21,21,22,22,23],
        3: [19,20,21,21,22,22,25,25,26,26,27],4: [17,18,19,19,20,20,23,23,24,24,25],
        5: [15,16,17,17,20,20,21,21,22,22,23],6: [15,18,19,19,20,20,21,21,22,22,25],
        7: [16,17,18,18,19,19,22,22,23,23,24],8: [15,16,19,19,20,20,21,21,22,22,23],
        9: [17,18,19,19,20,20,21,21,24,24,25],10:[15,16,17,17,18,18,21,21,22,22,23],
        11:[15,16,19,19,20,20,21,21,22,22,23],12:[17,18,19,19,20,20,23,23,24,24,25],
    },
    2023:{
        1: [15,16,17,17,20,20,21,21,22,22,23],2: [15,16,17,17,20,20,21,21,22,22,23],
        3: [19,20,21,21,24,24,25,25,26,26,27],4: [16,17,18,18,19,19,22,22,23,23,24],
        5: [15,16,19,19,20,20,21,21,22,22,23],6: [17,18,19,19,20,20,21,21,24,24,25],
        7: [15,16,17,17,18,18,21,21,22,22,23],8: [15,18,19,19,20,20,21,21,22,22,25],
        9: [16,17,18,18,19,19,20,20,23,23,24],10:[16,17,20,20,21,21,22,22,23,23,24],
        11:[18,19,20,20,21,21,22,22,26,26,27],12:[16,17,18,18,19,19,22,22,23,23,24],
    },
    2024:{
        1: [15,16,19,19,20,20,21,21,22,22,23],2: [15,16,18,18,19,19,20,20,21,21,22],
        3: [15,18,19,19,20,20,21,21,22,22,25],4: [15,16,17,17,18,18,19,19,22,22,23],
        5: [14,15,16,16,17,17,20,20,21,21,22],6: [14,17,18,18,19,19,20,20,21,21,24],
        7: [15,16,17,17,18,18,19,19,22,22,23],8: [14,15,16,16,19,19,20,20,21,21,22],
        9: [13,16,17,17,18,18,19,19,20,20,23],10:[15,16,17,17,18,18,21,21,22,22,23],
        11:[14,15,18,18,19,19,20,20,21,21,22],12:[15,16,17,17,20,20,21,21,22,22,23],
    },
    2025:{
        1: [17,18,19,19,20,20,21,21,24,24,25],2: [17,18,19,19,20,20,21,21,24,24,25],
        3: [15,16,21,21,22,22,23,23,24,24,25],4: [16,19,20,20,21,21,22,22,23,23,26],
        5: [16,17,18,18,19,19,20,20,23,23,24],6: [15,16,17,17,18,18,21,21,22,22,24],
        7: [18,19,20,20,21,21,22,22,25,25,26],8: [15,16,17,17,18,18,19,19,22,22,23],
        9: [16,17,20,20,21,21,22,22,23,23,24],10:[17,18,19,19,20,20,21,21,24,24,25],
        11:[17,18,19,19,22,22,23,23,24,24,26],12:[16,19,20,20,21,21,22,22,23,23,26],
    },
    2026:{
        1: [16,17,18,18,19,19,20,20,23,23,24],2: [16,17,18,18,19,19,20,20,23,23,24],
        3: [17,20,21,21,22,22,23,23,24,24,27],4: [18,19,20,20,21,21,22,22,25,25,26],
        5: [15,16,17,17,18,18,19,19,22,22,23],6: [15,16,17,17,20,20,21,21,22,22,24],
        7: [18,19,20,20,21,21,24,24,25,25,26],8: [15,16,17,17,18,18,21,21,22,22,23],
        9: [16,19,20,20,21,21,22,22,23,23,26],10:[16,17,18,18,19,19,20,20,23,23,24],
        11:[17,18,21,21,22,22,23,23,24,24,28],12:[18,19,20,20,21,21,22,22,25,25,26],
    },
}

def fvenc(anio, mes, dig):
    dias = CRON.get(anio, CRON[2026]).get(mes, [28]*11)
    dia  = dias[min(dig,10)]
    mv,av = mes+1,anio
    if mv>12: mv,av=1,anio+1
    try:    return date(av,mv,dia)
    except: return date(av,mv,28)

def fvenc_ij(anio, mes, dig):
    m2,a2 = mes+1,anio
    if m2>12: m2,a2=1,anio+1
    return fvenc(a2,m2,dig)

def ctim(imp, dias): return round(imp*TIM_D*max(dias,0),2)
def cmulta(anio):    return 0.0  # No se calcula multa exacta; solo se alerta para revisión de gradualidad

def num(s):
    s=str(s).strip().strip("()").lstrip("-").replace(" ","")
    if not s or s in ["","nan","None","-"]: return 0.0
    hc,hd=","in s,"."in s
    if hc and hd:
        s=s.replace(",","") if s.index(",")<s.index(".") else s.replace(".","").replace(",",".")
    elif hc:
        p=s.split(",")
        s=s.replace(",","") if len(p)==2 and len(p[1])==3 else s.replace(",",".")
    elif hd:
        p=s.split(".")
        if len(p)==2 and len(p[1])==3: s=s.replace(".","")
    try: return float(s)
    except: return 0.0

def es_pago(s):
    s=str(s).strip()
    return s.startswith("(") or s.startswith("-")

# ══════════════════════════════════════════════════════════════════════════════
# LECTURA GOOGLE SHEET
# ══════════════════════════════════════════════════════════════════════════════
def sid(url):
    m=re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)",url)
    return m.group(1) if m else ""

def leer_sheet(sheet_id):
    for pestana in ["REPORTE DE IMPUESTOS","Sheet1",""]:
        try:
            p=pestana.replace(" ","%20")
            url=f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p}"
            r=requests.get(url,timeout=12)
            if r.status_code==200 and len(r.text)>200:
                df=pd.read_csv(StringIO(r.text),header=None,dtype=str)
                if len(df)>5: return df
        except: pass
    return None

# ══════════════════════════════════════════════════════════════════════════════
# PARSEO REPORTE DE IMPUESTOS
# ══════════════════════════════════════════════════════════════════════════════
SMAP=[
    (r"SALDO IGV|^IGV\b",                                         "1011","A"),
    (r"IMPUESTO A LA RENTA|RENTA.*MYPE|RENTA.*RER|RENTA.*GENE",  "3121","B"),
    (r"RENTA.*4TA|CUARTA",                                        "3042","B"),
    (r"RENTA.*5TA|QUINTA",                                        "3052","B"),
    (r"RENTA.*2DA|SEGUNDA",                                       "3022","B"),
    (r"\bESSALUD\b",                                              "5210","C"),
    (r"\bONP\b",                                                  "5310","C"),
    (r"\bITAN\b",                                                 "3038","B"),
    (r"FRACCIONAMIENTO|FRACC.*ART",                               "8021","F"),
    (r"\bAFP\b",                                                  "AFP","C"),
    (r"\bSIS\b",                                                  "SIS","C"),
]

HDRS={"MESES","PERIODO","SE PAGÓ","SE PAGO","PENDIENTE DE PAGO",
      "IMPORTE PAGADO","N° DE CUOTAS","AMORTIZA","VENCIM.","TOTALES",
      "TOTAL","INTERÉS","INTERES","SALDO","N°","CUOTAS","VENCIM",
      "AMORTIZA.","FECHA PAGADO","FECHA DE PAGO","FECHA"}

def det_sec(txt):
    t=txt.upper().strip()
    am=re.search(r"\b(20[23]\d)\b",t)
    anio=int(am.group(1)) if am else 2026
    for pat,cod,tp in SMAP:
        if re.search(pat,t): return cod,anio,tp
    return None,None,None

def es_hdr(vals):
    txt=" ".join(str(v).upper().strip() for v in vals if v and str(v) not in ["nan",""])
    first=vals[0].strip().upper() if vals and vals[0] else ""
    if first in ["IA"] or (first.isdigit() and 1<=int(first)<=99): return False
    return any(h in txt for h in HDRS)

def pend_fila(vals):
    for i in range(len(vals)-1,-1,-1):
        c=str(vals[i]).strip()
        if not c or c in ["nan","","FRACCIONADO","-"]: continue
        if es_pago(c): continue
        v=num(c)
        if v>=0: return v
    return 0.0

def parsear_reporte(df):
    """
    Parsea el reporte de impuestos.
    REGLA CLAVE: solo procesa secciones que EXISTEN en el reporte.
    Si una sección fue eliminada → esos tributos/períodos no se analizan.
    """
    recs=[]; vistos=set()
    sc=sa=st_=None

    for _,row in df.iterrows():
        vals=[str(v).strip() if pd.notna(v) and str(v) not in ["nan",""] else "" for v in row]
        txt=" ".join(v for v in vals if v)
        if not txt: continue

        cd,ad,td=det_sec(txt)
        if cd: sc,sa,st_=cd,ad,td; continue
        if not sc: continue
        if es_hdr(vals): continue

        v=vals[1:] if vals and vals[0]=="" else vals
        if not v or not v[0]: continue

        # ── Fraccionamiento ───────────────────────────────────────────────────
        if st_=="F":
            cid=v[0].strip().upper()
            if not (cid=="IA" or (cid.isdigit() and 1<=int(cid)<=99)): continue
            total=num(v[4]) if len(v)>4 else 0
            pago_s=v[5].strip() if len(v)>5 else ""
            vcto_s=v[1].strip() if len(v)>1 else ""
            pagada=es_pago(pago_s) and num(pago_s)>0
            pm=num(pago_s) if pagada else 0
            vcto=None
            if re.match(r"\d{1,2}/\d{2}/\d{4}",vcto_s):
                try: vcto=datetime.strptime(vcto_s,"%d/%m/%Y").date()
                except: pass
            ck=("8021",cid,sa)
            if ck in vistos: continue
            vistos.add(ck)
            recs.append({"tipo":"F","codigo":"8021","nombre":TRIBUTO["8021"],
                         "mes_nom":f"CUOTA {cid}","mes_num":0 if cid=="IA" else int(cid),
                         "anio":sa,"declarado":total,"pendiente":0.0 if pagada else total,
                         "pagado_reg":pm,"pagada":pagada,"vcto_sheet":vcto,"igv_justo":None,
                         "es_manual":False})
            continue

        # ── Por mes ───────────────────────────────────────────────────────────
        md=None
        for cel in v[:3]:
            cu=cel.upper().strip()
            for mn,mv in MESES.items():
                if cu==mn or cu.startswith(mn+" "): md=(mn,mv); break
            if md: break
        if not md: continue

        mn,mv=md
        ck=(sc,mn,sa)
        if ck in vistos: continue

        pend=pend_fila(v)
        decl=0.0
        for c in v[1:5]:
            if c and not es_pago(c) and c not in ["FRACCIONADO","-"]:
                vv=num(c)
                if vv>0: decl=vv; break
        if decl==0: decl=pend

        igv_j=None
        if st_=="A" and len(v)>2:
            c=v[2].strip()
            if re.match(r"\d{1,2}/\d{2}/\d{4}$",c):
                try: igv_j=datetime.strptime(c,"%d/%m/%Y").date()
                except: pass

        vistos.add(ck)
        recs.append({"tipo":st_,"codigo":sc,"nombre":TRIBUTO.get(sc,sc),
                     "mes_nom":mn,"mes_num":mv,"anio":sa,
                     "declarado":decl,"pendiente":pend,
                     "pagado_reg":max(decl-pend,0),"pagada":pend==0 and decl>0,
                     "vcto_sheet":None,"igv_justo":igv_j,"es_manual":sc in ("AFP","SIS")})
    return recs

def pdf_a_df(pdf_bytes):
    filas=[]
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for pg in pdf.pages:
                for tbl in pg.extract_tables():
                    if not tbl: continue
                    for row in tbl:
                        v=[str(x or "").strip().replace("\n"," ") for x in row]
                        if any(x for x in v): filas.append(v)
    except Exception as e: st.error(f"Error PDF reporte: {e}")
    if not filas: return pd.DataFrame()
    mc=max(len(r) for r in filas)
    return pd.DataFrame([r+[""]*(mc-len(r)) for r in filas])

# ══════════════════════════════════════════════════════════════════════════════
# PDF SUNAT
# ══════════════════════════════════════════════════════════════════════════════
def parsear_sunat(pdf_bytes):
    filas=[]
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for pg in pdf.pages:
                for tbl in pg.extract_tables():
                    if not tbl or len(tbl)<2: continue
                    h=[str(c or "").lower().replace("\n"," ") for c in tbl[0]]
                    if not any("período" in x or "periodo" in x for x in h): continue
                    if not any("tributo" in x for x in h): continue
                    for row in tbl[1:]:
                        if not row or len(row)<8: continue
                        v=[str(x or "").strip().replace("\n"," ") for x in row]
                        per,ord_,fstr,cod,mstr=v[0],v[2],v[3],v[5],v[7]
                        if not re.match(r"^202[2-9]\d{2}$",per): continue
                        if cod not in TRIBUTO: continue
                        imp=num(mstr)
                        if imp<=0: continue
                        fp=None
                        if re.match(r"\d{1,2}/\d{2}/\d{4}",fstr):
                            try: fp=datetime.strptime(fstr.strip(),"%d/%m/%Y").date()
                            except: pass
                        filas.append({"PERIODO":per,"N_ORDEN":ord_,"COD":cod,"FECHA":fp,"IMPORTE":imp})
    except Exception as e:
        st.error(f"Error PDF SUNAT: {e}"); return pd.DataFrame()
    if not filas: return pd.DataFrame()
    df=pd.DataFrame(filas).drop_duplicates(subset=["N_ORDEN"],keep="first")
    return df.reset_index(drop=True)

def combinar_sunat(archs):
    dfs,noms=[],[]
    for a in archs:
        a.seek(0); df=parsear_sunat(a.read())
        if not df.empty:
            df["_a"]=a.name; dfs.append(df); noms.append(a.name)
        else: st.warning(f"⚠️ Sin pagos en: **{a.name}**")
    if not dfs: return pd.DataFrame(),noms
    c=pd.concat(dfs,ignore_index=True)
    antes=len(c)
    c=c.drop_duplicates(subset=["N_ORDEN"],keep="first")
    if antes-len(c)>0: st.info(f"ℹ️ {antes-len(c)} duplicados eliminados.")
    return c.reset_index(drop=True),noms

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS CENTRAL
#
# REGLA FUNDAMENTAL:
# El REPORTE DE IMPUESTOS es la fuente de verdad.
# Solo se analiza lo que ESTÁ en el reporte.
# Si un pago del extracto SUNAT no tiene sección en el reporte → se ignora
# (significa que ya fue cerrado y eliminado porque todo estaba OK).
#
# Categorías de salida:
#   1. VENCIDOS CON MULTA  — retenciones sin pagar, vencidas (ONP/R5ta/R4ta/R2da)
#   2. VENCIDOS SIN MULTA  — IGV/Renta/EsSalud/Fracc sin pagar, vencidos
#   3. FALTA ACTUALIZAR    — pago en SUNAT pero no registrado en reporte activo
#   4. PAGADOS CON ATRASO  — registrado pero pagado fuera de fecha (TIM generado)
#   5. AL DÍA              — pagado y registrado a tiempo
# ══════════════════════════════════════════════════════════════════════════════
def analizar(extracto, reporte, digito, igv_justo, hoy):
    vm=[]   # 1. vencidos con multa
    vn=[]   # 2. vencidos sin multa
    act=[]  # 3. falta actualizar
    atr=[]  # 4. pagado con atraso
    ok=[]   # 5. al día
    vistos=set()

    # Construir índice del reporte para búsquedas rápidas
    # (cod, mes_nom, anio) → registro
    idx_reporte = {}
    for r in reporte:
        if r["tipo"]!="F":
            key=(r["codigo"],r["mes_nom"],r["anio"])
            idx_reporte[key]=r
    # Índice de fraccionamientos por monto
    fracc_reporte=[r for r in reporte if r["codigo"]=="8021"]

    # ── PASO 1: analizar cada pago del extracto SUNAT ─────────────────────────
    for _,fila in extracto.iterrows():
        per=str(fila["PERIODO"]).strip()
        if not re.match(r"^202[2-9]\d{2}$",per): continue
        anio,mes=int(per[:4]),int(per[4:6])
        cod=str(fila["COD"]).strip()
        if cod not in TRIBUTO: continue
        imp=float(fila["IMPORTE"])
        if imp<=0: continue
        nord=str(fila["N_ORDEN"]).strip()
        fp=fila["FECHA"]
        fecha_pago=fp if isinstance(fp,date) else None
        mn=MNom.get(mes,str(mes))

        # ── REGLA CLAVE: ¿existe este tributo/período en el reporte activo? ──
        if cod=="8021":
            rec_rep=next((r for r in fracc_reporte
                         if r["anio"]==anio and abs(r["declarado"]-imp)<1.0),None)
        else:
            rec_rep=idx_reporte.get((cod,mn,anio))

        # Si NO está en el reporte activo → fue eliminado → IGNORAR completamente
        if rec_rep is None:
            continue

        # ── Calcular vencimiento ──────────────────────────────────────────────
        if cod=="1011" and igv_justo:
            fij=rec_rep.get("igv_justo")
            fv=fij or fvenc_ij(anio,mes,digito); tv="IGV Justo"
        elif cod=="8021":
            fv=rec_rep.get("vcto_sheet"); tv="Fracc"
        else:
            fv=fvenc(anio,mes,digito); tv="Normal"

        # ── ¿Está registrado en el reporte? ──────────────────────────────────
        if cod=="8021":
            ya=rec_rep.get("pagada",False)
        else:
            ya=rec_rep.get("pagada",False) or rec_rep.get("pagado_reg",0)>0

        # ── Calcular atraso ───────────────────────────────────────────────────
        dt=max((fecha_pago-fv).days,0) if fecha_pago and fv else 0
        tarde=dt>0
        tim_v=ctim(imp,dt) if tarde else 0.0
        mul_v=cmulta(anio) if (tarde and cod in CON_MULTA) else 0.0

        # ── Instrucción interna ───────────────────────────────────────────────
        pest={"1011":f"IGV {anio}","5210":"ESSALUD","5310":"ONP",
              "3052":"RENTA_5TA","3042":"RENTA_4TA","3038":"ITAN",
              "8021":"FRACCIONAMIENTOS"}.get(cod,f"RENTA {anio}")
        fp_s=fecha_pago.strftime("%d/%m/%Y") if fecha_pago else ""
        instr=(f'Pestaña "{pest}" → {mn} → SE PAGÓ = S/ {imp:,.2f} · {fp_s}'
               if cod!="8021" else f"Fracc → registrar S/ {imp:,.2f} pagado {fp_s}")

        base={"codigo":cod,"nombre":TRIBUTO[cod],
              "periodo":f"{mn}-{anio}","mes":mn,"mes_num":mes,"anio":anio,
              "importe":imp,"fecha_pago":fecha_pago,"fecha_venc":fv,"tipo_venc":tv,
              "dias_tarde":dt,"tarde":tarde,"tim":tim_v,"multa":mul_v,
              "tiene_multa":cod in CON_MULTA,"n_orden":nord,"ya_reg":ya,
              "instruccion":instr,"es_manual":False}

        vistos.add((cod,mn,anio))

        if not ya:
            act.append(base)
        elif tarde and (tim_v>0 or mul_v>0):
            atr.append(base)
        else:
            ok.append(base)

    # ── PASO 2: detectar pendientes del reporte no vistos en el SUNAT ─────────
    for r in reporte:
        cod=r["codigo"]; mn=r["mes_nom"]; mv=r["mes_num"]; anio=r["anio"]
        saldo=r["pendiente"]
        es_manual=r.get("es_manual",False)

        if saldo<=0: continue

        # Fraccionamiento: cuotas vencidas sin pagar
        if cod=="8021":
            if r.get("pagada"): continue
            fv=r.get("vcto_sheet")
            if not fv or fv>=hoy: continue
            # ¿Ya aparece en el extracto SUNAT?
            ya_ext=any(str(f["COD"])=="8021" and int(str(f["PERIODO"])[:4])==anio
                      and abs(f["IMPORTE"]-r["declarado"])<1.0
                      for _,f in extracto.iterrows()) if not extracto.empty else False
            if ya_ext: continue
            dv=(hoy-fv).days
            vn.append({
                "codigo":"8021","nombre":TRIBUTO["8021"],
                "periodo":f"{mn}-{anio}","mes":mn,"mes_num":mv,"anio":anio,
                "importe":r["declarado"],"fecha_pago":None,
                "fecha_venc":fv,"tipo_venc":"Fracc",
                "dias_tarde":dv,"tarde":True,"tim":ctim(r["declarado"],dv),"multa":0,
                "tiene_multa":False,"n_orden":"","ya_reg":True,
                "instruccion":f"{mn} S/{r['declarado']:,.2f} — venció {fv.strftime('%d/%m/%Y')} — {dv}d",
                "es_manual":False})
            continue

        if (cod,mn,anio) in vistos: continue

        # AFP/SIS: pendiente manual
        if es_manual:
            vn.append({
                "codigo":cod,"nombre":TRIBUTO.get(cod,cod),
                "periodo":f"{mn}-{anio}","mes":mn,"mes_num":mv,"anio":anio,
                "importe":saldo,"fecha_pago":None,"fecha_venc":None,"tipo_venc":"Manual",
                "dias_tarde":0,"tarde":False,"tim":0,"multa":0,
                "tiene_multa":False,"n_orden":"","ya_reg":True,
                "instruccion":f"Pago manual pendiente S/ {saldo:,.2f}",
                "es_manual":True})
            continue

        # Tributos normales vencidos
        if cod=="1011" and igv_justo and r["igv_justo"]:
            fv=r["igv_justo"]; tv="IGV Justo"
        elif cod=="1011" and igv_justo:
            fv=fvenc_ij(anio,mv,digito); tv="IGV Justo"
        else:
            fv=fvenc(anio,mv,digito); tv="Normal"

        if fv>=hoy: continue

        dv=(hoy-fv).days
        tim_v=ctim(saldo,dv)
        mul_v=cmulta(anio) if cod in CON_MULTA else 0.0
        item={
            "codigo":cod,"nombre":TRIBUTO.get(cod,""),
            "periodo":f"{mn}-{anio}","mes":mn,"mes_num":mv,"anio":anio,
            "importe":saldo,"fecha_pago":None,"fecha_venc":fv,"tipo_venc":tv,
            "dias_tarde":dv,"tarde":True,"tim":tim_v,"multa":mul_v,
            "tiene_multa":cod in CON_MULTA,"n_orden":"","ya_reg":True,
            "instruccion":f"Declarado S/{r['declarado']:,.2f} — sin pagar — {dv} días vencido",
            "es_manual":False}
        if cod in CON_MULTA: vm.append(item)
        else:                vn.append(item)

    return {
        "vm":sorted(vm, key=lambda x:x["dias_tarde"],reverse=True),
        "vn":sorted(vn, key=lambda x:(0 if x.get("es_manual") else 1,
                                      -x["dias_tarde"])),
        "act":act,
        "atr":sorted(atr,key=lambda x:x["dias_tarde"],reverse=True),
        "ok":ok,
    }

# ══════════════════════════════════════════════════════════════════════════════
# PRIORIDADES DE PAGO — orden técnico correcto para el cliente
# 1. AFP/ONP — retención de sueldo, riesgo penal, NO fraccionable
# 2. Retenciones (R5ta/R4ta/R2da) — multa 100% si detecta SUNAT
# 3. IGV — importante pero fraccionable
# 4. Renta MYPE/RER — fraccionable
# 5. EsSalud — flexible en cobranza
# 6. Fraccionamiento — ya acordado, renegociable
# 7. SIS/ITAN — menor urgencia
# ══════════════════════════════════════════════════════════════════════════════
# Prioridades confirmadas por Contadeus International SAC:
# 1. Retenciones (R5ta/R4ta/R2da) — multa 100% + riesgo penal
# 2. ONP — retención previsional trabajador
# 3. Fraccionamiento — compromiso firmado con SUNAT, romperlo reactiva deuda original
# 4. AFP — retención previsional, cobranza judicial
# 5. EsSalud
# 6. Renta MYPE/RER/General — pagos a cuenta, fraccionable
# 7. IGV — fraccionable
# 8. SIS — cronograma propio, seguimiento independiente
PRIORIDAD_PAGO = {
    "3052": 1, "3042": 2, "3022": 3,  # retenciones — multa 100% + riesgo penal
    "5310": 4,             # ONP — retención previsional
    "8021": 5,             # Fraccionamiento — compromiso firmado SUNAT
    "AFP":  6,             # AFP — retención previsional
    "5210": 7,             # EsSalud
    "3121": 8, "3111": 8, "3031": 8,  # Renta MYPE/RER/General — fraccionable
    "1011": 9,             # IGV — fraccionable
    "3038": 10,            # ITAN
    "SIS":  99,            # SIS — cronograma propio, seguimiento independiente
}

CONCEPTO_CLIENTE = {
    "AFP":  "AFP",
    "5310": "ONP",
    "3052": "Renta de 5ta categoría",
    "3042": "Renta de 4ta categoría",
    "3022": "Renta de 2da categoría",
    "1011": "IGV",
    "3121": "Impuesto a la Renta",
    "3111": "Impuesto a la Renta",
    "3031": "Impuesto a la Renta",
    "5210": "EsSalud",
    "8021": "Cuota de fraccionamiento",
    "SIS":  "Seguro Integral de Salud",
    "3038": "ITAN",
}

MENSAJE_CLIENTE = {
    "AFP":  "Puede generar gastos adicionales de cobranza judicial.",
    "5310": "Puede generar multas e intereses.",
    "3052": "Puede generar multas e intereses.",
    "3042": "Puede generar multas e intereses.",
    "3022": "Puede generar multas e intereses.",
    "1011": "Incluye intereses acumulados a la fecha.",
    "3121": "Incluye intereses acumulados a la fecha.",
    "3111": "Incluye intereses acumulados a la fecha.",
    "3031": "Incluye intereses acumulados a la fecha.",
    "5210": "Incluye intereses acumulados a la fecha.",
    "8021": "Cuota pendiente de pago.",
    "3038": "Pendiente de pago.",
    "SIS":  "Pendiente de pago.",
}

ALERTA_INTERNA_MULTA = "Afecto a multa - revisar gradualidad"

def generar_informe_cliente(empresa, ruc, res, hoy):
    vm=res["vm"]; vn=res["vn"]
    todos = vm + vn

    lines=[]
    lines.append("📊 *Reporte Tributario*")
    if ruc:
        lines.append(f"RUC {ruc} · {hoy.strftime('%d/%m/%Y')}")
    else:
        lines.append(hoy.strftime('%d/%m/%Y'))
    lines.append("")

    if not todos:
        lines.append("Estimado cliente:")
        lines.append("")
        lines.append("✅ Sus obligaciones tributarias se encuentran al día.")
        lines.append("No hay pagos pendientes a la fecha.")
        lines.append("")
        lines.append("*El equipo de Contadeus International*")
        return "\n".join(lines)

    lines.append("Estimado cliente:")
    lines.append("A continuación le presentamos el estado actualizado de sus obligaciones pendientes:")
    lines.append("")
    lines.append("🔴 *Obligaciones con regularización prioritaria*")
    lines.append("")

    # Ordenar por prioridad real (no por monto)
    ordenados = sorted(todos,
        key=lambda x: (PRIORIDAD_PAGO.get(x["codigo"], 99), -x["dias_tarde"])
    )

    total = 0
    for i, r in enumerate(ordenados, 1):
        monto = round(r["importe"] + r["tim"] + r["multa"])
        total += monto
        concepto = CONCEPTO_CLIENTE.get(r["codigo"], r["nombre"])
        periodo  = r["periodo"]

        # Mensaje breve para cliente final, sin tecnicismos ni multas exactas.
        nota = MENSAJE_CLIENTE.get(r["codigo"], "Pendiente de regularización.")
        detalle = f"_({nota})_" if nota else ""

        lines.append(f"{i}. *{concepto} {periodo}* — S/ {monto:,} {detalle}".strip())

    lines.append("")
    lines.append(f"💰 *Total pendiente de regularización: S/ {total:,}*")
    lines.append("")

    # Orden recomendado — conciso
    orden_parts = []
    for i, r in enumerate(ordenados, 1):
        concepto = CONCEPTO_CLIENTE.get(r["codigo"], r["nombre"])
        orden_parts.append(f"{i}️⃣ {concepto} {r['periodo']}")
    lines.append("📌 *Orden recomendado de atención:*")
    lines.append("  ".join(orden_parts))
    lines.append("")
    lines.append("Recomendamos atender estas obligaciones según el orden indicado para mantener su empresa al día y evitar contingencias futuras.")
    lines.append("")
    lines.append("Si desea efectuar algún pago, indíquenos cuál y con gusto le enviaremos el NPS o la guía correspondiente.")
    lines.append("")
    lines.append("Quedamos atentos.")
    lines.append("")
    lines.append("*El equipo de Contadeus International*")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════════════════
# EXCEL
# ══════════════════════════════════════════════════════════════════════════════
def gen_excel(empresa,ruc,res,extracto,noms,fuente):
    buf=BytesIO()
    vm=res["vm"]; vn=res["vn"]; act=res["act"]; atr=res["atr"]; ok_=res["ok"]
    t_urgente=sum(r["importe"]+r["tim"]+r["multa"] for r in vm+vn)

    with pd.ExcelWriter(buf,engine="openpyxl") as w:
        hs=datetime.now().strftime("%d/%m/%Y %H:%M")
        anios=sorted({r["anio"] for r in vm+vn+act+atr+ok_})
        pd.DataFrame({"Campo":[
            "Empresa","RUC","Fecha análisis","PDF SUNAT","Fuente reporte",
            "Años analizados","Vencidos con multa","Vencidos sin pagar",
            "Falta actualizar reporte","Pagados con atraso","Al día","Total urgente S/",
        ],"Valor":[
            empresa,ruc,hs,", ".join(noms),fuente,", ".join(str(a) for a in anios),
            len(vm),len(vn),len(act),len(atr),len(ok_),f"{t_urgente:,.2f}",
        ]}).to_excel(w,sheet_name="RESUMEN",index=False)

        def rows(lst,extras):
            out=[]
            for r in lst:
                d={"Año":r["anio"],"Tributo":r["nombre"],"Período":r["periodo"],
                   "Importe S/":r["importe"],
                   "Fecha pago":r["fecha_pago"].strftime("%d/%m/%Y") if r.get("fecha_pago") else "",
                   "N° Orden":r.get("n_orden","")}
                for k in extras:
                    if k=="Vencimiento": d[k]=r["fecha_venc"].strftime("%d/%m/%Y") if r.get("fecha_venc") else ""
                    elif k=="Días": d[k]=r["dias_tarde"]
                    elif k=="TIM S/": d[k]=r["tim"]
                    elif k=="Multa S/": d[k]=ALERTA_INTERNA_MULTA if r.get("tiene_multa") else "No aplica"
                    elif k=="Total S/": d[k]=r["importe"]+r["tim"]
                    elif k=="Instrucción": d[k]=r.get("instruccion","")
                    elif k=="Tipo": d[k]=r["tipo_venc"]
                out.append(d)
            return out

        if vm:  pd.DataFrame(rows(vm, ["Vencimiento","Días","TIM S/","Multa S/","Total S/"])).to_excel(w,sheet_name="🔴 VENCIDOS+MULTA",index=False)
        if vn:  pd.DataFrame(rows(vn, ["Vencimiento","Días","TIM S/","Total S/"])).to_excel(w,sheet_name="🔴 VENCIDOS SIN PAGAR",index=False)
        if act: pd.DataFrame(rows(act,["Instrucción","Días","TIM S/","Multa S/"])).to_excel(w,sheet_name="🟡 ACTUALIZAR REPORTE",index=False)
        if atr: pd.DataFrame(rows(atr,["Vencimiento","Días","TIM S/","Multa S/","Tipo"])).to_excel(w,sheet_name="🟠 PAGADOS CON ATRASO",index=False)
        if ok_: pd.DataFrame(rows(ok_,["Vencimiento","Tipo"])).to_excel(w,sheet_name="✅ AL DÍA",index=False)
        extracto.to_excel(w,sheet_name="EXTRACTO SUNAT",index=False)
    return buf.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hdr">
  <h1>📊 Contadeus — Revisor Tributario</h1>
  <p>Solo analiza lo que está en el reporte activo · Prioriza por urgencia · Genera informe listo para el cliente</p>
</div>
""", unsafe_allow_html=True)

SK=["listo","res","empresa","ruc","ext_df","noms","fuente"]
for k in SK:
    if k not in st.session_state:
        st.session_state[k]=(False if k=="listo" else [] if k=="noms" else
                             pd.DataFrame() if k=="ext_df" else
                             {} if k=="res" else "")

HOY=date.today()

# ── RESULTADOS ──────────────────────────────────────────────────────────────
if st.session_state.listo and st.session_state.res:
    res=st.session_state.res
    vm=res["vm"]; vn=res["vn"]; act=res["act"]; atr=res["atr"]; ok_=res["ok"]
    empresa=st.session_state.empresa; ruc=st.session_state.ruc
    t_urgente=sum(r["importe"]+r["tim"]+r["multa"] for r in vm+vn)
    anios=sorted({r["anio"] for r in vm+vn+act+atr+ok_},reverse=True)

    st.markdown(f'<div class="emp">🏢 {empresa}{f" · RUC {ruc}" if ruc else ""}'
                f' · Años: {" · ".join(str(a) for a in anios)}</div>',
                unsafe_allow_html=True)

    # KPIs
    for col,(n,lbl,color) in zip(st.columns(5),[
        (len(vm),"Vencidos + multa","red"),(len(vn),"Vencidos sin pagar","red"),
        (len(act),"Actualizar reporte","amb"),(len(ok_),"Al día","grn"),
        (f"S/ {t_urgente:,.0f}","Total urgente","red")]):
        with col:
            st.markdown(f'<div class="kpi"><div class="n {color}">{n}</div>'
                        f'<div class="l">{lbl}</div></div>',unsafe_allow_html=True)

    st.markdown('<div class="sep"></div>',unsafe_allow_html=True)

    # ── 1. VENCIDOS CON MULTA ────────────────────────────────────────────────
    if vm:
        st.markdown('<div class="stitle">🚨 URGENTE — Retenciones vencidas afectas a multa</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="card cr">ONP / Renta 5ta / Renta 4ta / Renta 2da vencidos. '
                    'Estos conceptos pueden generar <strong>multas e intereses</strong>. '
                    'Contadeus debe revisar la gradualidad antes de informar un importe de multa.</div>',unsafe_allow_html=True)
        for anio in anios:
            items=[r for r in vm if r["anio"]==anio]
            if not items: continue
            st.markdown(f'<div class="yr">📅 {anio}</div>',unsafe_allow_html=True)
            for r in items:
                costo=r["importe"]+r["tim"]+r["multa"]
                vs=r["fecha_venc"].strftime("%d/%m/%Y") if r.get("fecha_venc") else "N/D"
                st.markdown(f"""<div class="card cr">
                    <strong>🚨 {r['nombre']} — {r['periodo']}</strong><br>
                    💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp; Venció: <strong>{vs}</strong>
                    &nbsp;·&nbsp; <strong>{r['dias_tarde']} días</strong><br>
                    <span class="badge br">Afecto a multa</span>
                    <span class="badge ba">TIM S/ {r['tim']:,.2f}</span>
                    <span class="badge br">Total sin multa: S/ {costo:,.2f}</span>
                </div>""",unsafe_allow_html=True)

    # ── 2. VENCIDOS SIN MULTA ────────────────────────────────────────────────
    if vn:
        st.markdown('<div class="sep"></div>',unsafe_allow_html=True)
        st.markdown('<div class="stitle">🔴 Impuestos vencidos sin pagar</div>',
                    unsafe_allow_html=True)
        for anio in anios:
            items=[r for r in vn if r["anio"]==anio]
            if not items: continue
            st.markdown(f'<div class="yr">📅 {anio}</div>',unsafe_allow_html=True)
            for r in items:
                if r.get("es_manual"):
                    st.markdown(f"""<div class="card cp">
                        <strong>📋 {r['nombre']} — {r['periodo']}</strong>
                        &nbsp;·&nbsp; S/ {r['importe']:,.2f}
                        &nbsp;·&nbsp; <span class="badge bp">Pago manual</span>
                    </div>""",unsafe_allow_html=True)
                else:
                    costo=r["importe"]+r["tim"]
                    vs=r["fecha_venc"].strftime("%d/%m/%Y") if r.get("fecha_venc") else "N/D"
                    st.markdown(f"""<div class="card cr">
                        <strong>🔴 {r['nombre']} — {r['periodo']}</strong><br>
                        💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp; Venció: <strong>{vs}</strong>
                        &nbsp;·&nbsp; <strong>{r['dias_tarde']} días</strong><br>
                        <span class="badge ba">TIM S/ {r['tim']:,.2f}</span>
                        <span class="badge br">Total: S/ {costo:,.2f}</span>
                    </div>""",unsafe_allow_html=True)

    # ── 3. FALTA ACTUALIZAR ──────────────────────────────────────────────────
    if act:
        st.markdown('<div class="sep"></div>',unsafe_allow_html=True)
        st.markdown('<div class="stitle">🟡 Falta registrar en el reporte de impuestos</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="card ca">Pagados en SUNAT, presentes en el reporte activo, '
                    'pero sin registrar el pago. <strong>Actualizar antes de enviar al cliente.</strong></div>',
                    unsafe_allow_html=True)
        for anio in anios:
            items=[r for r in act if r["anio"]==anio]
            if not items: continue
            st.markdown(f'<div class="yr">📅 {anio}</div>',unsafe_allow_html=True)
            for r in items:
                atr_txt=""
                if r["tarde"]:
                    ml=f'<span class="badge br">Afecto a multa</span>' if r.get("tiene_multa") else ""
                    atr_txt=(f'<br>{ml}<span class="badge ba">TIM S/ {r["tim"]:,.2f}</span>'
                            f' — {r["dias_tarde"]} días tarde')
                fp_s=r["fecha_pago"].strftime("%d/%m/%Y") if r.get("fecha_pago") else "N/D"
                st.markdown(f"""<div class="card ca">
                    <strong>📌 {r['nombre']} — {r['periodo']}</strong><br>
                    💰 S/ {r['importe']:,.2f} &nbsp;·&nbsp; Pagado: <strong>{fp_s}</strong>
                    &nbsp;·&nbsp; N° {r['n_orden']}{atr_txt}<br>
                    <span style="color:#92400E;">▶ {r['instruccion']}</span>
                </div>""",unsafe_allow_html=True)

    # ── 4. PAGADOS CON ATRASO ────────────────────────────────────────────────
    if atr:
        st.markdown('<div class="sep"></div>',unsafe_allow_html=True)
        with st.expander(f"🟠 {len(atr)} pagados con atraso — TIM y alertas de multa"):
            for anio in anios:
                items=[r for r in atr if r["anio"]==anio]
                if not items: continue
                st.markdown(f'<div class="yr">📅 {anio}</div>',unsafe_allow_html=True)
                for r in items:
                    ml='⚠️ Afecto a multa - revisar gradualidad' if r.get("tiene_multa") else "Solo TIM"
                    vs=r["fecha_venc"].strftime("%d/%m/%Y") if r.get("fecha_venc") else ""
                    fp_s=r["fecha_pago"].strftime("%d/%m/%Y") if r.get("fecha_pago") else ""
                    st.markdown(f"""<div class="card co">
                        <strong>{r['nombre']} — {r['periodo']}</strong>
                        &nbsp;·&nbsp; S/ {r['importe']:,.2f}
                        &nbsp;·&nbsp; Pagado: {fp_s} &nbsp;·&nbsp; Vencía: {vs}
                        &nbsp;·&nbsp; {r['dias_tarde']}d tarde &nbsp;·&nbsp; {ml}
                        &nbsp;·&nbsp; TIM S/ {r['tim']:,.2f} &nbsp;·&nbsp; ({r['tipo_venc']})
                    </div>""",unsafe_allow_html=True)

    # ── 5. AL DÍA ────────────────────────────────────────────────────────────
    if ok_:
        with st.expander(f"✅ {len(ok_)} pagos al día"):
            for r in ok_:
                fp_s=r["fecha_pago"].strftime("%d/%m/%Y") if r.get("fecha_pago") else ""
                st.markdown(f'<div class="card cg">✓ {r["nombre"]} — {r["periodo"]}'
                            f' — S/ {r["importe"]:,.2f} — {fp_s}</div>',
                            unsafe_allow_html=True)

    if not vm and not vn and not act and not atr:
        st.markdown('<div class="card cg">✅ <strong>Todo al día.</strong> No hay pendientes.</div>',
                    unsafe_allow_html=True)

    # ── INFORME PARA EL CLIENTE ───────────────────────────────────────────────
    st.markdown('<div class="sep"></div>',unsafe_allow_html=True)
    st.markdown('<div class="stitle">📱 Mensaje para el cliente — copiar y pegar en WhatsApp</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="card cb" style="margin-bottom:8px;">Solo incluye lo que el cliente '
                'necesita saber: impuestos pendientes de pago con montos y prioridad. '
                'No incluye trabajo interno.</div>',unsafe_allow_html=True)

    informe=generar_informe_cliente(empresa,ruc,res,HOY)
    st.text_area("",value=informe,height=320,label_visibility="collapsed")
    st.caption("💡 Clic dentro del texto → Ctrl+A → Ctrl+C → pegar en WhatsApp")

    # ── BOTONES ───────────────────────────────────────────────────────────────
    st.markdown('<div class="sep"></div>',unsafe_allow_html=True)
    col_dl,col_nx=st.columns(2)
    with col_dl:
        eb=gen_excel(empresa,ruc,res,st.session_state.ext_df,
                     st.session_state.noms,st.session_state.fuente)
        n=empresa[:20].replace(" ","_") if empresa else ruc
        st.download_button("⬇️  Descargar reporte Excel completo",data=eb,
                          file_name=f"Contadeus_{n}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          use_container_width=True,type="primary")
    with col_nx:
        if st.button("➡️  Analizar otra empresa",use_container_width=True):
            for k in SK:
                st.session_state[k]=(False if k=="listo" else [] if k=="noms" else
                                     pd.DataFrame() if k=="ext_df" else
                                     {} if k=="res" else "")
            st.rerun()
    st.markdown('<div class="card cb">💡 <strong>Descarga el Excel antes de pasar a otra empresa.</strong></div>',
                unsafe_allow_html=True)

# ── FORMULARIO ──────────────────────────────────────────────────────────────
else:
    col_f,col_h=st.columns([3,2])
    with col_f:
        st.markdown("### 🏢 Datos de la empresa")
        ruc_inp=st.text_input("RUC (11 dígitos)",placeholder="20613979779")
        digito_calc=None
        if ruc_inp and len(ruc_inp.strip())==11 and ruc_inp.strip().isdigit():
            digito_calc=int(ruc_inp.strip()[-1])
            st.markdown(f'<div class="card cb" style="font-size:.82rem;padding:7px 12px;">'
                        f'✓ Dígito RUC: <strong>{digito_calc}</strong> — '
                        f'cronograma SUNAT 2022–2026 calculado</div>',
                        unsafe_allow_html=True)
        elif ruc_inp: st.warning("El RUC debe tener 11 dígitos.")

        empresa_inp=st.text_input("Nombre (opcional)",placeholder="TDD INVERSIONES S.A.C.")
        igv_chk=st.checkbox("✅ Acogida a IGV Justo (Ley 30524)",value=True)

        st.markdown("")
        st.markdown("### 📄 PDF 1 — Extracto SUNAT")
        st.caption("SUNAT SOL → Mis declaraciones y pagos → Reporte electrónico → PDF. Puedes subir varios años.")
        arch_s=st.file_uploader("",type=["pdf"],accept_multiple_files=True,
                                label_visibility="collapsed",key="us")
        if arch_s:
            st.markdown(f'<div class="card cg" style="font-size:.82rem;padding:7px 12px;">'
                        f'📄 {len(arch_s)} PDF(s): {" · ".join(a.name for a in arch_s)}</div>',
                        unsafe_allow_html=True)

        st.markdown("")
        st.markdown("### 📊 Reporte de Impuestos del cliente")
        st.caption("Solo se analiza lo que esté activo en el reporte. "
                   "Si eliminaste secciones ya cerradas, el sistema las ignora correctamente.")
        tab_s,tab_p=st.tabs(["🔗 Google Sheet (link)","📁 PDF exportado"])
        with tab_s:
            su=st.text_input("",placeholder="https://docs.google.com/spreadsheets/d/...",
                            label_visibility="collapsed",key="su_inp")
        with tab_p:
            ar=st.file_uploader("",type=["pdf"],accept_multiple_files=False,
                               label_visibility="collapsed",key="ur")
            if ar:
                st.markdown(f'<div class="card cg" style="font-size:.82rem;padding:7px 12px;">'
                            f'📊 {ar.name}</div>',unsafe_allow_html=True)

        st.markdown("")
        if st.button("🔍  Analizar",type="primary",use_container_width=True):
            err=[]
            if not ruc_inp.strip() or len(ruc_inp.strip())!=11: err.append("RUC inválido.")
            if not arch_s: err.append("Sube el PDF de SUNAT.")
            if not su.strip() and not ar: err.append("Proporciona el link del Sheet o el PDF del reporte.")
            for e in err: st.error(e)

            if not err and digito_calc is not None:
                ef=empresa_inp.strip() or ruc_inp.strip()
                rdf=None; fuente=""

                if su.strip():
                    sID=sid(su)
                    if not sID: st.error("Link inválido."); st.stop()
                    with st.spinner("Leyendo Google Sheet..."):
                        rdf=leer_sheet(sID); fuente=f"Sheet ({su[-35:]})"
                    if rdf is None:
                        st.error("No se pudo leer el Sheet. Verifica que esté compartido como "
                                 "'Cualquier persona con el link puede ver'."); st.stop()
                elif ar:
                    with st.spinner("Leyendo PDF reporte..."):
                        ar.seek(0); rdf=pdf_a_df(ar.read()); fuente=ar.name
                    if rdf is None or rdf.empty:
                        st.error("No se pudo leer el PDF del reporte."); st.stop()

                with st.spinner(f"Procesando {len(arch_s)} PDF(s) SUNAT..."):
                    edf,noms=combinar_sunat(arch_s)
                    if edf.empty: st.error("Sin pagos en el PDF SUNAT."); st.stop()

                with st.spinner("Analizando 2022–2026..."):
                    rp=parsear_reporte(rdf)
                    resultado=analizar(edf,rp,digito_calc,igv_chk,HOY)

                if sum(len(v) for v in resultado.values())==0:
                    st.info("Sin registros para analizar.")
                else:
                    st.session_state.update({
                        "listo":True,"res":resultado,"empresa":ef,"ruc":ruc_inp.strip(),
                        "ext_df":edf,"noms":noms,"fuente":fuente})
                    st.rerun()

    with col_h:
        st.markdown("""<div class="card cb" style="margin-top:8px;">
            <strong>📋 Cómo funciona</strong><br><br>
            El reporte de impuestos es la <strong>fuente de verdad</strong>.<br>
            Si eliminaste una sección porque ya estaba todo pagado
            → el sistema la ignora, no genera falsas alertas.<br><br>
            <strong>Produce 5 categorías:</strong><br>
            🚨 Retenciones vencidas (multa adicional)<br>
            🔴 Impuestos vencidos sin pagar<br>
            🟡 Pagos sin registrar en el reporte<br>
            🟠 Pagados con atraso (TIM generado)<br>
            ✅ Al día
        </div>""",unsafe_allow_html=True)

        st.markdown("""<div class="card cr" style="margin-top:10px;">
            <strong>⚠️ Retenciones afectas a multa</strong><br>
            ONP · Renta 5ta · Renta 4ta · Renta 2da<br>
            <em>El sistema alerta la contingencia; Contadeus revisa gradualidad antes de calcular la multa.</em>
        </div>""",unsafe_allow_html=True)

        st.markdown("""<div class="card cg" style="margin-top:10px;">
            <strong>📅 Cronogramas verificados</strong><br>
            2022 · 2023 · 2024 · 2025 · 2026<br>
            Fuente: sunat.gob.pe + El Peruano
        </div>""",unsafe_allow_html=True)

