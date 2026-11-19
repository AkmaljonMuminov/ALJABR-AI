# ALJABR AI

**Intelligence. Control. Independence.** (Aql. Nazorat. Mustaqillik.)

*English version: [README.en.md](README.en.md)*

ALJABR AI — modulli, ovoz bilan boshqariladigan shaxsiy sun'iy intellekt
yordamchisi. U avval bitta foydalanuvchi uchun Android smartfonda ishlaydi
(asosiy til — o'zbek, qo'shimcha tillar — rus va ingliz) va keyinchalik ommaviy
AI platformasiga aylanishi mumkin bo'lgan tarzda loyihalangan.

## Holat

| Bosqich | Modul | Holati |
|---------|-------|--------|
| 1 | ALJABR CORE (sozlamalar, log, ishga tushirish) | **Tayyor va testlangan** |
| 2 | ALJABR BRAIN (AI provayder, suhbat) | **Tayyor va testlangan** (haqiqiy OpenAI xizmatida hali sinalmagan) |
| 3 | ALJABR VOICE (push-to-talk, ovoz kirish/chiqish) | **Tayyor va testlangan** (telefonda hali sinalmagan) |
| 4 | ALJABR MEMORY (SQLite, ruxsat bilan eslab qolish) | **Tayyor va testlangan** (telefonda hali sinalmagan) |
| 5 | ALJABR COMMANDS (ruxsat nazoratidagi buyruqlar) | Rejada |
| 6 | ALJABR SECURITY (ruxsat etilgan himoya monitoringi) | Rejada |
| 7 | Android interfeysi | Rejada |
| 8 | Ommaviy ko'p foydalanuvchili platforma (dastlab o'chiq) | Rejada |

1–4-bosqichlar Linux va Python 3.13 da testlangan. Ular **Android qurilmada hali
tekshirilmagan**; qarang: `docs/ANDROID_SETUP.md`. AI so'rovlari faqat soxta va
mahalliy test serverlarida sinalgan; o'z kalitingiz va modelingiz bilan birinchi
haqiqiy so'rov hali tasdiqlanmagan. Ovoz soxta nutq dvigatellari va soxta
`termux-*` dasturlar bilan sinalgan; haqiqiy mikrofon, dinamik va o'zbekcha nutq
sifati telefoningizda tekshirilishi kerak.

## Tez boshlash (Android'da Termux yoki istalgan Python 3.9+)

```bash
git clone https://github.com/AkmaljonMuminov/ALJABR-AI.git
cd ALJABR-AI
cp .env.example .env          # keyin .env da OPENAI_API_KEY va ALJABR_AI_MODEL ni kiriting
python main.py --check        # tizim tekshiruvi
python main.py --chat         # AI bilan suhbat (chiqish: /exit)
python main.py --ask "Salom!" # bitta savol berish
python main.py --voice        # ovozli suhbat (Termux:API bo'lmasa matn rejimi)
python -m unittest discover -s tests -t .   # testlarni ishga tushirish
```

Uchinchi tomon paketlari kerak emas.

## Xotira (4-bosqich)

Chat ichida (`python main.py --chat`):

```
/remember Mening sevimli rangim ko'k   # eslab qolish (faqat siz buyurganda)
/memories                              # ro'yxat; /memories so'z — qidirish
/edit 1 Yangi matn                     # o'zgartirish
/forget 1                              # o'chirish; /forget all — hammasi (tasdiq bilan)
```

Saqlangan eslatmalar qayta ishga tushirgandan keyin ham qoladi va AI javob berayotganda
foydalaniladi. Parol, kalit, token va karta raqami saqlanmaydi. Batafsil: `docs/PHASE4_MEMORY.md`.

## Loyiha tuzilmasi

```
main.py            kirish nuqtasi (--check, --chat, --ask, --voice, --version, --env-file)
config/            .env o'qish va tekshirilgan sozlamalar
core/              ilova hayot sikli, xavfsiz log, xabarlar (uz/ru/en), xatolar
brain/             AI provayder interfeysi, OpenAI adapteri, suhbat, chat sikli
voice/             nutq kirish/chiqish, uyg'otish iborasi, push-to-talk sessiyasi
memory/            uzoq muddatli xotira: eslatmalar, qidiruv, parol filtri
database/          SQLite ulanishi va migratsiyalar
commands/ security/ api/   (keyingi bosqichlar)
tests/             unit testlar
docs/              arxitektura, bosqich rejalari, Android o'rnatish
```

## Xavfsizlik va maxfiylik qoidalari

* Maxfiy ma'lumotlar faqat sizning mahalliy `.env` faylingizda turadi
  (`.gitignore` ga kiritilgan). Uni hech qachon commit qilmang.
* Loglarda API kalitlari, bearer tokenlar va `password=...` qiymatlari
  yashiriladi. Xabarlar mazmuni logga yozilmaydi.
* API kaliti faqat sozlangan HTTPS manzilga yuboriladi va yo'naltirishlarda
  (redirect) hech qachon boshqa manzilga uzatilmaydi (redirectlar rad etiladi).
* **Xabarlaringiz siz sozlagan AI provayderga yuboriladi** (standart bo'yicha
  OpenAI) va uning maxfiylik siyosatiga bo'ysunadi. Chatga parol yoki kalit
  yozmang.
* Mikrofon faqat Enter bosgandan keyin ishlatiladi (push-to-talk); fonda
  tinglash yo'q. Aytgan gapingiz logga yozilmaydi.
* Suhbat tarixi faqat xotirada turadi va dastur tugagach yo'qoladi. Doimiy
  eslatmalar faqat siz `/remember` deb buyurganda saqlanadi; AI eslatma yarata,
  o'zgartira yoki o'chira olmaydi.
* Parol, API kalit, token va karta raqami eslatmaga saqlanmaydi (filtr taxminiy,
  kafolat emas — bunday ma'lumotlarni umuman yozmang).
* Tegishli eslatmalar savolingiz bilan birga **AI provayderga yuboriladi**.
  Xohlamasangiz `.env` da `ALJABR_MEMORY_IN_PROMPT=false` qiling.
* Eslatmalar `data/aljabr.db` faylida (faqat egasi o'qiy oladi) turadi, lekin
  shifrlanmagan. Har bir yozuv `user_id` ga bog'langan (kelgusi ko'p foydalanuvchili
  rejim uchun).
* Nozik amallar (xabar yuborish, fayl o'chirish, xarid, xavfli buyruqlar) aniq
  foydalanuvchi tasdig'ini talab qiladi (5-bosqich).
* Xavfsizlik skanerlash faqat siz aniq ruxsat bergan tizimlar bilan cheklanadi
  (6-bosqich).

## Hujjatlar

* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — arxitektura
* [`docs/PHASE1_PLAN.md`](docs/PHASE1_PLAN.md) — 1-bosqich rejasi
* [`docs/PHASE2_BRAIN.md`](docs/PHASE2_BRAIN.md) — AI miya
* [`docs/PHASE3_VOICE.md`](docs/PHASE3_VOICE.md) — ovoz tizimi
* [`docs/PHASE4_MEMORY.md`](docs/PHASE4_MEMORY.md) — xotira tizimi
* [`docs/ANDROID_SETUP.md`](docs/ANDROID_SETUP.md) — Android'da o'rnatish

*Eslatma: `docs/` ichidagi hujjatlar hozircha inglizcha.*
