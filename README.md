# LLM API Tool Calling Demo

Jednoduchý Python skript zavola LLM API, model muze pouzit lokalni vypocetni nastroj a vysledek nastroje se posle zpet modelu pro finalni odpoved.

## Co projekt ukazuje

- volani OpenAI LLM API z Pythonu,
- definici nastroje `calculate_expression`,
- lokalni a bezpecny vypocet matematickeho vyrazu,
- vraceni vysledku nastroje zpet do modelu,
- finalni odpoved od LLM.

Skutecny API klic v repozitari neni. Patri pouze do lokalniho souboru `.env`, ktery je v `.gitignore`.

## Struktura

```text
llm-api-tool-demo/
|-- app.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
`-- README.md
```

## Instalace

Vytvor virtualni prostredi:

```powershell
py -m venv .venv
```

Aktivuj ho:

```powershell
.venv\Scripts\Activate.ps1
```

Nainstaluj zavislosti:

```powershell
pip install -r requirements.txt
```

Projekt potrebuje jen balicek `openai`. Soubor `.env` nacita primo skript, takze neni potreba dalsi knihovna.

## Nastaveni API klice

Zkopiruj `.env.example` do lokalniho souboru `.env`:

```powershell
Copy-Item .env.example .env
```

Do `.env` vloz svuj skutecny klic:

```env
OPENAI_API_KEY=tvuj_skutecny_klic
OPENAI_MODEL=gpt-4.1-mini
```

Soubor `.env` se neposila na GitHub, protoze je uvedeny v `.gitignore`.

## Spusteni

Interaktivne:

```powershell
py app.py
```

Nebo rovnou s dotazem:

```powershell
py app.py "Kolik je (25 + 17) * 3?"
```

Pro zobrazeni tool callu:

```powershell
py app.py --show-tool-calls "Kolik je sqrt(144) + 8 * 5?"
```

## Jak to funguje

1. Uzivatel zada dotaz.
2. Skript posle dotaz do OpenAI API a nabidne modelu nastroj `calculate_expression`.
3. Pokud model potrebuje pocitat, vrati function call.
4. Python lokalne spusti bezpecny kalkulator.
5. Skript posle vysledek nastroje zpet modelu.
6. Model vytvori finalni odpoved pro uzivatele.

Kalkulator podporuje operatory `+`, `-`, `*`, `/`, `**`, `%`, zavorky a funkce `sqrt`, `abs`, `round`, `ceil`, `floor`.

## Odevzdani

Do ukolu se odevzdava odkaz na GitHub repozitar. Pred publikovanim zkontroluj, ze v repozitari neni soubor `.env` ani zadny skutecny API klic.
