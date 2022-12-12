from manim import *
import numpy as np

# Seed chosen by unfair coinflip because I don't have dice handy.
rng = np.random.default_rng(0)

class CreateBallTree(Scene):
    def construct(self):
        global dots
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
        #self.play(Create(plane))
        #self.play(*[Create(d) for d in dots.values()])
        self.add(plane)
        self.add(*dots.values())

        _, anims = create_ball_tree(points)
        for anim in anims:
            self.play(anim)
        self.wait()

def get_dot(point):
    global dots
    return dots[tuple(point)]

def highlight(points, color=BLUE, scale=2):
    highlights = []
    for point in points:
        dot = get_dot(point)
        anim = dot.animate.scale(scale).set_color(color)

        highlights.append(anim)
    return AnimationGroup(*highlights)

def unhighlight(points):
    return highlight(points, color=GREY, scale=0.8)


def find_bounds(points, anims):
    # FIND BOUNDS/CENTROID OF POINTS

    # Todo: animate lines from points to centroid, centroid
    # fadin+transform to bound
    centroid = points.mean(axis=0)
    radius = max(np.linalg.norm(centroid-points, axis=1))
    circle = Circle(radius=radius, arc_center=centroid, color=WHITE)
    anims.append(GrowFromCenter(circle))

    return circle, centroid, radius

def find_spreadline(points, anims, circle, ):
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

    return line, angle

def find_median(points, anims, centroid, spreadAngle):
    # FIND MEDIAN POINT ALONG LINE
    #diff = A-B
    #unit_vector = np.array(diff / np.linalg.norm(diff))
    unit_vector = np.array([np.cos(spreadAngle), np.sin(spreadAngle), 0])
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

    def recurse_points(projected):
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
            return recurse_points(projected[1:-1])
    median = recurse_points(projected)

    median_index = list(map(tuple, projected)).index(tuple(median))
    left_projected = set(map(tuple, projected[:median_index]))
    right_projected = set(map(tuple, projected[median_index:]))

    left_points = []
    right_points = []
    for point in points:
        projected_point = tuple((np.dot(point-centroid, unit_vector)*unit_vector)+centroid)
        if projected_point in left_projected:
            left_points.append(point)
        elif projected_point in right_projected:
            right_points.append(point)
        else:
            assert 0, "Projected point not found!"

    return median, left_points, right_points, list(projected_dots.values())

def bisect_points(anims, left_points, right_points, median, spreadAngle, radius):
    unit_vector = np.array([np.cos(spreadAngle+(PI/2)),
                            np.sin(spreadAngle+(PI/2)), 0])
    vector = unit_vector*radius
    line = Line(median+vector, median-vector)

    highlightL = highlight(left_points, color=BLUE)
    highlightR = highlight(right_points, color=GREEN)

    anims.append(AnimationGroup(GrowFromCenter(line),
                                highlightL,
                                highlightR))

    return line

def create_ball_tree(points, anims = []):
    if points.shape[0] == 1:
        return

    circle, centroid, radius = find_bounds(points, anims)

    if points.shape[0] < 3:
        return

    spreadLine, spreadAngle = find_spreadline(points, anims, circle)

    median, left, right, projected_dots = \
        find_median(points, anims, centroid, spreadAngle)

    bisectionLine = bisect_points(anims, left, right,
                                  median, spreadAngle, radius)

    shrinklines = [ShrinkToCenter(spreadLine),
                   ShrinkToCenter(bisectionLine)]
    shrinkdots = [ShrinkToCenter(dot) for dot in projected_dots]
    anims.append(AnimationGroup(*shrinklines,
                                *shrinkdots,
                                unhighlight(points)))

    # RECURSE FOR EACH SIDE?
    create_ball_tree(np.array(left))
    create_ball_tree(np.array(right))

    return None, anims
