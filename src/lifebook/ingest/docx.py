"""Read a .docx as a list of paragraph strings, with no third-party dependency.

A .docx is a zip; word/document.xml holds the text. In-paragraph line breaks
(<w:br>) and tabs (<w:tab>) become '\\n' and '\\t' so runs on either side of a break
do not fuse into one word. The output is a flat paragraph stream in document order,
not a structured document. Paragraphs nested inside another paragraph (a text box's
<w:txbxContent>) are folded into their container and not emitted a second time, so
their text is never doubled.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def read_paragraphs(path: Path | str) -> list[str]:
    """Return the document's paragraphs in order (text trimmed, nbsp normalized)."""
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)

    # ElementTree has no parent pointers; build a child -> parent map to detect nesting.
    parents = {child: parent for parent in root.iter() for child in parent}

    def nested_in_paragraph(node) -> bool:
        node = parents.get(node)
        while node is not None:
            if node.tag == _W + "p":
                return True
            node = parents.get(node)
        return False

    out: list[str] = []
    for para in root.iter(_W + "p"):
        # A nested paragraph (e.g. inside a text box) is walked as part of its ancestor
        # below; skip it here so its text is emitted once, not twice.
        if nested_in_paragraph(para):
            continue
        parts: list[str] = []
        for node in para.iter():  # runs and their children, in document order
            if node.tag == _W + "t":
                parts.append(node.text or "")
            elif node.tag in (_W + "br", _W + "cr"):
                parts.append("\n")
            elif node.tag == _W + "tab":
                parts.append("\t")
        out.append("".join(parts).replace("\xa0", " ").strip())
    return out
