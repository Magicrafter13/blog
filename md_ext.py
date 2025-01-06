"""Markdown extensions."""

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
