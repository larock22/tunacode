"""Custom lexers for syntax highlighting in the CLI."""

import re

from prompt_toolkit.lexers import Lexer


class FileReferenceLexer(Lexer):
    """Lexer that highlights @file references in light blue."""

    # Pattern to match @file references
    FILE_REF_PATTERN = re.compile(r"@([\w./_-]+)")

    def lex_document(self, document):
        """Return a formatted text list for the given document."""
        lines = document.text.split("\n")

        def get_line_tokens(line_number):
            """Get tokens for a specific line."""
            if line_number >= len(lines):
                return []

            line = lines[line_number]
            tokens = []
            last_end = 0

            # Find all @file references in the line
            for match in self.FILE_REF_PATTERN.finditer(line):
                start, end = match.span()

                # Add text before the match
                if start > last_end:
                    tokens.append(("", line[last_end:start]))

                # Add the @file reference with styling
                tokens.append(("class:file-reference", match.group(0)))
                last_end = end

            # Add remaining text
            if last_end < len(line):
                tokens.append(("", line[last_end:]))

            return tokens

        return get_line_tokens
