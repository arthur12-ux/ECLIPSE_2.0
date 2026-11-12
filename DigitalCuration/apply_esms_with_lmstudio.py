"""Compatibility shim: run `src.apply_esms_with_lmstudio` as a script.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("src.apply_esms_with_lmstudio", run_name="__main__")
