# Beleid voor de [WORKSPACE_NAAM] workspace

Deze workspace hoort bij de waardestroom **[VALUE_STREAM_NAAM]**.

## Verplichte leesvolgorde van grondslagen

Elke geautomatiseerde rol, agent of runner hanteert bij aanvang van zijn functioneren de volgende verplichte leesvolgorde:

**In de centrale canon repository** (`https://github.com/hans-blok/mandarin-canon.git`):
1. `grondslagen/0.algemeen/constitutie.md`
2. overige algemene grondslagen binnen `grondslagen/0.algemeen/`
3. grondslagen van de expliciet toegewezen value stream

**In deze workspace**:
4. workspace-specifiek beleid (dit bestand)

Het overslaan, herordenen of impliciet toepassen van deze leesvolgorde is niet toegestaan.

**Zonder aantoonbare toepassing van de constitutie is handelen ongeldig.**

## Dit beleid is workspace-specifiek

Dit beleid beschrijft alleen de workspace-specifieke scope. Voor alle regels, uitzonderingen, details en constitutionele bepalingen volgen we volledig de richtlijnen in `hans-blok/mandarin-canon`.

De constitutie, algemene regels en governance voor alle workspaces staan in:
- https://github.com/hans-blok/mandarin-canon.git

## Canon Repository Synchronisatie

In alle geautomatiseerde en handmatige processen wordt de centrale canon repository geraadpleegd. Dit gebeurt altijd eerst met een `git pull` om te waarborgen dat de meest recente grondslagen worden gebruikt.

**Foutmelding**: Wanneer de mandarin-canon-repository niet bereikbaar is of niet kan worden gevonden, wordt een foutmelding gegeven en stopt het proces.

## Scope

### Wat we in deze workspace vastleggen

- [Beschrijf hier de scope van deze workspace: wat hoort erbij en wat wordt ondersteund]
- [Geef concrete voorbeelden van wat binnen de scope valt]

### Wat niet in deze workspace hoort

Andere domeinen vallen buiten deze workspace en horen in andere repositories. Voorbeelden hiervan zijn:
- [Domein 1 dat niet binnen scope valt]
- [Domein 2 dat niet binnen scope valt]
- [Domein 3 dat niet binnen scope valt]

## Workspace-specifieke aanvullingen

- [Aanvulling 1: bijv. taalgebruik, documentatiestijl]
- [Aanvulling 2: bijv. specifieke werkwijze of proces]
- [Aanvulling 3: bijv. logging of traceerbaarheid]

---

*Laatste update: [DATUM] door [NAAM]*
