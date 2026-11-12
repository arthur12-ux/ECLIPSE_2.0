"""Compatibility shim: run `src.llm_test_connection` as a script.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("src.llm_test_connection", run_name="__main__")
