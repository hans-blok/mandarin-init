#!/usr/bin/env python3
"""
Fetch and organize agents from mandarin-agents repository.

This script fetches agent definitions (charters, prompts, runners) from the
mandarin-agents GitHub repository (including .github directory) based on a published 
manifest (agents-publicatie.json). It organizes files into the workspace according 
to their type and applies filtering based on value streams.

Usage:
    python fetch_mandarin_agents.py kennispublicatie
    python fetch_mandarin_agents.py utility
    python fetch_mandarin_agents.py --list

The script performs:
- Git clone/pull of mandarin-agents repository
- Manifest parsing with value stream filtering
- File organization (charters, prompts, runners)
- Detailed logging to logs/ folder

Design decisions:
- mandarin-agents folder is kept (not deleted) for efficient git pull reuse
- Runner modules are fully replaced, not merged
- Utility agents are always included regardless of value stream
- Type hints used throughout for maintainability
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class Agent:
    """Agent specification from manifest."""
    
    name: str
    value_stream: str
    charter_count: int = 0
    prompt_count: int = 0
    agent_count: int = 0
    runner_count: int = 0
    
    def is_utility(self) -> bool:
        """Check if this is a utility agent (applies to all value streams)."""
        return self.value_stream.lower() == "utility"
    
    def applies_to(self, target_stream: str) -> bool:
        """Check if agent applies to target value stream."""
        if self.is_utility():
            return True
        return self.value_stream.lower() == target_stream.lower()


@dataclass
class FileOperation:
    """Represents a file copy operation."""
    
    source: Path
    destination: Path
    status: str = "pending"  # pending, new, updated, unchanged, error
    
    def is_module(self) -> bool:
        """Check if this is a module directory operation."""
        return self.source.is_dir()


class ManifestParser:
    """Parse agents-publicatie.json manifest."""
    
    def __init__(self, manifest_path: Path):
        """Initialize parser with manifest path."""
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
        self.manifest_path = manifest_path
        self._data: Dict = {}
        self._agents: List[Agent] = []
        self._locations: Dict[str, str] = {}
        
    def parse(self) -> Tuple[List[Agent], Dict[str, str], Dict[str, str]]:
        """Parse manifest and return agents, metadata, and location templates.
        
        Supports both v1.x (flat list) and v2.x (nested by value stream) format.
        """
        self._data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        
        # Extract metadata
        version = str(self._data.get("versie", "unknown"))
        metadata = {
            "version": version,
            "published_at": str(self._data.get("publicatiedatum", "unknown")),
        }
        
        # Extract location templates
        self._locations = self._data.get("locaties", {})
        
        # Parse agents - support both v1.x and v2.x formats
        if "valueStreams" in self._data and isinstance(self._data["valueStreams"], dict):
            # v2.x format: nested structure with valueStreams object
            for value_stream, vs_data in self._data["valueStreams"].items():
                agents_dict = vs_data.get("agents", {})
                for agent_name, agent_data in agents_dict.items():
                    agent = Agent(
                        name=str(agent_name),
                        value_stream=str(value_stream),
                        charter_count=1,  # Always 1 charter per agent
                        prompt_count=int(agent_data.get("aantalPrompts", 0)),
                        agent_count=int(agent_data.get("aantalAgents", 0)),
                        runner_count=int(agent_data.get("aantalRunners", 0)),
                    )
                    self._agents.append(agent)
        else:
            # v1.x format: flat list with agents array
            agents_raw = self._data.get("agents", [])
            for idx, entry in enumerate(agents_raw):
                if not isinstance(entry, dict):
                    raise ValueError(f"Agent entry {idx} must be object, got {type(entry)}")
                
                name = entry.get("naam")
                value_stream = entry.get("valueStream")
                
                if not name or not value_stream:
                    raise ValueError(f"Agent entry {idx} missing required fields: naam={name}, valueStream={value_stream}")
                
                agent = Agent(
                    name=str(name),
                    value_stream=str(value_stream),
                    charter_count=1,  # Always 1 charter per agent
                    prompt_count=int(entry.get("aantalPrompts", 0)),
                    agent_count=int(entry.get("aantalAgents", 0)),
                    runner_count=int(entry.get("aantalRunners", 0)),
                )
                self._agents.append(agent)
        
        metadata["agent_count"] = str(len(self._agents))
        return self._agents, metadata, self._locations
    
    def get_value_streams(self) -> List[str]:
        """Extract unique value streams from parsed agents."""
        # For v2.x format, check if valueStreams key exists in data
        if "valueStreams" in self._data and isinstance(self._data["valueStreams"], dict):
            streams = {vs.lower() for vs in self._data["valueStreams"].keys() if vs.lower() != "utility"}
            return sorted(streams)
        
        # For v1.x format, extract from agents
        streams = {agent.value_stream.lower() for agent in self._agents if not agent.is_utility()}
        return sorted(streams)


class RepositoryManager:
    """Manage Git operations for mandarin-agents repository."""
    
    def __init__(self, repo_url: str, target_dir: Path):
        """Initialize repository manager."""
        self.repo_url = repo_url
        self.target_dir = target_dir
    
    def fetch(self) -> Path:
        """Clone or pull repository."""
        if self.target_dir.exists() and (self.target_dir / ".git").exists():
            print(f"[INFO] Repository exists, pulling latest changes...")
            self._run_git(["pull"], cwd=self.target_dir)
        else:
            print(f"[INFO] Cloning repository from {self.repo_url}...")
            self.target_dir.mkdir(parents=True, exist_ok=True)
            self._run_git(["clone", "--depth", "1", self.repo_url, str(self.target_dir)])
        
        return self.target_dir
    
    def _run_git(self, args: List[str], cwd: Path | None = None) -> str:
        """Run git command with error handling."""
        cmd = ["git"] + args
        result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
        
        if result.returncode != 0:
            raise RuntimeError(
                f"Git command failed: {' '.join(cmd)}\n"
                f"Exit code: {result.returncode}\n"
                f"Error: {result.stderr}"
            )
        
        return result.stdout.strip()


class FileOrganizer:
    """Organize agent files into workspace structure."""
    
    def __init__(self, workspace: Path, repo_path: Path, locations: Dict[str, str]):
        """Initialize organizer."""
        self.workspace = workspace
        self.repo_path = repo_path
        self.locations = locations
        
        # Target directories
        self.charters_dir = workspace / "charters-agents"
        self.agents_dir = workspace / ".github" / "agents"
        self.prompts_dir = workspace / ".github" / "prompts"
        self.scripts_dir = workspace / "scripts"
    
    def resolve_files(self, agents: List[Agent], value_stream: str) -> Tuple[List[FileOperation], List[str]]:
        """Resolve agent files to copy operations."""
        operations: List[FileOperation] = []
        warnings: List[str] = []
        
        for agent in agents:
            if not agent.applies_to(value_stream):
                continue
            
            # Charter
            charter_path = self._resolve_charter(agent)
            if charter_path:
                operations.append(charter_path)
            else:
                warnings.append(f"{agent.name}: charter not found")
            
            # Agents - always try to resolve, even if count is 0
            agent_ops = self._resolve_agents(agent)
            if agent_ops:
                operations.extend(agent_ops)
            elif agent.agent_count > 0:
                warnings.append(f"{agent.name}: expected {agent.agent_count} agent files but found none")
            
            # Prompts
            if agent.prompt_count > 0:
                prompt_ops = self._resolve_prompts(agent)
                if prompt_ops:
                    operations.extend(prompt_ops)
                else:
                    warnings.append(f"{agent.name}: expected {agent.prompt_count} prompts but found none")
            
            # Runners
            if agent.runner_count > 0:
                runner_op = self._resolve_runner(agent)
                if runner_op:
                    operations.append(runner_op)
                else:
                    warnings.append(f"{agent.name}: runner module not found")
        
        return operations, warnings
    
    def _resolve_charter(self, agent: Agent) -> FileOperation | None:
        """Resolve charter file for agent using manifest location template."""
        charter_template = self.locations.get("charters")
        if not charter_template:
            return None
        
        # Get value-stream-specific template or default
        if isinstance(charter_template, dict):
            template = charter_template.get(agent.value_stream) or charter_template.get("default")
        else:
            template = charter_template
        
        if not template:
            return None
        
        # Substitute placeholders
        charter_path_str = (
            template
            .replace("<agent-naam>", agent.name)
            .replace("<value-stream>", agent.value_stream)
        )
        charter_path = self.repo_path / charter_path_str
        
        # Try the template path first
        if charter_path.exists():
            dest = self.charters_dir / f"{agent.name}.md"
            return FileOperation(source=charter_path, destination=dest)
        
        # Fallback: try alternative naming convention (charter.<agent-naam>.md vs <agent-naam>.charter.md)
        if ".charter." in charter_path_str:
            # Try charter.<agent-naam>.md format
            alt_path_str = charter_path_str.replace(".charter.", ".")
            alt_path_str = alt_path_str.replace(f"{agent.name}.md", f"charter.{agent.name}.md")
        elif "charter." in charter_path_str:
            # Try <agent-naam>.charter.md format
            alt_path_str = charter_path_str.replace(f"charter.{agent.name}", f"{agent.name}.charter")
        else:
            return None
        
        alt_charter_path = self.repo_path / alt_path_str
        if alt_charter_path.exists():
            dest = self.charters_dir / f"{agent.name}.md"
            return FileOperation(source=alt_charter_path, destination=dest)
        
        return None
    
    def _resolve_prompts(self, agent: Agent) -> List[FileOperation]:
        """Resolve prompt files for agent using manifest location template."""
        operations: List[FileOperation] = []
        
        prompts_template = self.locations.get("prompts")
        if not prompts_template:
            return operations
        
        # Get value-stream-specific template or default
        if isinstance(prompts_template, dict):
            template = prompts_template.get(agent.value_stream) or prompts_template.get("default")
        else:
            template = prompts_template
        
        if not template:
            return operations
        
        # Substitute known placeholders
        template_path = (
            template
            .replace("<agent-naam>", agent.name)
            .replace("<value-stream>", agent.value_stream)
        )
        
        # Extract directory path and pattern from template
        # Handle both old format (<agent-naam>-<werkwoord>.prompt.md) 
        # and new format (mandarin.<agent-naam>*.prompt.md)
        if "*" in template_path:
            # Template contains wildcard, extract directory and pattern
            prompts_dir_str = template_path.rsplit("/", 1)[0]
            pattern = template_path.rsplit("/", 1)[1]
        else:
            # Old format without wildcard
            prompts_dir_str = template_path.rsplit("/", 1)[0]
            pattern = f"{agent.name}-*.prompt.md"
        
        prompts_dir = self.repo_path / prompts_dir_str
        
        if not prompts_dir.exists():
            return operations
        
        # Find all prompts matching pattern
        for prompt_file in prompts_dir.glob(pattern):
            dest = self.prompts_dir / prompt_file.name
            operations.append(FileOperation(source=prompt_file, destination=dest))
        
        return operations
    
    def _resolve_agents(self, agent: Agent) -> List[FileOperation]:
        """Resolve agent definition files using manifest location template."""
        operations: List[FileOperation] = []
        
        agents_template = self.locations.get("agents")
        
        # If no template in manifest, use default pattern based on value stream
        if not agents_template:
            # Default: exports/<value-stream>/agents/<agent-naam>*.agent.md
            agents_dir = self.repo_path / "exports" / agent.value_stream / "agents"
            pattern = f"{agent.name}*.agent.md"
        else:
            # Get value-stream-specific template or default
            if isinstance(agents_template, dict):
                template = agents_template.get(agent.value_stream) or agents_template.get("default")
            else:
                template = agents_template
            
            if not template:
                return operations
            
            # Substitute known placeholders
            template_path = (
                template
                .replace("<agent-naam>", agent.name)
                .replace("<value-stream>", agent.value_stream)
            )
            
            # Extract directory path and pattern from template
            if "*" in template_path:
                # Template contains wildcard, extract directory and pattern
                agents_dir_str = template_path.rsplit("/", 1)[0]
                pattern = template_path.rsplit("/", 1)[1]
            else:
                # No wildcard, use agent name pattern
                agents_dir_str = template_path.rsplit("/", 1)[0]
                pattern = f"{agent.name}*.agent.md"
            
            agents_dir = self.repo_path / agents_dir_str
        
        if not agents_dir.exists():
            return operations
        
        # Find all agent files matching pattern
        for agent_file in agents_dir.glob(pattern):
            dest = self.agents_dir / agent_file.name
            operations.append(FileOperation(source=agent_file, destination=dest))
        
        return operations
    
    def _resolve_runner(self, agent: Agent) -> FileOperation | None:
        """Resolve runner module for agent using manifest location template."""
        runners_template = self.locations.get("runners")
        if not runners_template:
            return None
        
        # Get value-stream-specific template or default
        if isinstance(runners_template, dict):
            template = runners_template.get(agent.value_stream) or runners_template.get("default")
        else:
            template = runners_template
        
        if not template:
            return None
        
        # Substitute placeholders
        runner_path_str = (
            template
            .replace("<agent-naam>", agent.name)
            .replace("<value-stream>", agent.value_stream)
        )
        runner_path = self.repo_path / runner_path_str
        
        # Fallback: try exports/value-stream/runners/agent-naam.py
        if not runner_path.exists():
            fallback_path = self.repo_path / "exports" / agent.value_stream / "runners" / f"{agent.name}.py"
            if fallback_path.exists():
                runner_path = fallback_path
        
        # Check if resolved path exists
        if runner_path.exists():
            if runner_path.is_dir():
                dest = self.scripts_dir / agent.name
                return FileOperation(source=runner_path, destination=dest)
            elif runner_path.suffix == ".py":
                dest = self.scripts_dir / runner_path.name
                return FileOperation(source=runner_path, destination=dest)
        
        return None
    
    def execute_operations(self, operations: List[FileOperation]) -> Dict[str, int]:
        """Execute file copy operations."""
        stats = {"new": 0, "updated": 0, "unchanged": 0, "error": 0, "modules_replaced": 0}
        
        print(f"\n[INFO] Executing {len(operations)} file operations...")
        
        for op in operations:
            try:
                if op.is_module():
                    # Module replacement: delete existing, copy new
                    if op.destination.exists():
                        shutil.rmtree(op.destination)
                        print(f"  [REMOVE] Existing module {op.destination.name}/")
                    
                    op.destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(op.source, op.destination)
                    op.status = "module_replaced"
                    stats["modules_replaced"] += 1
                    print(f"  [MODULE] {op.source.name}/ -> {op.destination.relative_to(self.workspace)}")
                else:
                    # Single file copy
                    op.destination.parent.mkdir(parents=True, exist_ok=True)
                    
                    if op.destination.exists():
                        if op.destination.read_bytes() == op.source.read_bytes():
                            op.status = "unchanged"
                        else:
                            op.status = "updated"
                    else:
                        op.status = "new"
                    
                    shutil.copy2(op.source, op.destination)
                    stats[op.status] += 1
                    print(f"  [{op.status.upper():9}] {op.source.name} -> {op.destination.relative_to(self.workspace)}")
                    
            except Exception as e:
                op.status = "error"
                stats["error"] += 1
                print(f"  [ERROR] Failed to copy {op.source.name}: {e}")
        
        return stats


class FetchLogger:
    """Write detailed fetch logs."""
    
    def __init__(self, workspace: Path):
        """Initialize logger."""
        self.workspace = workspace
        self.logs_dir = workspace / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def write_log(
        self,
        value_stream: str,
        metadata: Dict[str, str],
        agents: List[Agent],
        stats: Dict[str, int],
        warnings: List[str],
        repo_url: str,
    ) -> Path:
        """Write detailed fetch log."""
        timestamp = datetime.now()
        log_filename = f"fetch-agents-{timestamp.strftime('%Y%m%d-%H%M%S')}.md"
        log_path = self.logs_dir / log_filename
        
        lines = [
            f"# Fetch Agents Log\n\n",
            f"**Datum**: {timestamp.strftime('%Y-%m-%d')}\n",
            f"**Tijd**: {timestamp.strftime('%H:%M:%S')}\n",
            f"**Value Stream**: {value_stream}\n",
            f"**Repository**: {repo_url}\n",
            f"**Manifest Versie**: {metadata.get('version', 'unknown')}\n",
            f"**Publicatiedatum**: {metadata.get('published_at', 'unknown')}\n\n",
            f"## Status\n\n",
            f"✓ SUCCESS: {len(agents)} agents gefetched\n\n",
            f"## Gefetchte Agents\n\n",
        ]
        
        # List agents
        for agent in agents:
            agent_type = "utility" if agent.is_utility() else "value-stream"
            lines.append(f"- **{agent.name}** ({agent_type}): {agent.prompt_count} prompts")
            if agent.runner_count > 0:
                lines.append(f", {agent.runner_count} runners")
            lines.append("\n")
        
        # Statistics table
        lines.append(f"\n## Bestandsoperaties\n\n")
        lines.append(f"| Status | Aantal |\n")
        lines.append(f"|--------|--------|\n")
        lines.append(f"| Nieuw | {stats.get('new', 0)} |\n")
        lines.append(f"| Bijgewerkt | {stats.get('updated', 0)} |\n")
        lines.append(f"| Ongewijzigd | {stats.get('unchanged', 0)} |\n")
        lines.append(f"| Runner modules vervangen | {stats.get('modules_replaced', 0)} |\n")
        if stats.get('error', 0) > 0:
            lines.append(f"| Fouten | {stats.get('error', 0)} |\n")
        
        # Warnings
        if warnings:
            lines.append(f"\n## Waarschuwingen\n\n")
            for warning in warnings:
                lines.append(f"- {warning}\n")
        
        # Locations
        lines.append(f"\n## Locaties\n\n")
        lines.append(f"- Charters: `charters-agents/`\n")
        lines.append(f"- Prompts: `.github/prompts/`\n")
        lines.append(f"- Runners: `scripts/`\n")
        lines.append(f"- Log: `{log_path.relative_to(self.workspace)}`\n")
        
        # Behavior notes
        lines.append(f"\n## Overschrijfgedrag\n\n")
        lines.append(f"⚠️  **Runner modules**: Volledig verwijderd en vervangen (niet gemerged!)\n")
        lines.append(f"- Charters: Volledig overschreven met versie uit mandarin-agents\n")
        lines.append(f"- Prompts: Bestaande prompts met dezelfde naam overschreven\n\n")
        lines.append(f"Dit gedrag is by design: fetching installeert de canonieke versie uit mandarin-agents.\n")
        
        log_path.write_text("".join(lines), encoding="utf-8")
        return log_path


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch agents from mandarin-agents repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_mandarin_agents.py kennispublicatie
  python fetch_mandarin_agents.py utility
  python fetch_mandarin_agents.py --list
        """,
    )
    parser.add_argument(
        "value_stream",
        nargs="?",
        help="Target value stream (required unless --list)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available value streams and exit",
    )
    parser.add_argument(
        "--manifest",
        default="agents-publicatie.json",
        help="Manifest filename in repo root (default: agents-publicatie.json)",
    )
    parser.add_argument(
        "--repo-url",
        default="https://github.com/hans-blok/mandarin-agents.git",
        help="Repository URL (default: mandarin-agents)",
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.list and not args.value_stream:
        parser.error("value_stream is required unless --list is specified")
        return 1
    
    workspace = Path.cwd()
    repo_dir = workspace / "mandarin-agents"
    
    try:
        # Fetch repository
        repo_mgr = RepositoryManager(args.repo_url, repo_dir)
        repo_path = repo_mgr.fetch()
        
        # Parse manifest
        manifest_path = repo_path / args.manifest
        parser_obj = ManifestParser(manifest_path)
        agents, metadata, locations = parser_obj.parse()
        
        # List mode
        if args.list:
            streams = parser_obj.get_value_streams()
            print("Available value streams:")
            for stream in streams:
                applicable = [a for a in agents if a.applies_to(stream)]
                print(f"  - {stream} ({len(applicable)} agents)")
            print(f"  - utility (always included, {sum(1 for a in agents if a.is_utility())} agents)")
            print(f"\nManifest version: {metadata['version']}")
            print(f"Published: {metadata['published_at']}")
            return 0
        
        # Filter agents
        value_stream = args.value_stream
        applicable_agents = [a for a in agents if a.applies_to(value_stream)]
        
        if not applicable_agents:
            print(f"[ERROR] No agents found for value stream '{value_stream}'")
            print(f"Use --list to see available value streams")
            return 1
        
        print(f"\n[INFO] Processing {len(applicable_agents)} agents for value stream '{value_stream}'")
        
        # Organize files
        organizer = FileOrganizer(workspace, repo_path, locations)
        operations, warnings = organizer.resolve_files(applicable_agents, value_stream)
        
        if not operations:
            print("[ERROR] No files resolved for applicable agents")
            return 1
        
        # Execute operations
        stats = organizer.execute_operations(operations)
        
        # Write log
        logger = FetchLogger(workspace)
        log_path = logger.write_log(
            value_stream=value_stream,
            metadata=metadata,
            agents=applicable_agents,
            stats=stats,
            warnings=warnings,
            repo_url=args.repo_url,
        )
        
        # Print summary
        print("\nSUMMARY")
        print(f"Value-stream: {value_stream}")
        print(f"Manifest version: {metadata['version']} published: {metadata['published_at']}")
        print(f"Agents applied: {len(applicable_agents)}")
        for agent in applicable_agents:
            agent_type = "utility" if agent.is_utility() else "value-stream"
            print(f"  - {agent.name} ({agent_type})")
        
        print(f"Files copied -> new: {stats['new']}, updated: {stats['updated']}, "
              f"unchanged: {stats['unchanged']}, errors: {stats['error']}")
        
        if stats.get('modules_replaced', 0) > 0:
            print(f"Runner modules replaced: {stats['modules_replaced']} (⚠️  old content removed)")
        
        if warnings:
            print(f"\nWarnings: {len(warnings)}")
            for warning in warnings[:5]:  # Limit to first 5
                print(f"  - {warning}")
            if len(warnings) > 5:
                print(f"  ... and {len(warnings) - 5} more (see log)")
        
        print(f"\nLog: {log_path.relative_to(workspace)}")
        print("[SUCCESS] Agents fetched")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}")
        return 1
    except ValueError as e:
        print(f"[ERROR] Invalid manifest: {e}")
        return 1
    except RuntimeError as e:
        print(f"[ERROR] Operation failed: {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
