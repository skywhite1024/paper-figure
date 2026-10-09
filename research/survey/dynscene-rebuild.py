"""Run the reviewed paper-specific DynScene reconstruction."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[1]/'reconstruct_dynscene.py'),run_name='__main__')
