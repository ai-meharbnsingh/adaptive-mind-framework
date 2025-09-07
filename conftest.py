import sys
from pathlib import Path

project_root = Path(__file__).parent
framework_core = project_root / "01_Framework_Core"
sys.path.insert(0, str(framework_core))