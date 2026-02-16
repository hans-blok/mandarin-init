"""Fetch agent files (prompts and contracts) for a value stream fase and copy them to a target workspace.

Bron: artefacten/<code>/<code>.<fase>.<agent>/
  - prompts/mandarin.<agent>.*.prompt.md → target/.github/prompts/
  - agent-contracten/<agent>.*.agent.md → target/.github/agents/

Typical usage (from another workspace):
    python ..\\mandarin-agents\\scripts\\fetch_prompts.py sfw.03 --source ..\\mandarin-agents --target .

Default source lookup: if this script lives in mandarin-canon, it auto-targets the
peer repo mandarin-agents (../mandarin-agents). Otherwise it uses the repo root it
is in. Override with --source as needed.

Default target: the repo root where this script lives (so calling from scripts/ still
copies into repo subfolders). Override with --target to point elsewhere.

The script reads agents-publicatie.json, finds agents for the given value stream code
and fase, collects their agent files from artefacten/, and copies them into
appropriate folders in the target workspace. A log file is written to logs/ with details
of the run. Use --dry-run to see what would happen.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SIBLING_AGENTS = REPO_ROOT.parent / "mandarin-agents"

# Prefer sibling mandarin-agents when this script is placed in mandarin-canon; else use current repo.
if REPO_ROOT.name != "mandarin-agents" and SIBLING_AGENTS.exists():
    DEFAULT_SOURCE = SIBLING_AGENTS.resolve()
else:
    DEFAULT_SOURCE = REPO_ROOT

# Default target is the repo root where this script lives so running from scripts/ keeps
# .github/prompts under the repository, not under the current working directory.
DEFAULT_TARGET = REPO_ROOT


def parse_value_stream_fase(value: str) -> Tuple[str, str]:
    if "." not in value:
        raise ValueError("Gebruik formaat <code>.<fase>, bijvoorbeeld sfw.03")
    code, fase = value.split(".", 1)
    code = code.strip().lower()
    fase = fase.strip().zfill(2)
    if not code or not fase.isdigit():
        raise ValueError("Ongeldige value stream of fase; verwacht zoiets als sfw.03")
    return code, fase


def load_publicatie(source_root: Path) -> Dict:
    manifest_path = source_root / "agents-publicatie.json"
    if not manifest_path.is_file():
        hint = "Voer een git pull uit in de bron of geef --source naar mandarin-agents."
        raise FileNotFoundError(f"Niet gevonden: {manifest_path}. {hint}")
    with manifest_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def find_agents(manifest: Dict, code: str, fase: str) -> List[str]:
    for vs in manifest.get("value_streams", []):
        if vs.get("code", "").lower() != code:
            continue
        for fase_entry in vs.get("fasen", []):
            if str(fase_entry.get("volgnummer", "")).zfill(2) == fase:
                return [agent.get("naam", "").strip() for agent in fase_entry.get("agents", []) if agent.get("naam")]
    raise ValueError(f"Geen agents gevonden voor {code}.{fase}")


def collect_agent_files(artefacten_root: Path, code: str, fase: str, agents: Iterable[str]) -> Dict[str, Dict[str, List[Path]]]:
    """Collect prompts and contracts for agents.
    
    Returns: {agent: {'prompts': [...], 'contracts': [...]}}
    """
    base = artefacten_root / code
    if not base.is_dir():
        raise FileNotFoundError(f"Artefacten map ontbreekt: {base}")

    mapping: Dict[str, Dict[str, List[Path]]] = {}
    fase_marker = f"{code}.{fase}"
    fase_dirs = [p for p in base.iterdir() if p.is_dir() and p.name.startswith(fase_marker)]
    
    print(f"DEBUG: Looking in base directory: {base}")
    print(f"DEBUG: Looking for fase_marker: {fase_marker}")
    print(f"DEBUG: Found fase directories: {[fd.name for fd in fase_dirs]}")
    
    for agent in agents:
        print(f"DEBUG: Processing agent: {agent}")
        agent_files = {'prompts': [], 'contracts': []}
        
        for fase_dir in fase_dirs:
            print(f"DEBUG: Checking fase_dir: {fase_dir}")
            
            # Prompts: prompts/mandarin.{agent}*.prompt.md
            prompts_dir = fase_dir / 'prompts'
            print(f"DEBUG: Looking for prompts in: {prompts_dir}")
            if prompts_dir.is_dir():
                print(f"DEBUG: All files in prompts directory: {[f.name for f in prompts_dir.iterdir() if f.is_file()]}")
                prompt_pattern = f"mandarin.{agent}*.prompt.md"
                print(f"DEBUG: Using prompt pattern: {prompt_pattern}")
                prompt_files = list(prompts_dir.glob(prompt_pattern))
                print(f"DEBUG: Found prompt files: {[pf.name for pf in prompt_files]}")
                agent_files['prompts'].extend(prompt_files)
            else:
                print(f"DEBUG: Prompts directory does not exist: {prompts_dir}")
            
            # Contracts: agent-contracten/{agent}.*.agent.md
            contracts_dir = fase_dir / 'agent-contracten'
            print(f"DEBUG: Looking for contracts in: {contracts_dir}")
            if contracts_dir.is_dir():
                print(f"DEBUG: All files in agent-contracten directory: {[f.name for f in contracts_dir.iterdir() if f.is_file()]}")
                contract_pattern = f"{agent}.*.agent.md"
                print(f"DEBUG: Using contract pattern: {contract_pattern}")
                contract_files = list(contracts_dir.glob(contract_pattern))
                print(f"DEBUG: Found contract files: {[cf.name for cf in contract_files]}")
                agent_files['contracts'].extend(contract_files)
            else:
                print(f"DEBUG: Contracts directory does not exist: {contracts_dir}")
        
        print(f"DEBUG: Final files for {agent}: {agent_files}")
        
        # Sort alle findings
        for file_type in agent_files:
            agent_files[file_type] = sorted(agent_files[file_type])
            
        mapping[agent] = agent_files
    
    return mapping


def copy_agent_files(mapping: Dict[str, Dict[str, List[Path]]], target_root: Path, dry_run: bool) -> Dict[str, List[Path]]:
    """Copy agent files to appropriate target directories.
    
    Returns: {'prompts': [...], 'contracts': [...]}
    """
    copied: Dict[str, List[Path]] = {'prompts': [], 'contracts': []}
    
    # Define target directories
    target_dirs = {
        'prompts': target_root / '.github' / 'prompts',
        'contracts': target_root / '.github' / 'agents'
    }
    
    # Create target directories if needed
    for file_type, target_dir in target_dirs.items():
        if not target_dir.exists() and not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"DEBUG: Created directory {target_dir}")  # Debug output
        elif target_dir.exists():
            print(f"DEBUG: Directory already exists {target_dir}")  # Debug output
    
    # Copy files
    for agent_files in mapping.values():
        for file_type, files in agent_files.items():
            if file_type not in target_dirs:
                continue  # Skip unknown file types
            target_dir = target_dirs[file_type]
            for src in files:
                dest = target_dir / src.name
                copied[file_type].append(dest)
                if dry_run:
                    continue
                try:
                    shutil.copy2(src, dest)
                    print(f"DEBUG: Copied {src} -> {dest}")  # Debug output
                except Exception as e:
                    print(f"ERROR: Failed to copy {src} -> {dest}: {e}")  # Error output
    
    return copied


def write_log(target_root: Path, code: str, fase: str, mapping: Dict[str, Dict[str, List[Path]]], copied: Dict[str, List[Path]], dry_run: bool, source_root: Path) -> Path:
    logs_dir = target_root / "logs"
    if not logs_dir.exists() and not dry_run:
        logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = logs_dir / f"fetch-agents-{code}-{fase}-{timestamp}.log"
    lines = [
        f"timestamp: {timestamp}",
        f"value_stream: {code}",
        f"fase: {fase}",
        f"source: {source_root}",
        f"target: {target_root}",
        f"dry_run: {dry_run}",
        "agents: " + ", ".join(sorted(mapping.keys())),
    ]
    
    lines.append("files:")
    for agent, file_types in sorted(mapping.items()):
        total_files = sum(len(files) for files in file_types.values())
        if total_files > 0:
            lines.append(f"  {agent}:")
            for file_type, files in file_types.items():
                if files:
                    for f in files:
                        lines.append(f"    {file_type}: {f}")
                else:
                    lines.append(f"    {file_type}: GEEN BESTANDEN GEVONDEN")
        else:
            lines.append(f"  {agent}: GEEN BESTANDEN GEVONDEN")
    
    total_copied = sum(len(files) for files in copied.values())
    if total_copied > 0:
        lines.append("copied:")
        for file_type, files in copied.items():
            if files:
                lines.append(f"  {file_type}:")
                for dest in files:
                    lines.append(f"    {dest}")
    
    if dry_run:
        lines.append("actie: dry-run, niets gekopieerd")
    
    content = "\n".join(lines) + "\n"
    if not dry_run:
        log_path.write_text(content, encoding="utf-8")
    return log_path


def build_message(code: str, fase: str, copied: Dict[str, List[Path]], missing: List[str], dry_run: bool) -> str:
    total_copied = sum(len(files) for files in copied.values())
    
    if dry_run:
        base = f"Dry-run klaar voor {code}.{fase}." if total_copied > 0 or missing else f"Geen agent bestanden gevonden voor {code}.{fase}."
    else:
        base = f"Yes! Agent bestanden voor {code}.{fase} zijn klaargezet." if total_copied > 0 else f"Geen agent bestanden gekopieerd voor {code}.{fase}."
    
    parts = [base]
    
    if total_copied > 0:
        details = []
        for file_type, files in copied.items():
            if files:
                details.append(f"{len(files)} {file_type}")
        if details:
            parts.append(f"Gekopieerd: {', '.join(details)}.")
    
    if missing:
        parts.append(f"Ontbrekend voor agents: {', '.join(sorted(missing))}.")
    
    if not dry_run and total_copied > 0:
        parts.append("Succes met de volgende stap!")
    
    return " ".join(parts)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Fetch agent files (prompts and contracts) voor een value stream fase")
    parser.add_argument("value_stream_fase", help="Formaat <code>.<fase> bijvoorbeeld sfw.03")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Pad naar mandarin-agents bron (met agents-publicatie.json)")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help="Doel workspace")
    parser.add_argument("--dry-run", action="store_true", help="Toon wat er zou gebeuren zonder te kopiëren")
    args = parser.parse_args(argv)

    code, fase = parse_value_stream_fase(args.value_stream_fase)
    source_root = args.source.expanduser().resolve()
    target_root = args.target.expanduser().resolve()
    manifest_path = source_root / "agents-publicatie.json"
    artefacten_root = source_root / "artefacten"
    if not manifest_path.is_file():
        parser.error(f"agents-publicatie.json ontbreekt in {source_root}. Tip: git pull in mandarin-agents of geef --source.")
    if not artefacten_root.is_dir():
        parser.error(f"Artefacten map ontbreekt: {artefacten_root}. Tip: git pull in mandarin-agents of geef --source.")

    manifest = load_publicatie(source_root)
    agents = find_agents(manifest, code, fase)
    mapping = collect_agent_files(artefacten_root, code, fase, agents)
    copied = copy_agent_files(mapping, target_root, args.dry_run)
    
    # Check for agents with no files at all
    missing = [agent for agent, file_types in mapping.items() 
               if sum(len(files) for files in file_types.values()) == 0]
    
    log_path = write_log(target_root, code, fase, mapping, copied, args.dry_run, source_root)

    message = build_message(code, fase, copied, missing, args.dry_run)
    print(message)
    if not args.dry_run:
        print(f"Log: {log_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
