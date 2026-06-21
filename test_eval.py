import sys
sys.path.append(".")
from mathlab.core.octave_bridge import OctaveBridge

bridge = OctaveBridge()
print("1+1 =", bridge.evaluate("1+1"))
print("type(1) =", bridge.evaluate("type(1)"))
