import sys
import os
from pathlib import Path

def generate_source_txt(root_dir, output_file):
    root_path = Path(root_dir).resolve()

    if not root_path.is_dir():
        print(f"Error: {root_dir} is not a valid directory.")
        sys.exit(1)

    # Standard extensions to include; feel free to add more (e.g., .js, .cpp)
    valid_extensions = {'.py', '.java', '.c', '.h', '.html', '.css', '.sh', '.ts', '.tsx', '.rs'}

    out_path = Path(output_file).resolve()

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Use os.walk so we can skip "node_modules" directories efficiently
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Remove any "node_modules" or "target" dirs so os.walk won't descend into them
            dirnames[:] = [d for d in dirnames if d.lower() not in ('node_modules', 'target')]

            for filename in filenames:
                file_path = Path(dirpath) / filename
                if file_path.suffix in valid_extensions:
                    if file_path.resolve() == out_path:
                        continue

                    try:
                        relative_path = file_path.relative_to(root_path)

                        # Write the header
                        outfile.write(f"\n{'='*80}\n")
                        outfile.write(f"FILE: {relative_path}\n")
                        outfile.write(f"{'='*80}\n\n")

                        # Write the content
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
                            outfile.write(infile.read())
                            outfile.write("\n")

                    except Exception as e:
                        print(f"Could not read {file_path}: {e}")

    print(f"Done! Source code compiled into {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <directory_path> [output_filename]")
        sys.exit(1)

    target_dir = sys.argv[1]
    out_name = sys.argv[2] if len(sys.argv) > 2 else "source_compilation.txt"
    
    generate_source_txt(target_dir, out_name)
