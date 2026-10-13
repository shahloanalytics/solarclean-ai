"""SolarClean AI 2.0 | Premium UI. Scientific scenario prototype, not a certified controller."""
import io
from datetime import date
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from solarclean import validate_data, estimate_energy_gap, cleaning_economics, build_report, compare_strategies
from intelligence import data_diagnostics, decision, sensitivity, scenario_forecast, strategy_scenarios

st.set_page_config(page_title="SolarClean AI | Intelligence Studio", page_icon="☀️", layout="wide", initial_sidebar_state="expanded")

# HTML below is fixed developer-controlled markup (not derived from CSV inputs).
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--sc-ink:#13273b;--sc-teal:#007e78;--sc-border:#e3ebf0;--sc-bg:#f5f8fb}
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif}
.stApp{background:var(--sc-bg);color:var(--sc-ink)}
.block-container{max-width:1460px;padding-top:1.15rem;padding-bottom:4rem}
h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;letter-spacing:-.045em;color:var(--sc-ink)!important}
h1{font-weight:800!important}
[data-testid="stSidebar"]{background:#102637!important;border-right:1px solid #274657}
[data-testid="stSidebar"] *{color:#eef5f8!important}
[data-testid="stSidebar"] [data-baseweb="input"], [data-testid="stSidebar"] [data-baseweb="select"], [data-testid="stSidebar"] input{background:#203c50!important;border-color:#355669!important}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-weight:500!important;color:#c4d7e0!important}
[data-testid="stSidebar"] div[data-testid="stSliderThumbValue"]{color:#fff!important}
[data-testid="stSidebar"] hr{border-color:#315061}
.hero{padding:32px 36px;border-radius:22px;background:linear-gradient(117deg,#102e42 2%,#075b62 64%,#087a71 100%);color:#fff;margin-bottom:20px;position:relative;overflow:hidden;box-shadow:0 14px 33px rgba(9,49,66,.15)}
.hero:after{content:'';position:absolute;right:-70px;top:-150px;width:350px;height:350px;border:1px solid #ffffff3b;border-radius:50%;box-shadow:0 0 0 40px #ffffff09,0 0 0 90px #ffffff07}
.hero .eyebrow{font-size:11px;font-weight:800;letter-spacing:.18em;color:#b6e4db;text-transform:uppercase}
.hero h1{font-size:clamp(30px,3.1vw,48px);color:white!important;margin:8px 0 5px;font-weight:800}
.hero p{font-size:15px;color:#d9e9ed;margin-bottom:0;max-width:740px}
.tag{display:inline-block;margin-top:16px;margin-right:8px;border-radius:100px;padding:6px 11px;background:#ffffff19;border:1px solid #ffffff30;color:#e7f4f2;font-size:11px;font-weight:700}
.section-label{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#668392;font-weight:800;margin:22px 0 7px}
.panel-note{padding:13px 17px;border:1px solid #dce9ef;background:#edf5f7;border-radius:11px;color:#355669;font-size:13px;margin:10px 0 18px}
.data-note{padding:13px 17px;background:#fff8e9;border:1px solid #efe1bc;border-radius:11px;color:#7b5c22;font-size:12px;margin-bottom:16px}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--sc-border);border-radius:16px;padding:19px 20px 18px;box-shadow:0 4px 15px #172f4607;min-height:121px}
[data-testid="stMetricLabel"]{color:#6a8090;font-size:12px;font-weight:600}
[data-testid="stMetricValue"]{color:#123147;font-family:'Manrope',sans-serif;font-size:clamp(20px,1.65vw,28px);font-weight:800;letter-spacing:-.055em}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:5px;background:#e9eff3;border-radius:14px;padding:6px;overflow-x:auto}
[data-testid="stTabs"] [data-baseweb="tab"]{height:44px;border-radius:10px;padding:0 16px;font-weight:700;color:#506b7a;white-space:nowrap;font-size:13px}
[data-testid="stTabs"] [aria-selected="true"]{background:#fff!important;color:#006d69!important;box-shadow:0 2px 8px #17374b11}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],[data-testid="stTabs"] [data-baseweb="tab-border"]{display:none}
[data-testid="stTabs"] [data-testid="stVerticalBlock"]{gap:.75rem}
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"]{background:white;border:1px solid var(--sc-border);border-radius:15px;padding:6px;overflow:hidden}
button[kind="primary"]{background:#007e78;border:none;border-radius:10px}
.stDownloadButton button{border-color:#d6e6e8;border-radius:10px;background:white;color:#006d69;font-weight:700}
.small-copy{font-size:12px;color:#778c99;margin:10px 0}
.footer{margin-top:32px;border-top:1px solid #dce7ed;padding-top:14px;color:#7b8e99;font-size:11px}
@media(max-width:760px){.block-container{padding-left:1rem;padding-right:1rem}.hero{padding:23px 21px}.hero h1{font-size:29px}[data-testid="stMetric"]{min-height:108px;padding:13px}}
</style>""", unsafe_allow_html=True)

PLOT_COLORS=['#007e78','#e8a04c','#448bc2','#8a73b8']
def chart_style(fig, height=355):
    fig.update_layout(template='plotly_white',height=height,font_family='DM Sans',font_color='#40596a',
        paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',margin=dict(l=22,r=22,t=57,b=35),
        title_font=dict(size=16,color='#14354a',family='Manrope'),legend_title_text='',
        hoverlabel=dict(bgcolor='#15364a',font_color='white'),
        xaxis=dict(showgrid=False,zeroline=False,linecolor='#e6edf0'),
        yaxis=dict(showgrid=True,gridcolor='#edf2f5',zeroline=False))
    return fig

def section(title,subtitle=None):
    st.markdown(f'<div class="section-label">{title}</div>',unsafe_allow_html=True)
    if subtitle: st.caption(subtitle)

with st.sidebar:
    st.markdown('### ☀️ SolarClean AI')
    st.caption('INTELLIGENCE STUDIO • 2.0')
    st.divider()
    st.markdown('**01 / Energiya va xarajatlar**')
    tariff=st.number_input('Elektr qiymati · so‘m/kWh',min_value=0.,value=1000.,step=100.)
    water_price=st.number_input('Suv narxi · so‘m/litr',min_value=0.,value=10.)
    labor=st.number_input('Mehnat xarajati · so‘m',min_value=0.,value=25000.,step=1000.)
    transport=st.number_input('Transport va boshqa xarajat · so‘m',min_value=0.,value=0.,step=1000.)
    liters=st.number_input('Bir tozalashdagi suv · litr',min_value=0.,value=5.,step=1.)
    st.divider()
    st.markdown('**02 / Tahlil parametrlari**')
    recovery=st.slider('Tiklanish farazi · %',0,100,20)
    horizon=st.select_slider('Ssenariy davri · kun',options=[7,14,30],value=14)
    panel_kw=st.number_input('PV panel quvvati · kW',min_value=0.01,value=0.33)
    last_clean=st.date_input('Oxirgi tozalash sanasi',value=date.today())
    cost=labor+transport+liters*water_price
    st.divider()
    st.metric('Bir martalik tozalash',f'{cost:,.0f} so‘m')
    st.caption('Barcha xarajatlar foydalanuvchi farazlari. Real tariflar bilan yangilang.')

st.markdown('''<div class="hero"><div class="eyebrow">ENERGY INTELLIGENCE / DECISION SUPPORT</div>
<h1>SolarClean AI <span style="color:#a9eee1">2.0</span></h1>
<p>Quyosh panellari uchun aqlli tozalash tahlili. Energiya, iqtisodiyot va resurslarni yagona qaror tizimiga birlashtiring.</p>
<span class="tag">◈ Energy analytics</span><span class="tag">◎ Cleaning intelligence</span><span class="tag">↗ Economic scenarios</span></div>''',unsafe_allow_html=True)

with st.expander('📁 Ma’lumotlarni boshqarish',expanded=False):
    st.caption('CSV faylingizni yuklang yoki namuna ma’lumotlari bilan platformani sinab ko‘ring.')
    upload=st.file_uploader('CSV faylni tanlang',type='csv')
    source=st.radio('Ma’lumot manbasi',['Namuna simulyatsiyasi','Haqiqiy o‘lchov'],horizontal=True,disabled=upload is None)
try:
    data_path=Path(__file__).resolve().parent/'sample_data.csv'
    df=pd.read_csv(upload) if upload is not None else pd.read_csv(data_path)
except Exception as exc:
    st.error(f'CSV o‘qishda xato: {exc}');st.stop()
origin='SIMULYATSIYA MA’LUMOTLARI — real o‘lchov emas' if upload is None or source=='Namuna simulyatsiyasi' else 'Foydalanuvchi haqiqiy deb belgilagan CSV (mustaqil tasdiqlanmagan)'
issues=validate_data(df)
if issues:
    for issue in issues: st.error(issue)
    st.stop()
df['timestamp']=pd.to_datetime(df['timestamp'],errors='coerce')
analysis=estimate_energy_gap(df,panel_kw=panel_kw)
gap=analysis['gap_kwh']
recovered=max(0,gap)*recovery/100 if gap is not None else 0
econ=cleaning_economics(recovered,tariff,cost)
label,why,confidence=decision(analysis,econ,origin,df)
quality=data_diagnostics(df)
scenarios=strategy_scenarios(df,[7,14,30],cost,liters,tariff,recovery)
forecast=scenario_forecast(df,horizon,recovery)
sens=sensitivity(gap,tariff,cost,recovery)
old_comparison=compare_strategies(df,tariff,cost,liters,14,recovery,analysis)
report=build_report(origin,analysis,econ,cost,liters,label,why,confidence,tariff,recovery,old_comparison)
report=pd.concat([report,pd.DataFrame([('Qaror tizimi','SolarClean AI 2.0'),('Ssenariy izohi','Kalendar va AI taqqoslanishi yagona farazlarga asoslangan, lekin empirik validatsiya qilinmagan.'),('O‘lchovlar soni',quality['rows']),('Kuzatuv davri (kun)',quality['days'])],columns=['Ko‘rsatkich','Qiymat'])],ignore_index=True)

st.markdown(f'<div class="data-note">● <b>Ma’lumot maqomi:</b> {"Simulyatsiya · namoyish" if origin.startswith("SIMULYATSIYA") else "Yuklangan CSV · mustaqil tekshirilmagan"} &nbsp; | &nbsp; {quality["rows"]} kuzatuv &nbsp; | &nbsp; {quality["days"]} kun. Natijalar real tozalash topshirig‘i emas.</div>',unsafe_allow_html=True)

pages=st.tabs(['▦ Umumiy panel','◉ Energiya tahlili','◇ Qaror markazi','▤ Strategiyalar','⌁ Ssenariy prognozi','▧ Hisobotlar'])
with pages[0]:
    section('01 / Operatsion ko‘rsatkichlar','Energiya ishlab chiqarishi va iqtisodiy natija — bir qarashda.')
    a,b,c,d=st.columns(4)
    a.metric('Amaldagi ishlab chiqarish',f"{analysis['actual_total']:.3f} kWh")
    b.metric('Kutilayotgan ishlab chiqarish',f"{analysis['expected_total']:.3f} kWh" if analysis['expected_total'] is not None else 'Noma’lum')
    c.metric('Energiya farqi',f'{gap:.3f} kWh' if gap is not None else 'Noma’lum')
    d.metric('Tozalash qiymati',f'{cost:,.0f} so‘m')
    x,y,z=st.columns(3)
    x.metric('Tiklanish farazi',f'{recovered:.3f} kWh')
    y.metric('Sof iqtisodiy natija',f"{econ['net_benefit']:,.0f} so‘m" if gap is not None else 'Aniqlanmagan')
    z.metric('Kuzatuvlar soni',quality['rows'])
    section('02 / Qaror xulosasi')
    if label=='CLEAN NOW': st.success(f'**{label}** · {why}')
    elif label=='WAIT & MONITOR': st.info(f'**{label}** · {why}')
    else: st.warning(f'**{label}** · {why}')
    st.caption(f'Ishonchlilik: {confidence} · Oxirgi tozalashdan beri: {max(0,(date.today()-last_clean).days)} kun')
    section('03 / Energiya dinamikasi')
    keys=[c for c in ['actual_kwh','expected_kwh'] if c in df]
    if keys:
        view=df[['timestamp']+keys].melt(id_vars='timestamp',var_name='Ko‘rsatkich',value_name='kWh')
        fig=px.area(view,x='timestamp',y='kWh',color='Ko‘rsatkich',color_discrete_sequence=PLOT_COLORS,title='Ishlab chiqarish: amaldagi va kutilayotgan')
        st.plotly_chart(chart_style(fig),use_container_width=True)
with pages[1]:
    section('04 / Energy analytics','Energiya ishlab chiqarishi va kuzatuv parametrlarining tahlili.')
    keys=[c for c in ['actual_kwh','expected_kwh'] if c in df]
    if keys:
        view=df[['timestamp']+keys].melt(id_vars='timestamp',var_name='Ko‘rsatkich',value_name='kWh')
        fig=px.line(view,x='timestamp',y='kWh',color='Ko‘rsatkich',markers=True,color_discrete_sequence=PLOT_COLORS,title='Elektr ishlab chiqarish dinamikasi')
        st.plotly_chart(chart_style(fig),use_container_width=True)
    for col in ('irradiance_wm2','panel_temp_c','soiling_ratio'):
        if col in df:
            fig=px.scatter(df,x=col,y='actual_kwh',color_discrete_sequence=PLOT_COLORS,title=f'{col} va elektr ishlab chiqarish')
            st.plotly_chart(chart_style(fig,310),use_container_width=True)
    section('Ma’lumotlar jadvali')
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.caption(f"Sifat nazorati: {quality['duplicates']} takrorlangan sana-vaqt; {quality['missing']} bo‘sh qiymat.")
with pages[2]:
    section('05 / Cleaning decision engine','Hisoblash shartlari va qaror chiqarishning iqtisodiy asosi.')
    st.warning(f'**{label}** — {why}') if label not in ('CLEAN NOW','WAIT & MONITOR') else st.info(f'**{label}** — {why}')
    a,b,c=st.columns(3)
    a.metric('Zararsizlik chegarasi',f'{cost/tariff:.3f} kWh' if tariff>0 else 'Tarif nol')
    b.metric('Tiklanish qiymati',f"{econ['recovered_value']:,.0f} so‘m")
    c.metric('Qaror ishonchliligi',confidence)
    section('06 / Sensitivity analysis','Tiklanish koeffitsiyenti va tarif o‘zgarganda sof natijaning sezgirligi.')
    fig=px.line(sens,x='Tarif koeffitsiyenti',y='Sof natija (so‘m)',color='Tiklanish (%)',markers=True,color_discrete_sequence=px.colors.sequential.Teal,title='Iqtisodiy natijaning sezgirligi')
    st.plotly_chart(chart_style(fig),use_container_width=True)
    st.caption('Tiklanish foizi taxminiy parametr. Bu tizim chang ta’sirini mustaqil isbotlamaydi.')
with pages[3]:
    section('07 / Cleaning strategy optimizer','Kalendar va adaptiv strategiyalar uchun yagona farazlarga asoslangan hisob.')
    if scenarios.empty: st.warning('Taqqoslash uchun expected_kwh va yetarli sanalar kerak.')
    else:
        st.dataframe(scenarios,use_container_width=True,hide_index=True)
        l,r=st.columns(2)
        with l:
            fig=px.bar(scenarios,x='Strategiya',y='Sof natija (so‘m)',color='Strategiya',color_discrete_sequence=PLOT_COLORS,title='Sof iqtisodiy natija')
            st.plotly_chart(chart_style(fig,350),use_container_width=True)
        with r:
            fig=px.bar(scenarios,x='Strategiya',y='Suv (litr)',color='Strategiya',color_discrete_sequence=PLOT_COLORS,title='Suv sarfi')
            st.plotly_chart(chart_style(fig,350),use_container_width=True)
    st.warning('Bu ilmiy validatsiya emas, soddalashtirilgan ssenariy hisobidir. Real tajribada natijalar farq qilishi mumkin.')
with pages[4]:
    section('08 / Scenario intelligence',f'{horizon} kunlik shartli ishlab chiqarish ssenariysi.')
    if forecast.empty: st.warning('Kamida uch kunlik to‘liq tarixiy ma’lumot kerak.')
    else:
        view=forecast.melt(id_vars='Sana',var_name='Ssenariy',value_name='kWh')
        fig=px.line(view,x='Sana',y='kWh',color='Ssenariy',color_discrete_sequence=PLOT_COLORS,title='O‘zgarmas kunlik o‘rtacha asosidagi ssenariy')
        st.plotly_chart(chart_style(fig),use_container_width=True)
        st.dataframe(forecast,use_container_width=True,hide_index=True)
    st.caption('Bu mashinaviy o‘rganish modeli yoki real ob-havo prognozi emas; oxirgi kuzatuvlarning o‘rtacha qiymatlari asosida tuzilgan.')
with pages[5]:
    section('09 / Reporting workspace','Tahlil va taxminlarni ilmiy hisobot sifatida eksport qilish.')
    st.dataframe(report,use_container_width=True,hide_index=True)
    c1,c2,c3,c4=st.columns(4)
    with c1: st.download_button('⬇ CSV hisobot',report.to_csv(index=False).encode('utf-8-sig'),'solarclean_report.csv','text/csv',use_container_width=True)
    with c2: st.download_button('⬇ Tahlil CSV',analysis['data'].to_csv(index=False).encode('utf-8-sig'),'solarclean_data.csv','text/csv',use_container_width=True)
    try:
        output=io.BytesIO()
        with pd.ExcelWriter(output,engine='openpyxl') as writer:
            report.to_excel(writer,sheet_name='Hisobot',index=False)
            df.to_excel(writer,sheet_name='Ma’lumotlar',index=False)
            scenarios.to_excel(writer,sheet_name='Strategiyalar',index=False)
            sens.to_excel(writer,sheet_name='Sezgirlik',index=False)
            forecast.to_excel(writer,sheet_name='Prognoz',index=False)
        with c3: st.download_button('⬇ Excel hisobot',output.getvalue(),'solarclean_report.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',use_container_width=True)
    except ImportError: st.warning('Excel eksporti uchun openpyxl o‘rnating.')
    try:
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
        from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from xml.sax.saxutils import escape
        fontfile=next((p for p in [Path('C:/Windows/Fonts/arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')] if p.exists()),None)
        font='Helvetica'
        if fontfile: pdfmetrics.registerFont(TTFont('SolarUnicode',str(fontfile)));font='SolarUnicode'
        styles=getSampleStyleSheet()
        styles.add(ParagraphStyle(name='SolarText',fontName=font,fontSize=8,leading=12,spaceAfter=5))
        buff=io.BytesIO();doc=SimpleDocTemplate(buff,pagesize=A4)
        story=[Paragraph('SolarClean AI 2.0 — Scientific Report',styles['Title']),Spacer(1,12)]
        for _,row in report.iterrows():
            key=str(row['Ko‘rsatkich']);value='Aniqlanmagan' if pd.isna(row['Qiymat']) else str(row['Qiymat'])
            story.append(Paragraph(f'<b>{escape(key)}</b>: {escape(value)}',styles['SolarText']))
        doc.build(story)
        with c4: st.download_button('⬇ PDF hisobot',buff.getvalue(),'solarclean_report.pdf','application/pdf',use_container_width=True)
    except ImportError: st.warning('PDF eksporti uchun reportlab o‘rnating.')
    st.caption('Hisobot prototip natijasidir. Real iqtisodiy samaradorlik tajriba orqali tasdiqlanishi kerak.')

st.markdown('<div class="footer">SOLARCLEAN AI © 2026 · Research prototype · Energy intelligence · Not a certified inverter control system</div>',unsafe_allow_html=True)
