"""SolarClean AI core calculations.

This MVP intentionally avoids claiming that unexplained production gaps are caused by dust.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["timestamp", "actual_kwh"]
OPTIONAL_COLUMNS = [
    "expected_kwh", "panel_temp_c", "ambient_temp_c", "irradiance_wm2",
    "soiling_ratio", "panel_voltage_v", "panel_current_a", "cleaned"
]

def validate_data(df: pd.DataFrame) -> list[str]:
    issues = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            issues.append(f"Majburiy ustun mavjud emas: {col}")
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
        if ts.isna().any():
            issues.append("timestamp ustunida bo‘sh yoki noto‘g‘ri sana-vaqt mavjud.")
        if ts.duplicated().any():
            issues.append("Takrorlangan sana-vaqt qiymatlari mavjud.")
    if "actual_kwh" in df.columns:
        vals = pd.to_numeric(df["actual_kwh"], errors="coerce")
        if vals.isna().any():
            issues.append("actual_kwh ustunida son bo‘lmagan yoki bo‘sh qiymatlar mavjud.")
        if (vals.dropna() < 0).any():
            issues.append("Manfiy elektr ishlab chiqarish qiymatlari mavjud.")
    if "expected_kwh" in df.columns:
        vals = pd.to_numeric(df["expected_kwh"], errors="coerce")
        if (vals.dropna() < 0).any():
            issues.append("expected_kwh ustunida manfiy qiymatlar mavjud.")
    if df.empty:
        issues.append("Fayl bo‘sh.")
    return issues

def estimate_energy_gap(df: pd.DataFrame, panel_kw: float = 0.33) -> dict:
    data = df.copy()
    if "timestamp" in data.columns:
        data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    if "actual_kwh" not in data.columns:
        return {"data": data, "actual_total": 0.0, "expected_total": None, "gap_kwh": None, "gap_pct": None}
    data["actual_kwh"] = pd.to_numeric(data["actual_kwh"], errors="coerce")
    actual_total = float(data["actual_kwh"].fillna(0).clip(lower=0).sum())
    expected_total = None
    gap_kwh = None
    gap_pct = None
    if "expected_kwh" in data.columns:
        data["expected_kwh"] = pd.to_numeric(data["expected_kwh"], errors="coerce")
        if data["expected_kwh"].notna().any():
            expected_total = float(data["expected_kwh"].fillna(0).clip(lower=0).sum())
            gap_kwh = expected_total - actual_total
            gap_pct = (gap_kwh / expected_total * 100) if expected_total > 0 else None
    data["panel_kw_input"] = panel_kw
    return {
        "data": data,
        "actual_total": actual_total,
        "expected_total": expected_total,
        "gap_kwh": gap_kwh,
        "gap_pct": gap_pct,
    }

def cleaning_economics(recovered_kwh: float, tariff: float, cleaning_cost: float) -> dict:
    recovered_kwh = max(0.0, float(recovered_kwh))
    tariff = max(0.0, float(tariff))
    cleaning_cost = max(0.0, float(cleaning_cost))
    recovered_value = recovered_kwh * tariff
    return {
        "recovered_kwh": recovered_kwh,
        "recovered_value": recovered_value,
        "cleaning_cost": cleaning_cost,
        "net_benefit": recovered_value - cleaning_cost,
    }

def make_recommendation(df: pd.DataFrame, net_benefit: float, analysis: dict,
                        recovery_pct: float, data_origin: str) -> tuple[str, str, str]:
    if "expected_kwh" not in df.columns or analysis["gap_kwh"] is None:
        return (
            "Qo‘shimcha tekshiruv",
            "Kutilayotgan ishlab chiqarish bilan taqqoslash uchun expected_kwh ustuni yo‘q. Chang ta’sirini ajratish uchun irradiatsiya yoki nazorat paneli ma’lumotini kiriting.",
            "Past"
        )
    has_irradiance = "irradiance_wm2" in df.columns and pd.to_numeric(df["irradiance_wm2"], errors="coerce").notna().sum() > 0
    has_soiling = "soiling_ratio" in df.columns and pd.to_numeric(df["soiling_ratio"], errors="coerce").notna().sum() > 0
    if data_origin.startswith("SIMULYATSIYA"):
        return (
            "Qo‘shimcha tekshiruv",
            "Namuna ma’lumotlari simulyatsiya qilingan. Bu natija amaliy tozalash qarorini asoslamaydi; haqiqiy o‘lchovlar bilan almashtiring.",
            "Faqat namoyish uchun"
        )
    if not (has_irradiance or has_soiling):
        return (
            "Qo‘shimcha tekshiruv",
            "Irradiatsiya yoki changlanish ko‘rsatkichi yo‘q. Ishlab chiqarish farqining sababi chang ekanini tasdiqlab bo‘lmaydi.",
            "Past"
        )
    if net_benefit > 0 and analysis["gap_kwh"] > 0:
        return (
            "Tozalash",
            "Kiritilgan taxminlar bo‘yicha tiklanishi kutilayotgan energiya qiymati tozalash xarajatidan yuqori. Qarorni kichik tajriba yoki nazorat paneli bilan tekshiring.",
            "O‘rta — validatsiya kerak"
        )
    return (
        "Kuzatishni davom ettirish",
        "Kiritilgan ma’lumotlar va taxminlar bo‘yicha tozalashning sof iqtisodiy foydasi ijobiy emas yoki energiya farqi aniqlanmagan.",
        "O‘rta — validatsiya kerak"
    )

def compare_strategies(df: pd.DataFrame, tariff: float, cleaning_cost: float,
                       water_liters: float, calendar_days: int, expected_recovery_pct: float,
                       analysis: dict) -> pd.DataFrame:
    data = analysis["data"]
    if data.empty:
        return pd.DataFrame()
    timestamps = pd.to_datetime(data.get("timestamp", pd.Series(dtype="object")), errors="coerce").dropna()
    if timestamps.empty:
        calendar_count = np.nan
        calendar_note = "Sana ma’lumoti yo‘q; kalendar sonini aniqlab bo‘lmaydi"
    else:
        period_days = (timestamps.max().normalize() - timestamps.min().normalize()).days + 1
        # First scheduled cleaning occurs after a full interval, not on day one.
        calendar_count = max(0, (period_days - 1) // max(1, int(calendar_days)))
        calendar_note = f"{period_days} kalendar kun uchun rejalashtirilgan tozalashlar; energiya tiklanishi baholanmagan"
    actual = analysis["actual_total"]
    gap = analysis["gap_kwh"]
    if gap is None:
        ai_count = np.nan
        ai_cost = np.nan
        ai_net = np.nan
        ai_energy = actual
        gap_note = "expected_kwh yo‘q; iqtisodiy qaror hisoblanmadi"
    else:
        potential_recovery = max(0.0, gap) * expected_recovery_pct / 100.0
        ai_count = int(potential_recovery * tariff > cleaning_cost and potential_recovery > 0)
        ai_cost = ai_count * cleaning_cost
        realized_recovery = ai_count * potential_recovery
        ai_net = realized_recovery * tariff - ai_cost
        ai_energy = actual + realized_recovery
        gap_note = "shartli bir martalik qaror; kelajakdagi ishlab chiqarish prognozi emas"
    rows = [
        {
            "Strategiya": f"Kalendar ({calendar_days} kun)",
            "Tozalashlar soni (taxmin)": calendar_count,
            "Jami tozalash xarajati (so‘m)": calendar_count * cleaning_cost,
            "Baholangan ishlab chiqarish (kWh)": actual,
            "Suv sarfi (litr)": calendar_count * water_liters,
            "Sof iqtisodiy natija (so‘m)": np.nan,
            "Izoh": calendar_note
        },
        {
            "Strategiya": "SolarClean AI (soddalashtirilgan)",
            "Tozalashlar soni (taxmin)": ai_count,
            "Jami tozalash xarajati (so‘m)": ai_cost,
            "Baholangan ishlab chiqarish (kWh)": ai_energy,
            "Suv sarfi (litr)": ai_count * water_liters if pd.notna(ai_count) else np.nan,
            "Sof iqtisodiy natija (so‘m)": ai_net,
            "Izoh": gap_note
        }
    ]
    return pd.DataFrame(rows)

def build_report(data_origin: str, analysis: dict, economics: dict, cleaning_cost: float,
                 water_liters: float, recommendation: str, explanation: str, confidence: str,
                 tariff: float, expected_recovery_pct: float, comparison: pd.DataFrame) -> pd.DataFrame:
    data = analysis.get("data", pd.DataFrame())
    dates = pd.to_datetime(data["timestamp"], errors="coerce") if "timestamp" in data else pd.Series(dtype="datetime64[ns]")
    valid_dates = dates.dropna()
    actual = analysis.get("actual_total")
    expected = analysis.get("expected_total")
    gap = analysis.get("gap_kwh")
    recovered = economics.get("recovered_kwh", 0.0)
    recovered_value = economics.get("recovered_value", recovered * tariff)
    break_even_kwh = cleaning_cost / tariff if tariff > 0 else None
    break_even_gap = break_even_kwh / (expected_recovery_pct / 100) if expected_recovery_pct > 0 else None
    missing = [c for c in REQUIRED_COLUMNS if c not in data.columns]
    missing_optional = [c for c in OPTIONAL_COLUMNS if c not in data.columns]
    null_counts = ", ".join(f"{c}: {int(data[c].isna().sum())}" for c in data.columns if data[c].isna().any()) or "Aniqlanmadi"
    rows = [
        ("BO‘LIM", "1. MA’LUMOTLAR SIFATI VA KELIB CHIQISHI"),
        ("Ma’lumot manbasi", data_origin),
        ("Kuzatuvlar soni", len(data)),
        ("Davr boshlanishi", str(valid_dates.min()) if not valid_dates.empty else "Aniqlanmagan"),
        ("Davr tugashi", str(valid_dates.max()) if not valid_dates.empty else "Aniqlanmagan"),
        ("Qamrab olingan kalendar kun", (valid_dates.max().normalize()-valid_dates.min().normalize()).days + 1 if not valid_dates.empty else None),
        ("Majburiy ustunlar yetishmaydi", ", ".join(missing) or "Yo‘q"),
        ("Ixtiyoriy ustunlar yetishmaydi", ", ".join(missing_optional) or "Yo‘q"),
        ("Bo‘sh qiymatlar", null_counts),
        ("Tekshiruv ogohlantirishlari", "; ".join(validate_data(data)) or "Aniqlanmadi"),
        ("BO‘LIM", "2. ENERGIYA DIAGNOSTIKASI"),
        ("Amaldagi ishlab chiqarish jami (kWh)", actual),
        ("Kutilayotgan ishlab chiqarish jami (kWh)", expected),
        ("Kutilayotgan-amaldagi farq (kWh)", gap),
        ("Farq (%)", analysis.get("gap_pct")),
        ("Talqin", "Ishlab chiqarish farqi chang ta’sirining isboti emas; ob-havo, soya, harorat va texnik nosozliklar ham ta’sir qiladi."),
        ("BO‘LIM", "3. IQTISODIY BAHOLASH"),
        ("Elektr qiymati (so‘m/kWh)", tariff),
        ("Tozalash xarajati (so‘m)", cleaning_cost),
        ("Suv sarfi/tozalash (litr)", water_liters),
        ("Tiklanish taxmini (%)", expected_recovery_pct),
        ("Tiklanishi taxmin qilingan energiya (kWh)", recovered),
        ("Tiklanish qiymati (so‘m)", recovered_value),
        ("Sof foyda taxmini (so‘m)", economics.get("net_benefit")),
        ("Zararsizlik nuqtasi — energiya (kWh)", break_even_kwh),
        ("Zararsizlik nuqtasi — ishlab chiqarish farqi (kWh)", break_even_gap),
        ("BO‘LIM", "4. QAROR VA ISHONCHLILIK"),
        ("Tavsiya", recommendation),
        ("Tavsiya izohi", explanation),
        ("Ishonchlilik belgisi", confidence),
        ("BO‘LIM", "5. STRATEGIYALAR TAQQOSLANISHI"),
    ]
    if comparison is not None and not comparison.empty:
        for _, item in comparison.iterrows():
            strategy = str(item.get("Strategiya", "Strategiya"))
            for column in comparison.columns:
                if column != "Strategiya":
                    rows.append((f"{strategy} — {column}", item[column]))
    rows += [
        ("BO‘LIM", "6. METODOLOGIYA VA CHEKLOVLAR"),
        ("Hisoblash usuli", "Farq = kutilayotgan − amaldagi; tiklanish = musbat farq × tiklanish foizi; sof foyda = tiklanish × tarif − tozalash xarajati."),
        ("Strategiya cheklovi", "Kalendar strategiyasida tozalashdan keyingi energiya o‘sishi baholanmagan; strategiyalar sof iqtisodiy natijasini teng asosda qiyoslash mumkin emas."),
        ("Ma’lumot cheklovi", "Simulyatsiya ma’lumotlari real o‘lchov emas. Ushbu prototip chang sababli yo‘qotishni yoki AI ustunligini isbotlamaydi."),
        ("Keyingi validatsiya", "Bir xil sharoitdagi nazorat va tozalangan PV panellarida oldin/keyin ishlab chiqarish, irradiatsiya va haroratni o‘lchash."),
    ]
    return pd.DataFrame(rows, columns=["Ko‘rsatkich", "Qiymat"])
