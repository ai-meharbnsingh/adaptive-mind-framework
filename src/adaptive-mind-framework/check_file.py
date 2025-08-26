import chardet
import os

file_path = "scripts/prepare_session_context.py" # Adjust if you run this from elsewhere

try:
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    # Detect encoding
    result = chardet.detect(raw_data)
    print(f"Detected encoding: {result['encoding']} with confidence {result['confidence']:.2f}")

    # Decode and print content, character by character, showing ordinals
    print("\n--- File Content (Character Analysis) ---")
    decoded_content = raw_data.decode(result['encoding'], errors='replace') # Replace errors for visibility

    # Print around the suspected line (approx. line 34)
    lines = decoded_content.splitlines()
    start_line = max(0, 34 - 5) # Print 5 lines before
    end_line = min(len(lines), 34 + 5) # Print 5 lines after

    for i in range(start_line, end_line):
        line_num = i + 1
        line = lines[i]
        print(f"Line {line_num:3d}: ", end="")
        for char in line:
            # Highlight non-ASCII printable characters (32-126 are printable ASCII)
            # and potentially dangerous invisible characters (e.g., zero-width spaces)
            if 32 <= ord(char) <= 126:
                print(f"{char}", end="")
            elif char == '\t':
                print("[TAB]", end="")
            elif char == ' ':
                print("[SPACE]", end="")
            else:
                print(f"[U+{ord(char):04X}]", end="") # Print Unicode codepoint for non-printable/non-ASCII
        print() # Newline for the next line

    print("\n--- Searching for 'validate_phase_num' ---")
    found_def = False
    for i, line in enumerate(lines):
        if "def validate_phase_num" in line:
            print(f"Found 'def validate_phase_num' on line {i+1}:")
            print(line)
            # Also print the raw bytes for that line if found
            line_raw = raw_data.splitlines()[i]
            print(f"Raw bytes for this line: {line_raw.hex()}")
            found_def = True
            break
    if not found_def:
        print("'def validate_phase_num' string not found in file content.")


except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")