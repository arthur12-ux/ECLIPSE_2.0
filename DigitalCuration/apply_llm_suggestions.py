"""Compatibility shim: run `src.apply_llm_suggestions` as a script.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("src.apply_llm_suggestions", run_name="__main__")
