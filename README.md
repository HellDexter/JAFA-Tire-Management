# JAFA Tire Management

Aplikace pro kompletní správu pneumatik pro nákladní autodopravu s tahači a návěsy.

## Popis

JAFA Tire Management je webová aplikace vytvořená ve Flasku, která pomáhá s:

- **Skladovou evidencí pneumatik** - značky, typy, rozměry, dodavatelé
- **Přiřazováním pneumatik k vozidlům** - montáž, demontáž, sledování pozic na soupravě
- **Sledováním životnosti pneumatik** - datum montáže, aktuální nájezd, důvody demontáže
- **Správou vozového parku** - tahače, návěsy, soupravy
- **Generováním reportů** - průměrná životnost, důvody vyřazení, minimální skladové zásoby
- **Dokumentováním servisních zásahů** - fotografie, komentáře, historie

## Funkce

- Evidence tahačů, návěsů a jejich kombinací do souprav
- Evidence pneumatik na skladě i na vozidlech
- Přehledné zobrazení pozic pneumatik na jednotlivých vozidlech
- Sledování historie použití pneumatik
- Monitorování aktuálního stavu pneumatik včetně hloubky dezénu
- Správa dodavatelů a typů pneumatik
- Vytváření žádostí o nákup
- Generování reportů o životnosti a využití pneumatik

## Instalace

1. Naklonujte tento repozitář
2. Vytvořte virtuální prostředí Pythonu:
   ```
   python -m venv venv
   ```
3. Aktivujte virtuální prostředí:
   - Windows: `venv\Scripts\activate`
   - Linux/MacOS: `source venv/bin/activate`
4. Nainstalujte závislosti:
   ```
   pip install -r requirements.txt
   ```
5. Spusťte aplikaci:
   ```
   python app.py
   ```
6. Otevřete webový prohlížeč a přejděte na adresu `http://localhost:5000`
7. Inicializujte databázi kliknutím na tlačítko "Inicializovat databázi" na úvodní stránce

## Výchozí přihlašovací údaje

- **Uživatelské jméno:** admin
- **Heslo:** admin123

## Technologie

- **Backend:** Python, Flask, SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
- **Databáze:** SQLite (pro produkční nasazení doporučujeme přejít na PostgreSQL)

## Struktura projektu

- `/app.py` - Hlavní soubor aplikace
- `/models.py` - Databázové modely
- `/routes.py` - API endpointy a směrování
- `/templates/` - HTML šablony
- `/static/` - CSS, JavaScript, obrázky a uploady
- `/static/uploads/` - Nahrané fotografie pneumatik

## Licence

Všechna práva vyhrazena. Aplikace JAFA Tire Management je proprietární software vytvořený na zakázku.
