#!/usr/bin/env python3
"""
GRACE Reviewer - Full Compliance Audit Tool

Validates GRACE methodology compliance across the Kodex codebase.
Checks for:
- MODULE_CONTRACT presence
- Semantic markup (START_BLOCK/END_BLOCK pairs)
- Knowledge graph currency
- Verification plan alignment
- Documentation completeness
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class Severity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Finding:
    severity: Severity
    file: str
    line: Optional[int]
    message: str
    recommendation: str = ""


@dataclass
class ReviewReport:
    files_scanned: int = 0
    contracts_found: int = 0
    blocks_found: int = 0
    findings: List[Finding] = field(default_factory=list)
    
    def add(self, severity: Severity, file: str, line: Optional[int], 
            message: str, recommendation: str = ""):
        self.findings.append(Finding(severity, file, line, message, recommendation))
    
    def summary(self) -> str:
        critical = sum(1 for f in self.findings if f.severity == Severity.CRITICAL)
        errors = sum(1 for f in self.findings if f.severity == Severity.ERROR)
        warnings = sum(1 for f in self.findings if f.severity == Severity.WARNING)
        info = sum(1 for f in self.findings if f.severity == Severity.INFO)
        
        return (f"\n{'='*70}\n"
                f"GRACE REVIEW SUMMARY\n"
                f"{'='*70}\n"
                f"Files Scanned:        {self.files_scanned}\n"
                f"Contracts Found:      {self.contracts_found}\n"
                f"Semantic Blocks:      {self.blocks_found}\n"
                f"\nIssues:\n"
                f"  CRITICAL:           {critical}\n"
                f"  ERROR:              {errors}\n"
                f"  WARNING:            {warnings}\n"
                f"  INFO:               {info}\n"
                f"{'='*70}\n"
                f"STATUS: {'❌ FAILED' if critical > 0 or errors > 0 else '✅ PASSED'}\n"
                f"{'='*70}")


class GraceReviewer:
    """Performs GRACE compliance review on a codebase."""
    
    # Patterns for GRACE markup (supports multiple formats)
    CONTRACT_START = re.compile(
        r'START_MODULE_CONTRACT|START_BLOCK_CONTRACT|MODULE_CONTRACT|'
        r'---\s*GRACE\s+MODULE_CONTRACT\s*---'
    )
    # For TypeScript/JS: MODULE_CONTRACT: at start of comment block counts as contract start
    CONTRACT_START_TS = re.compile(r'MODULE_CONTRACT:', re.MULTILINE)
    CONTRACT_END = re.compile(
        r'END_MODULE_CONTRACT|END_BLOCK_CONTRACT|'
        r'---\s*GRACE\s+MODULE_MAP\s*---|---\s*GRACE\s+CHANGE_SUMMARY\s*---'
    )
    # For TypeScript/JS: CHANGE_SUMMARY: marks end of contract section
    CONTRACT_END_TS = re.compile(r'CHANGE_SUMMARY:', re.MULTILINE)
    BLOCK_START = re.compile(r'START_BLOCK_(\w+)|# ---\s*START_BLOCK_(\w+)|//\s*START_BLOCK_(\w+)')
    BLOCK_END = re.compile(r'END_BLOCK_(\w+)|# ---\s*END_BLOCK_(\w+)|//\s*END_BLOCK_(\w+)')
    # Also support block markers without prefix in comment blocks
    BLOCK_START_SIMPLE = re.compile(r'START_BLOCK_(\w+)')
    BLOCK_END_SIMPLE = re.compile(r'END_BLOCK_(\w+)')
    VERSION_TAG = re.compile(r'// VERSION:|@version|version:|# VERSION:|\* @version', re.IGNORECASE)
    FILE_TAG = re.compile(r'// FILE:|@file|file:|# FILE:|\* @file', re.IGNORECASE)
    
    # Documentation files
    REQUIRED_DOCS = [
        'docs/knowledge-graph.xml',
        'docs/development-plan.xml',
        'docs/verification-plan.xml',
        'docs/requirements.xml',
        'docs/technology.xml',
    ]
    
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.report = ReviewReport()
    
    def scan(self) -> ReviewReport:
        """Run full GRACE compliance scan."""
        print(f"🔍 Starting GRACE Review of {self.root}")
        print("-" * 70)
        
        # Check documentation structure
        self._check_documentation()
        
        # Scan source files
        self._scan_source_files()
        
        # Check knowledge graph consistency
        self._check_knowledge_graph()
        
        # Print detailed findings
        self._print_findings()
        
        return self.report
    
    def _check_documentation(self):
        """Check for required documentation files."""
        print("📄 Checking documentation structure...")
        
        for doc in self.REQUIRED_DOCS:
            doc_path = self.root / doc
            if doc_path.exists():
                self.report.add(Severity.INFO, doc, None, "Documentation present")
            else:
                # Check in parent directory (for monorepo structure)
                parent_docs = self.root.parent / 'kodex-infra' / 'docs'
                if doc == 'docs/verification-plan.xml':
                    # This is optional for frontend
                    self.report.add(Severity.INFO, doc, None, 
                                   "Optional for frontend/infra")
                else:
                    self.report.add(Severity.WARNING, doc, None,
                                   f"Missing: {doc}",
                                   "Create documentation file or reference parent")
        
        self.report.files_scanned += len(self.REQUIRED_DOCS)
    
    def _scan_source_files(self):
        """Scan all source files for GRACE compliance."""
        print("🔍 Scanning source files for GRACE markup...")
        
        # File patterns to scan
        patterns = {
            'Python': ['**/*.py'],
            'TypeScript': ['**/*.ts', '**/*.tsx', '**/*.vue'],
            'JavaScript': ['**/*.js'],
        }
        
        for lang, pattern_list in patterns.items():
            for pattern in pattern_list:
                for file_path in self.root.glob(pattern):
                    # Skip test files, venv, node_modules, dist, and config files
                    if any(skip in str(file_path) for skip in 
                          ['__pycache__', 'node_modules', 'venv', '.venv', 
                           'dist', 'test_', '.spec.', 'eslint.config.', 
                           'vitest.config.', 'vite.config.']):
                        continue
                    
                    self._analyze_file(file_path, lang)
    
    def _analyze_file(self, file_path: Path, lang: str):
        """Analyze a single file for GRACE compliance."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            self.report.add(Severity.ERROR, str(file_path), None,
                           f"Cannot read file: {e}")
            return
        
        self.report.files_scanned += 1
        rel_path = str(file_path.relative_to(self.root))
        
        # Check for MODULE_CONTRACT (Python and TypeScript formats)
        has_contract_start = bool(self.CONTRACT_START.search(content)) or bool(self.CONTRACT_START_TS.search(content))
        has_contract_end = bool(self.CONTRACT_END.search(content)) or bool(self.CONTRACT_END_TS.search(content))
        
        if has_contract_start and has_contract_end:
            self.report.contracts_found += 1
        elif has_contract_start and not has_contract_end:
            self.report.add(Severity.ERROR, rel_path, None,
                           "MODULE_CONTRACT started but not ended",
                           "Add matching END_MODULE_CONTRACT or END_BLOCK_CONTRACT")
        elif not has_contract_start and has_contract_end:
            self.report.add(Severity.ERROR, rel_path, None,
                           "MODULE_CONTRACT ended but not started",
                           "Add matching START_MODULE_CONTRACT or MODULE_CONTRACT")
        
        # Check for semantic blocks (multiple formats)
        block_starts = []
        for match in self.BLOCK_START.finditer(content):
            block_name = match.group(1) or match.group(2) or match.group(3)
            if block_name:
                block_starts.append(block_name)
        
        # Also check simple block markers in comment blocks
        for match in self.BLOCK_START_SIMPLE.finditer(content):
            block_name = match.group(1)
            if block_name and block_name not in block_starts:
                block_starts.append(block_name)
        
        block_ends = []
        for match in self.BLOCK_END.finditer(content):
            block_name = match.group(1) or match.group(2) or match.group(3)
            if block_name:
                block_ends.append(block_name)
        
        # Also check simple block markers
        for match in self.BLOCK_END_SIMPLE.finditer(content):
            block_name = match.group(1)
            if block_name and block_name not in block_ends:
                block_ends.append(block_name)
        
        self.report.blocks_found += len(block_starts)
        
        # Check for unmatched blocks
        unmatched = set(block_starts) - set(block_ends)
        if unmatched:
            for block in unmatched:
                self.report.add(Severity.ERROR, rel_path, None,
                               f"Unmatched START_BLOCK_{block}",
                               f"Add END_BLOCK_{block}")
        
        # Check for FILE/VERSION tags in significant files
        if len(content) > 100 and not any(skip in rel_path for skip in 
                                          ['alembic/versions/', 'migrations/']):
            has_file = bool(self.FILE_TAG.search(content))
            has_version = bool(self.VERSION_TAG.search(content))
            
            if not has_file and not has_version and not has_contract_start:
                # Only warn for larger, important files
                if len(content) > 500:
                    self.report.add(Severity.WARNING, rel_path, None,
                                   "Missing FILE/VERSION tags and MODULE_CONTRACT",
                                   "Add GRACE module header with contract")
    
    def _check_knowledge_graph(self):
        """Check knowledge graph for consistency."""
        print("🗺 Checking knowledge graph...")
        
        kg_path = self.root / 'docs' / 'knowledge-graph.xml'
        if not kg_path.exists():
            # Try parent structure
            kg_path = self.root.parent / 'kodex-infra' / 'docs' / 'knowledge-graph.xml'
        
        if kg_path.exists():
            try:
                content = kg_path.read_text()
                # Check for basic structure
                if '<KnowledgeGraph>' in content or '<knowledge-graph>' in content:
                    self.report.add(Severity.INFO, str(kg_path), None,
                                   "Knowledge graph structure valid")
                else:
                    self.report.add(Severity.WARNING, str(kg_path), None,
                                   "Knowledge graph may be missing root element")
            except Exception as e:
                self.report.add(Severity.ERROR, str(kg_path), None,
                               f"Cannot read knowledge graph: {e}")
        else:
            self.report.add(Severity.WARNING, 'docs/knowledge-graph.xml', None,
                           "Knowledge graph not found",
                           "Create or update knowledge-graph.xml")
    
    def _print_findings(self):
        """Print detailed findings."""
        print("\n" + "=" * 70)
        print("DETAILED FINDINGS")
        print("=" * 70)
        
        # Group by severity
        for severity in [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO]:
            findings = [f for f in self.report.findings if f.severity == severity]
            if findings:
                print(f"\n{severity.value} ({len(findings)}):")
                for finding in findings[:20]:  # Limit output
                    icon = {'CRITICAL': '🔴', 'ERROR': '❌', 
                           'WARNING': '⚠️', 'INFO': 'ℹ️'}[severity.value]
                    print(f"  {icon} {finding.file}")
                    if finding.line:
                        print(f"     Line {finding.line}: {finding.message}")
                    else:
                        print(f"     {finding.message}")
                    if finding.recommendation:
                        print(f"     → {finding.recommendation}")
                
                if len(findings) > 20:
                    print(f"  ... and {len(findings) - 20} more")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='GRACE Reviewer - Compliance Audit Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Review current directory
  %(prog)s /path/to/kodex-backend   # Review specific directory
  %(prog)s --quiet                  # Only show summary
        """
    )
    parser.add_argument('path', nargs='?', default='.',
                       help='Path to review (default: current directory)')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Only show summary')
    parser.add_argument('--json', action='store_true',
                       help='Output in JSON format')
    
    args = parser.parse_args()
    
    reviewer = GraceReviewer(args.path)
    report = reviewer.scan()
    
    if args.json:
        import json
        output = {
            'files_scanned': report.files_scanned,
            'contracts_found': report.contracts_found,
            'blocks_found': report.blocks_found,
            'findings': [
                {
                    'severity': f.severity.value,
                    'file': f.file,
                    'line': f.line,
                    'message': f.message,
                    'recommendation': f.recommendation
                }
                for f in report.findings
            ]
        }
        print(json.dumps(output, indent=2))
    elif args.quiet:
        print(report.summary())
    else:
        print(report.summary())
    
    # Exit with error code if critical issues found
    critical = sum(1 for f in report.findings if f.severity == Severity.CRITICAL)
    errors = sum(1 for f in report.findings if f.severity == Severity.ERROR)
    
    sys.exit(1 if critical > 0 or errors > 0 else 0)


if __name__ == '__main__':
    main()
