# SolarClean AI 2.0 — Professional UI

Quyosh PV tizimlarida tozalash zaruratini energetik va iqtisodiy ko'rsatkichlar bo'yicha baholovchi ilmiy prototip.

**Muhim:** Namuna ma'lumotlari simulyatsiyadir. Dastur sertifikatlangan invertor boshqaruv qurilmasi emas va real stansiyada validatsiyadan o'tgan deb ko'rsatilmaydi.

## Mahalliy ishga tushirish

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Community Cloud

1. GitHub'da yangi `solarclean-ai` repository yarating.
2. Ushbu papkadagi fayllarni **repository ildiziga** yuklang (`app.py` GitHub bosh sahifasida ko'rinsin).
3. https://share.streamlit.io ga o'ting; GitHub bilan kiring.
4. **Create app** > **Yup, I have an app** ni tanlang.
5. Repository: `<username>/solarclean-ai`, branch: `main`, main file path: `app.py`.
6. `Deploy` tugmasini bosing. Natija `https://...streamlit.app` manzilida ochiladi.

Agar tarqatish ishlamasa, Cloud'dagi **Manage app > Logs** oynasini tekshiring.

## Xavfsizlik

- Haqiqiy stansiya ma'lumotlari yoki API tokenlarini ommaviy GitHub'ga yuklamang.
- Integratsiya qilsangiz, API kalitlarini Streamlit Cloud Secrets bo'limiga kiriting.
- Ilk ulanishda invertordan faqat o'qish rejimida foydalaning.

## Test

```bash
python -m pip install pytest
python -m pytest -q
```
