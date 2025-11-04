"""Context management for selective markdown document loading.

This module parses markdown files with metadata tags and provides
on-demand retrieval of specific sections, dramatically reducing
token usage by loading only relevant context per query.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ContextManager:
    """Manages semantic chunking and retrieval of markdown documentation.
    
    Markdown files are parsed into sections delimited by metadata tags:
        <!-- meta: timeframe=15m, concept=entry -->
        ## Section Title
        Content here...
    
    Sections can be retrieved by any combination of metadata filters.
    """
    
    def __init__(self, context_dir: Path):
        """Initialize the context manager.
        
        Args:
            context_dir: Path to directory containing markdown files
        """
        self.context_dir = context_dir
        self.sections: Dict[str, Dict[str, Any]] = {}
        self.metadata_index: Dict[str, Set[str]] = {}
        
        if context_dir.exists():
            self._parse_all_files()
    
    def _parse_all_files(self) -> None:
        """Parse all markdown files in context directory."""
        for md_file in sorted(self.context_dir.rglob("*.md")):
            self._parse_file(md_file)
    
    def _parse_file(self, file_path: Path) -> None:
        """Parse a single markdown file into tagged sections.
        
        Args:
            file_path: Path to the markdown file
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: Failed to read {file_path}: {e}")
            return
        
        # Pattern matches: <!-- meta: key=val, key2=val2 -->\n## Title\nContent
        # Captures until next meta tag, next h2 header, or end of file
        pattern = r'<!--\s*meta:\s*(.*?)\s*-->\s*\n##\s+(.*?)\n(.*?)(?=<!--\s*meta:|^##\s+|\Z)'
        
        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            meta_str, title, text = match.groups()
            
            # Parse metadata string into dict
            metadata = self._parse_metadata(meta_str)
            
            # Generate unique section ID
            section_id = f"{file_path.stem}:{title.strip()}"
            
            # Store section
            self.sections[section_id] = {
                'id': section_id,
                'title': title.strip(),
                'content': text.strip(),
                'metadata': metadata,
                'source_file': file_path.name,
                'source_path': str(file_path.relative_to(self.context_dir.parent))
            }
            
            # Update metadata index for fast filtering
            # Handle multi-valued metadata (e.g., tag can have multiple values)
            for key, values in metadata.items():
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    index_key = f"{key}={value}"
                    if index_key not in self.metadata_index:
                        self.metadata_index[index_key] = set()
                    self.metadata_index[index_key].add(section_id)
    
    def _parse_metadata(self, meta_str: str) -> Dict[str, Any]:
        """Parse metadata string into dictionary with multi-value support.
        
        Args:
            meta_str: Comma-separated key=value pairs or bare tokens
            
        Returns:
            Dictionary of metadata key-value pairs (values can be lists)
            
        Examples:
            "core" -> {"tag": "core"}
            "timeframe=15m, concept=entry" -> {"timeframe": "15m", "concept": "entry"}
            "tag=journal, tag=all_trades" -> {"tag": ["journal", "all_trades"]}
        """
        metadata: Dict[str, Any] = {}
        
        for item in meta_str.split(','):
            item = item.strip()
            
            if '=' in item:
                # Key-value pair
                key, value = item.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle duplicate keys by creating lists
                if key in metadata:
                    # Convert to list if not already
                    if not isinstance(metadata[key], list):
                        metadata[key] = [metadata[key]]
                    metadata[key].append(value)
                else:
                    metadata[key] = value
            else:
                # Bare token (e.g., "core") -> treat as tag=core
                # Handle duplicate "tag" entries
                if 'tag' in metadata:
                    if not isinstance(metadata['tag'], list):
                        metadata['tag'] = [metadata['tag']]
                    metadata['tag'].append(item)
                else:
                    metadata['tag'] = item
        
        return metadata
    
    def get_sections(
        self,
        timeframe: Optional[str] = None,
        concept: Optional[str] = None,
        tag: Optional[str] = None,
        **extra_filters
    ) -> List[Dict[str, Any]]:
        """Retrieve sections matching metadata filters.
        
        Args:
            timeframe: Filter by timeframe (e.g., "15m", "1h", "daily")
            concept: Filter by concept (e.g., "entry", "structure", "liquidity")
            tag: Filter by custom tag (e.g., "core", "journal")
            **extra_filters: Additional metadata key=value filters
            
        Returns:
            List of section dictionaries containing title, content, metadata, and source info
            
        Example:
            # Get all 15m entry-related sections
            sections = mgr.get_sections(timeframe="15m", concept="entry")
            
            # Get all core personality sections
            sections = mgr.get_sections(tag="core")
        """
        filters = {}
        if timeframe:
            filters['timeframe'] = timeframe
        if concept:
            filters['concept'] = concept
        if tag:
            filters['tag'] = tag
        filters.update(extra_filters)
        
        if not filters:
            return list(self.sections.values())
        
        # Start with all sections that match first filter
        first_key = next(iter(filters.keys()))
        first_val = filters[first_key]
        index_key = f"{first_key}={first_val}"
        
        if index_key in self.metadata_index:
            matching_ids = self.metadata_index[index_key].copy()
        else:
            return []
        
        # Intersect with other filters
        for key, value in list(filters.items())[1:]:
            index_key = f"{key}={value}"
            if index_key in self.metadata_index:
                matching_ids &= self.metadata_index[index_key]
            else:
                return []
        
        return [self.sections[sid] for sid in matching_ids]
    
    def get_core_context(self) -> str:
        """Get all sections marked as 'core' (always-loaded context).
        
        Returns:
            Formatted string of all core sections
        """
        core_sections = self.get_sections(tag="core")
        return self._format_sections(core_sections)
    
    def get_context_menu(self) -> str:
        """Generate a summary of available context sections.
        
        Returns:
            Human-readable menu of available metadata tags and values
            
        Example output:
            Available Context:
            - timeframe: 1m, 5m, 15m, 1h, 4h, 1d, daily
            - concept: entry, exit, structure, liquidity, risk
            - tag: core, journal
        """
        # Collect all unique metadata keys and values
        menu_data: Dict[str, Set[str]] = {}
        
        for section in self.sections.values():
            for key, value in section['metadata'].items():
                if key not in menu_data:
                    menu_data[key] = set()
                
                # Handle both single values and lists
                if isinstance(value, list):
                    menu_data[key].update(value)
                else:
                    menu_data[key].add(value)
        
        if not menu_data:
            return "No tagged context available."
        
        lines = ["Available Context:"]
        for key in sorted(menu_data.keys()):
            values = ", ".join(sorted(menu_data[key]))
            lines.append(f"- {key}: {values}")
        
        return "\n".join(lines)
    
    def _format_sections(self, sections: List[Dict[str, Any]]) -> str:
        """Format sections for inclusion in prompt.
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            Formatted markdown string
        """
        if not sections:
            return ""
        
        formatted = []
        for section in sections:
            formatted.append(f"## {section['title']}")
            formatted.append(f"*Source: {section['source_file']}*\n")
            formatted.append(section['content'])
            formatted.append("")  # Blank line between sections
        
        return "\n".join(formatted)
    
    def search_content(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword search across all sections.
        
        Args:
            query: Search string
            limit: Maximum number of results to return
            
        Returns:
            List of matching sections, ranked by relevance
            
        Note:
            This is a basic implementation. For production, consider
            using proper text search or embeddings-based retrieval.
        """
        query_lower = query.lower()
        results = []
        
        for section in self.sections.values():
            # Simple scoring: count query word occurrences
            content_lower = section['content'].lower()
            title_lower = section['title'].lower()
            
            score = 0
            score += content_lower.count(query_lower) * 1
            score += title_lower.count(query_lower) * 3  # Title matches worth more
            
            if score > 0:
                results.append((score, section))
        
        # Sort by score descending and return top results
        results.sort(reverse=True, key=lambda x: x[0])
        return [section for _, section in results[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded context.
        
        Returns:
            Dictionary containing section counts and metadata stats
        """
        total_sections = len(self.sections)
        total_chars = sum(len(s['content']) for s in self.sections.values())
        
        metadata_counts = {}
        for section in self.sections.values():
            for key in section['metadata'].keys():
                metadata_counts[key] = metadata_counts.get(key, 0) + 1
        
        return {
            'total_sections': total_sections,
            'total_characters': total_chars,
            'metadata_keys': list(metadata_counts.keys()),
            'sections_per_key': metadata_counts
        }