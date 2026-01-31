from typing import Dict, List, Protocol
from src.agent.document_generator import DocumentGenerator

class ContentStrategy(Protocol):
    """Protocol for rendering strategies (SOLID: ISP/DIP)"""
    def render(self, doc: Dict, segments: List[Dict]) -> str:
        ...

class FormattedContentStrategy:
    """Strategy for high-quality formatted content (Kimi/M2)"""
    def render(self, doc: Dict, segments: List[Dict]) -> str:
        return doc.get("formatted_content") or ""

class SegmentDocumentStrategy:
    """Strategy for building document from segments using Generator"""
    def __init__(self, generator: DocumentGenerator):
        self.generator = generator

    def render(self, doc: Dict, segments: List[Dict]) -> str:
        try:
            topics = self.generator._group_by_topic(segments)
            return self.generator._build_markdown(doc, topics)
        except Exception:
            return ""

class RawContentStrategy:
    """Fallback strategy for raw text"""
    def render(self, doc: Dict, segments: List[Dict]) -> str:
        # Priority: Edited > Formatted (as fallback) > Raw
        return doc.get("edited_content") or doc.get("formatted_content") or doc.get("raw_content") or ""

class ContentRenderer:
    """
    Context class for Strategy Pattern (SOLID: OCP).
    Decides which rendering strategy to apply based on available data.
    """
    def __init__(self):
        self.generator = DocumentGenerator()
        self.formatted_strategy = FormattedContentStrategy()
        self.segment_strategy = SegmentDocumentStrategy(self.generator)
        self.raw_strategy = RawContentStrategy()

    def render_transcription(self, doc: Dict, segments: List[Dict]) -> str:
        # 1. Try Professional Format (if explicit flag or if content exists)
        if doc.get("formatted_content") and (doc.get("is_formatted") or not doc.get("raw_content")):
            return self.formatted_strategy.render(doc, segments)
            
        # 2. Try Segment Reconstruction
        if segments:
            content = self.segment_strategy.render(doc, segments)
            if content: return content
            
        # 3. Fallback to any remaining text content
        content = self.raw_strategy.render(doc, segments)
        return content or "# Sin contenido disponible"
