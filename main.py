from manim import *
import numpy as np

# Seed chosen by unfair coinflip because I don't have dice handy.
rng = np.random.default_rng(2)

class CreateBallTree(Scene):
    def construct(self):
        plane = NumberPlane()

        # Generate 3d points then mask the 3rd dimension so it doesn't mess up our calculations
        var = 2
        points3 = rng.multivariate_normal([0,0,0],
                                          var*np.identity(3),
                                          size=10)
        points = points3
        points[:,-1] = 0
        points = points

        dots = {tuple(p): Dot(p, color=GREY, radius=0.05) for p in points}
        self.play(Create(plane))
        self.play(*[Create(d) for d in dots.values()])

        def get_dot(point):
            return dots[tuple(point)]

        def highlight(points, color=BLUE, scale=2):
            highlights = []
            for point in points:
                dot = get_dot(point)
                anim = dot.animate.scale(scale).set_color(color)

                highlights.append(anim)
            return AnimationGroup(*highlights)

        def unhighlight(points):
            return highlight(points, color=GREY, scale=0.5)

        def create_ball_tree(points):
            # FIND BOUNDS/CENTROID OF POINTS

            # Todo: animate lines from points to centroid, centroid
            # fadin+transform to bound
            anims = []
            centroid = points.mean(axis=0)
            radius = max(np.linalg.norm(centroid-points, axis=1))
            circle = Circle(radius=radius, arc_center=centroid, color=WHITE)
            anims.append(FadeIn(circle))

            # APPROXIMATE DIMENSION OF GREATEST SPREAD

            # Pick any random point
            point = rng.choice(points)
            anims.append(Indicate(get_dot(point), color=YELLOW))

            # Find the furthest point from that
            dists = np.linalg.norm(point-points, axis=1)
            A = points[np.argmax(dists)]
            anims.append(ShowPassingFlash(Line(point, A)))

            # Find the furthest point from that
            dists = np.linalg.norm(A-points, axis=1)
            B = points[np.argmax(dists)]
            anims.append(ShowPassingFlash(Line(A, B)))

            # This line is a pretty good approximation of the line of greatest spread.
            line = Line(B, A)
            anims.append(Create(line))

            # Transform that line such that it intersects the centroid
            # and spans the bounding circle.
            #
            # This was wrong: https://www.rollpie.com/post/310
            def get_angle(A, B):
                diff = A-B
                mag = np.linalg.norm(diff)
                if mag == 0:
                    return 0

                unit_diff = diff / mag
                cos = unit_diff[0]
                return  np.arccos(cos)
            angle = get_angle(A, B)
            A = circle.point_at_angle(angle)
            B = circle.point_at_angle(angle+PI)
            line2 = Line(B, A)
            # THIS LINE RIGHT HERE
            anims.append(ReplacementTransform(line, line2))

            # FIND MEDIAN POINT ALONG LINE
            diff = A-B
            unit_vector = np.array([diff / np.linalg.norm(diff)])
            print(unit_vector.shape, points.shape)
            projected = np.inner(points, unit_vector) * unit_vector

            # DIVIDE POINTS BY WHICH SIDE OF MEDIAN

            # RECURSE FOR EACH SIDE?

            return None, Succession(*anims)

        self.play(create_ball_tree(points)[1])
        self.wait()
