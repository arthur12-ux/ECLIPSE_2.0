"""Compatibility shim: run `src.ingest` as a script.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("src.ingest", run_name="__main__")
