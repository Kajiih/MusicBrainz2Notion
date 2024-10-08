"""
Simple script to concatenate the content of files in source code.

Can be used to feed a LLM.
"""

from pathlib import Path

source_directory = "src"
output_file = "dev/_concatenated_src.py"
exclude_patterns = [
    "__pycache__",
    "*.pyc",
    "*.md",
    "*.json",
    "py.typed",
    "__init__.py",
]


def contains_code(content: str) -> bool:
    """
    Check if the content contains any lines of code, excluding comments and multi-line string literals.

    Args:
        content (str): The content of the file as a string.

    Returns:
        bool: True if the file contains code lines, False otherwise.
    """
    in_multiline_comment = False

    for line in content.splitlines():
        # Strip whitespace from the line
        stripped_line = line.strip()

        # Check for the start or end of a multi-line comment (""" or ''')
        if stripped_line.startswith(('"""', "'''")) and not in_multiline_comment:
            # If the line starts and ends with triple quotes, toggle only once
            if stripped_line.endswith(('"""', "'''")) and len(stripped_line) > 3:  # noqa: PLR2004
                continue
            # Enter multi-line comment state
            in_multiline_comment = True
            continue
        elif stripped_line.endswith(('"""', "'''")) and in_multiline_comment:  # noqa: RET507
            # Exit multi-line comment state
            in_multiline_comment = False
            continue

        # If we are inside a multi-line comment, skip this line
        if in_multiline_comment:
            continue

        # Check if the line is not empty and is not a single-line comment
        if stripped_line and not stripped_line.startswith("#"):
            return True

    return False


def concatenate_files(source_dir: str, output_file: str, exclude_patterns: list[str]) -> None:
    """
    Concatenate all files in the source directory into a single file, adding each file's relative path as a header.

    Args:
        source_dir (str): The directory containing the source files to be concatenated.
        output_file (str): The path to the output file where the concatenated content will be saved.
        exclude_patterns (List[str]): A list of glob patterns to exclude files or directories.
    """
    source_path = Path(source_dir)
    output_path = Path(output_file)

    if not source_path.is_dir():
        print(f"Error: {source_dir} is not a valid directory.")
        return

    with output_path.open("w", encoding="utf-8") as outfile:
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(source_path)

                # Skip files or directories that match the exclude patterns
                if any(file_path.match(pattern) or relative_path.match(pattern) for pattern in exclude_patterns):
                    continue

                # Read the entire content of the file
                with file_path.open(encoding="utf-8") as file:
                    file_content = file.read()

                # Check if the file contains actual code
                if not contains_code(file_content):
                    continue

                # Write the relative path as a header
                outfile.write(f"\n# %% === {relative_path} === #\n\n")

                # Write the original file content to the output file
                outfile.write(file_content)
                outfile.write("\n\n")

    print(f"Concatenated files have been saved to: {output_path}")


if __name__ == "__main__":
    concatenate_files(source_directory, output_file, exclude_patterns)
