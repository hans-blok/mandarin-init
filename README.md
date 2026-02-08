# mandarin-init

Dit is de plek waar de generieke bestanden worden onderhouden. 
Deze worden gebruikt bij het opnieuw opzetten van een workspace met GitHub repository.

## Gebruik

Een nieuwe workspace opzetten met deze generieke bestanden:

1. Start `init-workspace.bat` in de root van de repository.
	- Dit zet de basisstructuur en configuratie van de workspace klaar.
2. Start daarna `fetch-agents.bat`.
	- Dit haalt de benodigde agents en gerelateerde bestanden op.

Na deze stappen is de workspace klaar om in VS Code verder te gebruiken.

## install
in shell: pip install -r requirements.txt

## mkdocs renderen
<!--> kies een poort bijvoorbeeld 8005 -->
mkdocs serve -a 127.0.0.1:8005

http://127.0.0.1:8005/

Get-Process | Where-Object { $_.Name -like "*python*" -or $_.ProcessName -like "*mkdocs*" } | Select-Object Id, ProcessName, Path

Voorbeeld om te stoppen
Stop-Process -Id 13428, 31804, 37612 -Force