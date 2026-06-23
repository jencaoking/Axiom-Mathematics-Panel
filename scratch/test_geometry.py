import sys
print("Start")
import mathlab.core.cs_geometry_engine as cs_geom
print("Imported cs_geometry_engine")
print("Engine available:", cs_geom.cs_geometry.is_available)

if cs_geom.cs_geometry.is_available:
    print("Testing LineLine")
    res1 = cs_geom.cs_geometry.solve_line_line(1, -1, 0, 1, 1, -2) # y=x, y=-x+2 => (1,1)
    print("LineLine:", res1)
    
    print("Testing LineCircle")
    res2 = cs_geom.cs_geometry.solve_line_circle(1, 0, 0, 0, 0, 1) # x=0, x^2+y^2=1 => (0,1), (0,-1)
    print("LineCircle:", res2)
    
    print("Testing Conic")
    res3 = cs_geom.cs_geometry.generate_conic_points(1, 0, 1, 0, 0, -1, (-1, 1), (-1, 1), 10)
    print("Conic:", res3)
    
print("Done")
