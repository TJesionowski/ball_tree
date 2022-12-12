from manim import *
import numpy as np

# Seed chosen by unfair coinflip because I don't have dice handy.
rng = np.random.default_rng(0)

class CreateBallTree(Scene):
    def construct(self):
        plane = NumberPlane()

        # Generate points in a normal distribution squished to the
        # correct aspect ratio.
        cov = np.array([
            [16.0, 0.0, 0.0],
            [0.0,  9.0, 0.0],
            [0.0,  0.0, 0.0]
        ])
        cov /= np.linalg.norm(cov)
        points = rng.multivariate_normal([0,0,0],
                                         cov,
                                         size=10)

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
            anims.append(GrowFromCenter(circle))

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
                diff = B-A
                mag = np.linalg.norm(diff)
                if mag == 0:
                    return 0

                unit_diff = diff / mag
                cos = unit_diff[0]
                sin = unit_diff[1]
                if cos == 0 and sin == 1:
                    return np.deg2rad(90)
                elif cos == 0 and sin == -1:
                    return np.deg2rad(-90)
                elif cos != 0:
                    return  np.arctan(sin / cos)
                else:
                    print(sin, cos)
                    raise RuntimeError()
            assert np.rad2deg(get_angle(ORIGIN[:-1], np.array([1,0]))) == 0
            assert np.rad2deg(get_angle(ORIGIN[:-1], np.array([1,1]))) == 45
            assert np.rad2deg(get_angle(ORIGIN[:-1], np.array([0,1]))) == 90

            angle = get_angle(A, B)
            a = circle.point_at_angle(angle)
            b = circle.point_at_angle(angle+PI)
            if np.linalg.norm(A-a) > np.linalg.norm(A-b):
                A=a
                B=b
            else:
                A=b
                B=a

            anims.append(line.animate.put_start_and_end_on(A, B))

            # FIND MEDIAN POINT ALONG LINE
            diff = A-B
            unit_vector = np.array(diff / np.linalg.norm(diff))
            projected = [np.dot(p, unit_vector)*unit_vector for p in points-centroid]
            projected = np.array(projected)+centroid

            projection = []
            for point, proj in zip(points, projected):
                projection_line = Line(point, proj)
                projection.append(Succession(Create(projection_line),
                                             FadeOut(projection_line)))
            projected_dots = {tuple(p): Dot(p) for p in projected}
            projection += [GrowFromCenter(d) for d in projected_dots.values()]
            anims.append(AnimationGroup(*projection))

            # Working in centroid-space for a second...
            projected -= centroid
            furthest = projected[np.argmax(np.linalg.norm(projected, axis=1))]
            # https://stackoverflow.com/a/40984689
            projected = projected[np.argsort(np.linalg.norm(furthest-projected,
                                                            axis=1))]
            projected += centroid

            def find_median(projected):
                if len(projected) == 1:
                    anims.append(Flash(projected_dots[tuple(projected[0])]))
                    return projected[0]
                elif len(projected) == 2:
                    a = Flash(projected_dots[tuple(projected[0])])
                    b = Indicate(projected_dots[tuple(projected[1])])
                    anims.append(AnimationGroup(a, b))
                    return projected[0]
                else:
                    a = Indicate(projected_dots[tuple(projected[0])])
                    b = Indicate(projected_dots[tuple(projected[-1])])
                    anims.append(AnimationGroup(a, b))
                    return find_median(projected[1:-1])
            median = find_median(projected)

            # This SHOULD work but doesn't?
            rotate_line = line.animate\
                              .rotate(90,
                                      about_point=centroid)
            shift_line = line.animate\
                             .move_to(median)
            anims.append(AnimationGroup(rotate_line, shift_line))
            print(locals().keys())

            # DIVIDE POINTS BY WHICH SIDE OF MEDIAN

            # RECURSE FOR EACH SIDE?

            return None, anims

        _, anims = create_ball_tree(points)
        for anim in anims:
            self.play(anim)
        self.wait()
