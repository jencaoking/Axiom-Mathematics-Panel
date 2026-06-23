import sys
import os

print("Testing CsComplexEngine...")
from mathlab.core.cs_complex_engine import cs_complex

print("Engine initialized. Generating Mandelbrot...")
# 1920x1080 resolution
img = cs_complex.generate_mandelbrot_image(-2.5, 1.0, -1.0, 1.0, 1920, 1080, 256)

print(f"Image generated! Shape: {img.shape}, dtype: {img.dtype}")
print(f"Sample pixel [540, 960]: {img[540, 960]}")
print("Test successful!")
