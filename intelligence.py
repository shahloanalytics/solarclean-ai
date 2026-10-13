"""Scenario-only decision support; not causal attribution or validated AI."""
import numpy as np
import pandas as pd


def data_diagnostics(df):
    dates = pd.to_datetime(df.get('timestamp', pd.Series(dtype='object')), errors='coerce')
    return {'rows': len(df), 'start': dates.min(), 'end': dates.max(),
            'duplicates': int(dates.dropna().duplicated().sum()),
            'missing': int(df.isna().sum().sum()),
            'days': int((dates.max().normalize()-dates.min().normalize()).days + 1) if dates.notna().any() else 0}


def decision(analysis, economics, origin, df):
    gap = analysis.get('gap_kwh')
    if gap is None or not np.isfinite(gap):
        return 'INSUFFICIENT DATA', 'Kutilayotgan ishlab chiqarish mavjud emas.', 'Past'
    if origin.startswith('SIMULYATSIYA'):
        return 'INSUFFICIENT DATA', 'Namuna simulyatsiyasi: haqiqiy tozalash tavsiyasi berilmaydi.', 'Namoyish'
    if gap <= 0:
        return 'WAIT & MONITOR', 'Musbat ishlab chiqarish farqi aniqlanmadi.', 'Cheklangan'
    measured_soiling = 'soiling_ratio' in df and pd.to_numeric(df['soiling_ratio'], errors='coerce').notna().sum() >= 3
    if not measured_soiling:
        return 'INSPECT SYSTEM', 'Changlanishni tasdiqlovchi yetarli o‘lchov yo‘q; boshqa sabablarni tekshiring.', 'Past'
    if economics['net_benefit'] > 0:
        return 'CLEAN NOW', 'Kiritilgan farazlar asosida bir martalik tozalash iqtisodiy jihatdan ijobiy; nazorat o‘lchovi bilan tasdiqlang.', 'Shartli'
    return 'WAIT & MONITOR', 'Taxminiy tiklanish qiymati tozalash xarajatini qoplamaydi.', 'Shartli'


def sensitivity(gap_kwh, tariff, cost, recovery_pct):
    gap = max(0, float(gap_kwh or 0))
    rows=[]
    for tariff_factor in (0.5, 0.75, 1, 1.25, 1.5, 2):
        for recovery in (10, 20, 30, 50, 70, 100):
            rows.append({'Tarif koeffitsiyenti': tariff_factor, 'Tiklanish (%)': recovery,
                         'Sof natija (so‘m)': gap * recovery / 100 * tariff * tariff_factor - cost})
    return pd.DataFrame(rows)


def scenario_forecast(df, days, recovery_pct):
    """Explicit constant daily-rate scenario, not an ML forecast."""
    if 'expected_kwh' not in df or 'actual_kwh' not in df:
        return pd.DataFrame()
    d=df.copy()
    d['timestamp']=pd.to_datetime(d['timestamp'], errors='coerce')
    for c in ('expected_kwh','actual_kwh'):
        d[c]=pd.to_numeric(d[c], errors='coerce')
    d=d.dropna(subset=['timestamp','expected_kwh','actual_kwh'])
    if d.empty: return pd.DataFrame()
    daily=d.groupby(d['timestamp'].dt.normalize())[['expected_kwh','actual_kwh']].sum()
    if len(daily)<3: return pd.DataFrame()
    recent=daily.tail(min(7,len(daily)))
    base=float(recent['actual_kwh'].mean()); gap=max(0,float((recent['expected_kwh']-recent['actual_kwh']).mean()))
    start=d['timestamp'].max().normalize()
    return pd.DataFrame({'Sana':[start+pd.Timedelta(days=i) for i in range(1,days+1)],
                         'Bazaviy ishlab chiqarish (kWh)':[base]*days,
                         'Tozalanganda shartli (kWh)':[base+gap*recovery_pct/100]*days})


def strategy_scenarios(df, interval_options, cleaning_cost, water_liters, tariff, recovery_pct):
    """Common hypothetical daily loss and reset model. Not a measured comparison."""
    d=df.copy(); d['timestamp']=pd.to_datetime(d['timestamp'], errors='coerce')
    for col in ('actual_kwh','expected_kwh'):
        if col not in d: return pd.DataFrame()
        d[col]=pd.to_numeric(d[col], errors='coerce')
    d=d.dropna(subset=['timestamp','actual_kwh','expected_kwh'])
    if len(d)<3: return pd.DataFrame()
    daily=d.groupby(d['timestamp'].dt.normalize())[['actual_kwh','expected_kwh']].sum().sort_index()
    period=int((daily.index.max()-daily.index.min()).days+1)
    if period<2: return pd.DataFrame()
    avg_loss=max(0,float((daily['expected_kwh']-daily['actual_kwh']).mean()))
    # Scenario: after a cleaning, avoid a fraction of the assumed daily loss until next cleaning.
    # Fixed assumption is identical for all strategies and not a validated physical dust model.
    rows=[]
    for interval in interval_options:
        n=(period-1)//interval
        protected_days=sum(min(interval,period-k*interval) for k in range(1,n+1))
        recovered=protected_days*avg_loss*recovery_pct/100
        rows.append({'Strategiya':f'Kalendar {interval} kun', 'Tozalashlar':n,
                     'Tiklanish (kWh, ssenariy)':recovered, 'Xarajat (so‘m)':n*cleaning_cost,
                     'Suv (litr)':n*water_liters,'Sof natija (so‘m)':recovered*tariff-n*cleaning_cost})
    # One cleaning, on first date after initial interval, for a transparent simple comparator.
    ai_clean=int((period-1)*avg_loss*recovery_pct/100*tariff>cleaning_cost)
    recovered=(period-1)*avg_loss*recovery_pct/100 if ai_clean else 0
    rows.append({'Strategiya':'SolarClean AI — 1 qaror','Tozalashlar':ai_clean,
                 'Tiklanish (kWh, ssenariy)':recovered,'Xarajat (so‘m)':ai_clean*cleaning_cost,
                 'Suv (litr)':ai_clean*water_liters,'Sof natija (so‘m)':recovered*tariff-ai_clean*cleaning_cost})
    return pd.DataFrame(rows)
