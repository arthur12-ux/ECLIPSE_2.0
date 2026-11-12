"""Compatibility shim: run `src.esms_llm_metadata` as a script.

This file keeps the original CLI name working after moving the real
implementation into `src/`.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("src.esms_llm_metadata", run_name="__main__")
