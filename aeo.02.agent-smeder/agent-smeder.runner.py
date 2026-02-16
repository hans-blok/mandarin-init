"""
Agent Runner: agent-smeder

Verantwoordelijk voor het smeden van nieuwe agents: legt agent-contracten vast,
schrijft charters en genereert runners.

Input: input/input.md met YAML frontmatter
Output: Agent-artefacten in artefacten/{value-stream}.{fase}.{agent-naam}/

Intents:
- leg-agent-contract-vast: Genereert agent-contracten en prompt-metadata
- schrijf-charter: Creëert volledige agent-charter
- schrijf-runner: Genereert Python runner-script

Datum: 2026-02-06
Versie: 1.0
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional
import yaml
import re

def log_agent_action(agent_naam: str, gelezen: Optional[List[str]] = None, 
                     aangepast: Optional[List[str]] = None, 
                     aangemaakt: Optional[List[str]] = None) -> None:
    """
    Roept mandarin_agent_runner.py aan voor logging conform Norm 10.4.
    
    Args:
        agent_naam: Canonieke naam van de agent
        gelezen: Lijst van gelezen bestandspaden
        aangepast: Lijst van aangepaste bestandspaden
        aangemaakt: Lijst van aangemaakte bestandspaden
    """
    cmd = [
        "python", "scripts/mandarin_agent_runner.py", agent_naam,
        "--gelezen", *(gelezen or []),
        "--aangepast", *(aangepast or []),
        "--aangemaakt", *(aangemaakt or [])
    ]
    subprocess.run(cmd, check=True)


def parse_input() -> dict:
    """
    Leest input/input.md en parseert YAML frontmatter.
    
    Returns:
        Dictionary met intent, agent_naam en andere parameters
    
    Raises:
        FileNotFoundError: Als input/input.md niet bestaat
        ValueError: Als YAML frontmatter invalide is
    """
    input_file = Path("input/input.md")
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input bestand niet gevonden: {input_file}")
    
    content = input_file.read_text(encoding="utf-8")
    
    # Parse YAML frontmatter
    yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not yaml_match:
        raise ValueError("Geen geldige YAML frontmatter gevonden in input.md")
    
    frontmatter = yaml.safe_load(yaml_match.group(1))
    
    required_fields = ["intent", "agent_naam"]
    for field in required_fields:
        if field not in frontmatter:
            raise ValueError(f"Verplicht veld '{field}' ontbreekt in YAML frontmatter")
    
    return frontmatter


def handle_leg_agent_contract_vast(params: dict) -> None:
    """
    Intent: leg-agent-contract-vast
    
    Genereert agent-contracten en prompt-metadata voor alle intents van een agent.
    
    Args:
        params: Dictionary met agent_naam, value_stream, fase, intents
    """
    agent_naam = params["agent_naam"]
    value_stream = params.get("value_stream", "")
    fase = params.get("fase", "")
    intents = params.get("intents", [])
    
    gelezen_bestanden = ["input/input.md"]
    aangemaakte_bestanden = []
    
    # Lees agent-boundary voor context
    boundary_file = Path(f"agent-boundaries/{agent_naam}.boundary.md")
    if boundary_file.exists():
        gelezen_bestanden.append(str(boundary_file))
    
    # Bepaal agent folder
    agent_folder = Path(f"artefacten/{value_stream}.{fase}.{agent_naam}")
    agent_folder.mkdir(parents=True, exist_ok=True)
    
    # Genereer contract en prompt-metadata per intent
    for intent in intents:
        intent_naam = intent["naam"]
        
        # Agent-contract
        contract_path = agent_folder / f"{agent_naam}.{intent_naam}.agent.md"
        contract_content = f"""# Agent Contract - {agent_naam}.{intent_naam}

**Agent**: {agent_naam}
**Intent**: {intent_naam}
**Omschrijving**: {intent.get('omschrijving', '')}

## Input
{intent.get('input', 'Te specificeren')}

## Output
{intent.get('output', 'Te specificeren')}

## Foutafhandeling
{intent.get('foutafhandeling', 'Te specificeren')}

## Herkomstverantwoording
- Gegenereerd door: agent-smeder
- Datum: 2026-02-06
- Versie: 1.0
"""
        contract_path.write_text(contract_content, encoding="utf-8")
        aangemaakte_bestanden.append(str(contract_path))
        
        # Prompt-metadata
        prompt_path = agent_folder / f"mandarin.{agent_naam}.{intent_naam}.prompt.md"
        prompt_content = f"""---
agent: {agent_naam}
intent: {intent_naam}
charter: artefacten/{value_stream}.{fase}.{agent_naam}/{agent_naam}.charter.md
contract: artefacten/{value_stream}.{fase}.{agent_naam}/{agent_naam}.{intent_naam}.agent.md
---

# Prompt Metadata - {agent_naam}.{intent_naam}

Dit bestand bevat alleen YAML frontmatter voor agent-runner integratie.
"""
        prompt_path.write_text(prompt_content, encoding="utf-8")
        aangemaakte_bestanden.append(str(prompt_path))
    
    print(f"✓ Agent-contracten aangemaakt voor {agent_naam} ({len(intents)} intents)")
    
    # Log actie
    log_agent_action("agent-smeder", gelezen=gelezen_bestanden, aangemaakt=aangemaakte_bestanden)


def handle_schrijf_charter(params: dict) -> None:
    """
    Intent: schrijf-charter
    
    Creëert volledige agent-charter op basis van boundary en contracten.
    
    Args:
        params: Dictionary met agent_naam, value_stream, fase
    """
    agent_naam = params["agent_naam"]
    value_stream = params.get("value_stream", "")
    fase = params.get("fase", "")
    
    gelezen_bestanden = ["input/input.md"]
    aangemaakte_bestanden = []
    
    # Lees agent-boundary
    boundary_file = Path(f"agent-boundaries/{agent_naam}.boundary.md")
    if boundary_file.exists():
        gelezen_bestanden.append(str(boundary_file))
        boundary_content = boundary_file.read_text(encoding="utf-8")
    else:
        print(f"⚠ Waarschuwing: Agent-boundary niet gevonden voor {agent_naam}")
        boundary_content = ""
    
    # Lees agent-contracten
    agent_folder = Path(f"artefacten/{value_stream}.{fase}.{agent_naam}")
    contract_files = list(agent_folder.glob(f"{agent_naam}.*.agent.md"))
    gelezen_bestanden.extend([str(f) for f in contract_files])
    
    # Lees charter template
    template_file = Path("templates/agent-charter.template.md")
    if template_file.exists():
        gelezen_bestanden.append(str(template_file))
        charter_template = template_file.read_text(encoding="utf-8")
    else:
        charter_template = "# Agent Charter - {agent_naam}\n\nTe vullen op basis van template."
    
    # Genereer charter (simplified - in productie zou dit boundary/contracts parsen)
    charter_path = agent_folder / f"{agent_naam}.charter.md"
    charter_content = charter_template.replace("{agent_naam}", agent_naam)
    charter_content = charter_content.replace("{value_stream}", value_stream)
    charter_content = charter_content.replace("{fase}", fase)
    
    charter_path.write_text(charter_content, encoding="utf-8")
    aangemaakte_bestanden.append(str(charter_path))
    
    print(f"✓ Charter aangemaakt voor {agent_naam}")
    
    # Log actie
    log_agent_action("agent-smeder", gelezen=gelezen_bestanden, aangemaakt=aangemaakte_bestanden)


def handle_schrijf_runner(params: dict) -> None:
    """
    Intent: schrijf-runner
    
    Genereert Python runner-script voor de agent.
    
    Args:
        params: Dictionary met agent_naam, value_stream, fase
    """
    agent_naam = params["agent_naam"]
    value_stream = params.get("value_stream", "")
    fase = params.get("fase", "")
    
    gelezen_bestanden = ["input/input.md"]
    aangemaakte_bestanden = []
    
    # Lees charter voor intent-informatie
    agent_folder = Path(f"artefacten/{value_stream}.{fase}.{agent_naam}")
    charter_path = agent_folder / f"{agent_naam}.charter.md"
    if charter_path.exists():
        gelezen_bestanden.append(str(charter_path))
    
    # Lees agent-contracten voor intents
    contract_files = list(agent_folder.glob(f"{agent_naam}.*.agent.md"))
    gelezen_bestanden.extend([str(f) for f in contract_files])
    
    intents = [f.stem.replace(f"{agent_naam}.", "").replace(".agent", "") 
               for f in contract_files if ".agent.md" in f.name]
    
    # Genereer runner
    runner_path = agent_folder / f"{agent_naam}.py"
    runner_content = f'''"""
Agent Runner: {agent_naam}

Input: input/input.md met YAML frontmatter
Output: Agent-artefacten in artefacten/{value_stream}.{fase}.{agent_naam}/

Intents:
{chr(10).join(f"- {intent}" for intent in intents)}

Datum: 2026-02-06
Versie: 1.0
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional
import yaml
import re

def log_agent_action(agent_naam: str, gelezen: Optional[List[str]] = None, 
                     aangepast: Optional[List[str]] = None, 
                     aangemaakt: Optional[List[str]] = None) -> None:
    """Roept mandarin_agent_runner.py aan voor logging conform Norm 10.4."""
    cmd = [
        "python", "scripts/mandarin_agent_runner.py", agent_naam,
        "--gelezen", *(gelezen or []),
        "--aangepast", *(aangepast or []),
        "--aangemaakt", *(aangemaakt or [])
    ]
    subprocess.run(cmd, check=True)


def parse_input() -> dict:
    """Leest input/input.md en parseert YAML frontmatter."""
    input_file = Path("input/input.md")
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input bestand niet gevonden: {{input_file}}")
    
    content = input_file.read_text(encoding="utf-8")
    
    yaml_match = re.match(r'^---\\s*\\n(.*?)\\n---\\s*\\n', content, re.DOTALL)
    if not yaml_match:
        raise ValueError("Geen geldige YAML frontmatter gevonden in input.md")
    
    return yaml.safe_load(yaml_match.group(1))


{chr(10).join(f"""def handle_{intent.replace("-", "_")}(params: dict) -> None:
    \"\"\"Intent: {intent}\"\"\"
    # TODO: Implementeer intent-logica
    print(f"✓ Intent '{intent}' uitgevoerd")
    log_agent_action("{agent_naam}", gelezen=["input/input.md"], aangemaakt=[])
""" for intent in intents)}

def main() -> int:
    """Main entry point voor agent-runner."""
    try:
        params = parse_input()
        intent = params["intent"]
        
        intent_handlers = {{
{chr(10).join(f'            "{intent}": handle_{intent.replace("-", "_")},' for intent in intents)}
        }}
        
        if intent not in intent_handlers:
            print(f"✗ Onbekende intent: {{intent}}", file=sys.stderr)
            print(f"Beschikbare intents: {{', '.join(intent_handlers.keys())}}", file=sys.stderr)
            return 1
        
        intent_handlers[intent](params)
        return 0
        
    except Exception as e:
        print(f"✗ Fout bij uitvoeren agent-runner: {{e}}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
'''
    
    runner_path.write_text(runner_content, encoding="utf-8")
    aangemaakte_bestanden.append(str(runner_path))
    
    print(f"✓ Runner aangemaakt voor {agent_naam} ({len(intents)} intents)")
    
    # Log actie
    log_agent_action("agent-smeder", gelezen=gelezen_bestanden, aangemaakt=aangemaakte_bestanden)


def main() -> int:
    """
    Main entry point voor agent-smeder runner.
    
    Returns:
        0 bij succes, 1 bij fout
    """
    try:
        params = parse_input()
        intent = params["intent"]
        
        intent_handlers = {
            "leg-agent-contract-vast": handle_leg_agent_contract_vast,
            "schrijf-charter": handle_schrijf_charter,
            "schrijf-runner": handle_schrijf_runner,
        }
        
        if intent not in intent_handlers:
            print(f"✗ Onbekende intent: {intent}", file=sys.stderr)
            print(f"Beschikbare intents: {', '.join(intent_handlers.keys())}", file=sys.stderr)
            return 1
        
        intent_handlers[intent](params)
        return 0
        
    except Exception as e:
        print(f"✗ Fout bij uitvoeren agent-smeder: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())