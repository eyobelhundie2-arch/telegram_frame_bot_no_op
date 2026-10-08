from pathlib import Path
from processor import make_framed_image

BASE = Path(__file__).resolve().parent
sample = BASE / "templates" / "reference.png"
out = BASE / "test-output.png"
make_framed_image(sample, out)
print(f"Created: {out}")
