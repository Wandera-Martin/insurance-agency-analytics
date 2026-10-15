"""Execute the Phase 4 notebook with this interpreter; save only a successful run."""

import argparse
import sys
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient

from dataset import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "notebooks/03_persistency_retention.ipynb"
    )
    args = parser.parse_args()
    notebook = nbformat.read(ROOT / "notebooks/03_persistency_retention.ipynb", as_version=4)
    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv[0] = sys.executable
    client = NotebookClient(
        notebook, km=manager, timeout=300, resources={"metadata": {"path": str(ROOT)}}
    )
    try:
        client.execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, args.output)
    print(f"Executed every notebook cell successfully: {args.output}")


if __name__ == "__main__":
    main()
