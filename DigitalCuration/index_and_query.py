"""Compatibility shim: run `src.index_and_query` as a script.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("src.index_and_query", run_name="__main__")
