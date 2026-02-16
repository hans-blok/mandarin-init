# Agent Charter - <agent-naam>


<!--
Doel van dit template:
- Laat Agent Smeder dit charter consistent invullen.
- Sluit aan op de dual-file architectuur: per intent een `.agent.md` (contract) + een `mandarin.<agent>.<intent>.prompt.md` (YAML-only).

Vul alle placeholders in met concrete waarden.
Gebruik een value stream slug (lowercase, hyphens) die overeenkomt met `exports/<value-stream>/...`.
-->
**Agent**: <agent-naam>  
**Domein**: <domein>  
**Value Stream**: <value-stream>

**Governance**: Deze agent volgt het beleid vastgelegd in `beleid-mandarin-agents.md` en de relevante doctrine(s) voor agent-charters.

## Classificatie van de agent
(vink aan wat van toepassing is)

<!--
Richtlijn: agents in value stream `agent-enablement` zijn in principe
"Ecosysteem-normerend" op de inhoudelijke as.
-->

- **Inhoudelijke as**
  - [ ] Ecosysteem-normerend
  - [ ] Structuur-normerend
  - [ ] Structuurrealiserend
  - [ ] Beschrijvend
  - [ ] Curator

- **Inzet-as**
  - [ ] Value-stream-specifiek
  - [ ] Value-stream-overstijgend

- **Vorm-as**
  - [ ] Vormvast
  - [ ] Representatieomvormend

- **Werkingsas**
  - [ ] Inhoudelijk
  - [ ] Conditioneel


## 1. Doel en bestaansreden

<Leg in 2-5 zinnen uit waarom deze agent bestaat en welk probleem hij oplost.>

## 2. Capability boundary

<Een scherpe zin: wat de agent WEL doet.>

## 3. Rol en verantwoordelijkheid

<Beschrijf in B1-taal wat de agent doet, welke kwaliteit hij bewaakt en waar hij voor staat.>

De <agent-naam> bewaakt daarbij:
- <kwaliteit/risico 1>
- <kwaliteit/risico 2>
- <kwaliteit/risico 3>

## 4. Kerntaken

<Max 5-8 kerntaken. Houd kerntaken concreet en toetsbaar.>

1. **<kerntaak 1>**
   - <wat levert dit op>
   - <welke check/kwaliteit>

2. **<kerntaak 2>**
   - <wat levert dit op>
   - <welke check/kwaliteit>

## 5. Grenzen

### Wat de <agent-naam> WEL doet
- <concrete actie 1>
- <concrete actie 2>
- <concrete actie 3>

### Wat de <agent-naam> NIET doet
- <out-of-scope 1>
- <out-of-scope 2>
- <out-of-scope 3>

## 6. Werkwijze

<Beschrijf het standaardproces in 5-10 stappen. Dit is interne werkwijze ("hoe"), geen interface-contract.>

1. <stap 1>
2. <stap 2>
3. <stap 3>

## 7. Traceerbaarheid (contract <-> charter)

Dit charter is traceerbaar naar de bijbehorende agent-contracten per intent:

- Intent: `<intent-1>`
  - Agent contract: `artefacten/<value-stream>/<volgnummer value stream fase>.<agent-naam>/<agent-naam>.<intent-1>.agent.md`
  - Prompt metadata: `artefacten/<value-stream>/<volgnummer value stream fase>.<agent-naam>/mandarin.<agent-naam>.<intent-1>.prompt.md`
- Intent: `<intent-2>`
  - Agent contract: `artefacten/<value-stream>/<volgnummer value stream fase>.<agent-naam>/<agent-naam>.<intent-2>.agent.md`
  - Prompt metadata: `artefacten/<value-stream>/<volgnummer value stream fase>.<agent-naam>/mandarin.<agent-naam>.<intent-2>.prompt.md`  

## 8. Output-locaties

De <agent-naam> schrijft resultaten (waar van toepassing) naar:

- `artefacten/<agent-naam>/...`

<Noem hier 2–4 concrete bestandsnamen of patronen die bij het domein van de agent passen.>

## 9. Templates

Deze agent gebruikt de volgende templates voor het structureren van output per intent:

- **Intent `<intent-1>`**: [`templates/<product-1>.template.md`](../templates/<product-1>.template.md)  
  _Template voor <korte beschrijving deliverable van intent 1>_

- **Intent `<intent-2>`**: [`templates/<product-2>.template.md`](../templates/<product-2>.template.md)  
  _Template voor <korte beschrijving deliverable van intent 2>_

<Als een intent geen specifieke template heeft, gebruik: "Geen specifieke template (vrije markdown-structuur)">

## 10. Herkomstverantwoording

<Beschrijf welke bronnen/artefacten als basis dienen en waar output traceerbaar wordt opgeslagen.>

- Governance: `beleid-mandarin-agents.md` + mandarin-canon repository
- Agent-contracten: zie Traceerbaarheid

## 10. Change Log

| Datum | Versie | Wijziging | Auteur |
|------|--------|-----------|--------|
| 2026-01-24 | 0.1.0 | Initiële charter <agent-naam> | Agent Smeder |