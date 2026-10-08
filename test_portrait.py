from pathlib import Path
import sys
from processor import make_framed_image

if len(sys.argv) != 2:
    print(r'Usage: python test_portrait.py "C:\path\to\portrait.jpg"')
    raise SystemExit(1)

input_path = Path(sys.argv[1])
if not input_path.exists():
    print(f"File not found: {input_path}")
    raise SystemExit(1)

output_path = input_path.with_name(input_path.stem + "_framed.png")
make_framed_image(input_path, output_path)
print(f"Success: {output_path}")
