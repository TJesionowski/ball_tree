from manim import *
import numpy as np

# Seed chosen by unfair coinflip because I don't have dice handy.
rng = np.random.default_rng(0)
assert rng.bytes(8).hex() == "5f82c2d9cfeb0fa3"

class CreateBallTree(Scene):
    def construct(self):
        plane = NumberPlane()

        # Generate 3d points then mask the 3rd dimension so it doesn't mess up our calculations
        var=4
        points3 = rng.multivariate_normal([0,0,0],
                                          var*np.identity(3),
                                          size=10)
        points = points3
        points[:,-1] = 0
        points = points

        dots = [Dot(p) for p in points]
        self.add(plane, *dots)

        centroid = points.mean(axis=0)
        radius = max(np.linalg.norm(centroid-points, axis=1))
        self.play(Create(Circle(radius=radius, arc_center=centroid)))

        self.wait()
