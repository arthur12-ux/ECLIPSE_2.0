"""Compatibility shim: run `src.rag` as a script.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("src.rag", run_name="__main__")

