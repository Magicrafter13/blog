"""Markdown extensions."""

import re
import xml.etree.ElementTree

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

class HeadingShiftProcessor(Treeprocessor):  # pylint: disable=too-few-public-methods
    """Find all <h> elements and increase their level."""

    def run(self, root):
        """Largely adapted from ChatGPT."""
        for element in root.iter():
            if element.tag.startswith('h') and element.tag[1:].isdigit():
                level = int(element.tag[1:])
                element.tag = f'h{level + 2}'

class HeadingShiftExtension(Extension):
    """Extend Markdown library with heading shifter."""

    def extendMarkdown(self, md):
        """Register extension in the Markdown engine."""
        # Priority arbitrarily chosen by ChatGPT...
        md.treeprocessors.register(HeadingShiftProcessor(md), 'shiftheadings', 15)

class HeadingLinkProcessor(Treeprocessor):  # pylint: disable=too-few-public-methods
    """Add clickable and hyperlinkable IDs to every heading."""

    def run(self, root):
        """Add anchor with self id to every heading."""
        for element in root.iter():
            if element.tag in { 'h1', 'h2', 'h3', 'h4', 'h5', 'h6' }:
                # Heading text, normalized
                text = re.sub(r'[^a-zA-Z0-9 ]', '', element.text).replace(' ', '-').lower()

                # Link element
                anchor = xml.etree.ElementTree.Element(
                    'a',
                    attrib={
                        'href': f'#{text}',
                        'id': text,
                        'class': 'markdown-heading',
                        'aria-label': 'Direct link to this heading.' })
                anchor.text = '#'

                # Update heading element
                anchor.tail = f' {element.text}'
                element.text = None
                element.insert(0, anchor)

class HeadingLinkExtension(Extension):
    """Extend Markdown library with heading links."""

    def extendMarkdown(self, md):
        """Register extension in the Markdown engine."""
        md.treeprocessors.register(HeadingLinkProcessor(md), 'linkheadings', 14)
