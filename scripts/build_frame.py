"""IH rat rod - frame, rear leaf-spring suspension, front torsion-bar suspension.

Builds one FreeCAD document ("IH_frame", saved to models/IH frame.FCStd) in the
same world coordinates as the IH rat rod assembly:

    X = across the car (+X is the left side)      Y = rearward (front axle at ~-22, rear axle at ~2773)
    Z = up (ground plane is Z = -404.2)           all dimensions in mm

Run it inside FreeCAD (the IH rat rod assembly should be open so the axle
positions can be read from it; otherwise the fallbacks below are used):

    exec(open('/home/sfeldma/Work/IH rat rod/scripts/build_frame.py').read())

Change the numbers in the PARAMETERS section and re-run to regenerate.
"""
import math
import FreeCAD
import Part
from FreeCAD import Vector as V, Rotation, Placement

IN = 25.4
EX, EY, EZ = V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)
OUT_PATH = '/home/sfeldma/Work/IH rat rod/models/IH frame.FCStd'

# --------------------------------------------------------------------------
# PARAMETERS
# --------------------------------------------------------------------------
# Rails: C4x5.4 (4" web, 1.584" flange, 0.184" web, 0.296" flange), open side INWARD
RAIL_D, RAIL_BF, RAIL_TW, RAIL_TF = 4 * IN, 1.584 * IN, 0.184 * IN, 0.296 * IN
# Crossmembers: C3x4.1, open side rearward
CM_D, CM_BF, CM_TW, CM_TF = 3 * IN, 1.410 * IN, 0.170 * IN, 0.273 * IN
TP = 0.25 * IN                      # thickness of gusset / mounting plates (1/4")

# Rail layout (centerline of each rail)
X_C_FRONT = 10.0 * IN               # 20" between rail centerlines up front
X_C_REAR = 495.3                    # = rear axle spring-perch X (39.0" between perches)
Z_F = 12.0                          # rail centerline height, front section
Z_R = 225.0                         # rail centerline height, rear (kicked-up) section
Y_RAIL_FRONT, Y_RAIL_END = -420.0, 3550.0
Y_JOG0, Y_JOG1 = 1450.0, 1700.0     # abrupt step from 20" to 39" wide
Y_KICK0, Y_KICK1 = 1750.0, 2150.0   # kick-up over the rear axle

CM_YS = [-340.0, 200.0, 900.0, 1350.0, 2400.0, None, 3450.0]   # None -> rear axle Y

# Rivets: 3/8"
RIV_R, HOLE_R = 0.375 * IN / 2, 0.405 * IN / 2
HEAD_R, HEAD_R2, HEAD_H = 7.95, 5.5, 6.35
TAIL_R, TAIL_H = 6.35, 3.2

# Rear leaf springs (over the axle, 42" eye to eye, 5 leaves 2" x 1/4")
SPRING_W, LEAF_T = 2 * IN, 0.25 * IN
LEAF_HALF = [228.6, 304.8, 381.0, 457.2, 533.4]     # half lengths, short -> long
LEAF_RB = 4842.0                                    # arch radius of bottom leaf underside
PAD_TOP_Z = 50.8                                    # top of spring pad on the axle
AXLE_TUBE_HALF = 35.4

# Front torsion suspension
BAR_R = 0.5 * IN                    # 1" torsion bar
EYE_R = 18.9                        # torsion-arm eye: bushing outer radius (11 mm bushing wall on the 5/8" pin)
ARM_BOSS_R = EYE_R + 6.1            # round boss around the eye at the arm tip
BAR_REAR_Y = 590.0
PERCH_X = 345.0                     # the axle's original spring perch (stud), re-measured from the axle
SHOCK_AX_X, SHOCK_AX_Z = 596.5, -28.5   # the axle's original shock-mount holes (re-measured from the axle)
LADDER_FRAME_Y, LADDER_AXLE_Y = 760.0, 40.0
LADDER_FR_X = 350.0                 # ladder frame pivot, outboard of the torsion bar (bar is at |x| = 304)

# --------------------------------------------------------------------------
# measured / fallback values from the assembly
# --------------------------------------------------------------------------
try:
    _asm = FreeCAD.getDocument('IH_rat_rod')
except Exception:
    _asm = None
try:
    Y_REAR_AXLE = _asm.getObject('Body003').Placement.Base.y
except Exception:
    Y_REAR_AXLE = 2773.317
try:
    _fa = _asm.getObject('Body').Shape
    _c = _fa.common(Part.makeBox(10, 400, 1000, V(-5, -200, -500)))
    FA_Y0, FA_Y1 = _c.BoundBox.YMin, _c.BoundBox.YMax
    Y_FA = (FA_Y0 + FA_Y1) / 2.0
except Exception:
    _fa = None
    Y_FA, FA_Y0, FA_Y1 = -22.2, -44.4, 0.0

def axle_top(x):
    """Z of the top of the front axle beam at |x| (live from the assembly)."""
    try:
        c = _fa.common(Part.makeBox(10, 400, 1000, V(abs(x) - 5, -200, -500)))
        return c.BoundBox.ZMax
    except Exception:
        return -169.5

try:                                    # find the spring-perch stud and the shock-mount hole on the real axle
    for _f in _fa.Faces:
        _sf, _b = _f.Surface, _f.BoundBox
        if _sf.__class__.__name__ != 'Cylinder' or _b.XMin < 0:
            continue
        if abs(_sf.Axis.z) > 0.99 and abs(_sf.Radius - 6.3) < 0.3:
            PERCH_X = (_b.XMin + _b.XMax) / 2.0
        elif abs(_sf.Axis.y) > 0.99 and abs(_sf.Radius - 9.5) < 0.2 and _f.Area > 2000:
            SHOCK_AX_X, SHOCK_AX_Z = (_b.XMin + _b.XMax) / 2.0, (_b.ZMin + _b.ZMax) / 2.0
except Exception:
    pass

BAR_Z = SHOCK_AX_Z                  # torsion bars and arms level with the axle-end pin (arms horizontal)
LADDER_Z = SHOCK_AX_Z               # ladder bars horizontal at the same height (no roll lock)

CM_YS = [Y_REAR_AXLE if y is None else y for y in CM_YS]

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
PARTS, HOLES, RIVETS, GROUP_ORDER = {}, {}, {}, []

def add(key, shape, label, group, rgb=None):
    PARTS[key] = dict(shape=shape, label=label, group=group, rgb=rgb)
    if group not in GROUP_ORDER:
        GROUP_ORDER.append(group)

def cylc(c, axis, r, length):
    """Cylinder of radius r and given length, centered on point c, along axis."""
    a = V(axis); a.normalize()
    return Part.makeCylinder(r, length, c - a * (length / 2.0), a)

def cyl2(p0, p1, r):
    d = p1 - p0
    return Part.makeCylinder(r, d.Length, p0, d)

def boxr(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def prism(pts, vec):
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(vec)

def fuse_all(shapes):
    s = shapes[0]
    for o in shapes[1:]:
        s = s.fuse(o)
    try:                                   # tidy up, but only keep the result if no volume was lost
        v0 = s.Volume
        r = s.copy().removeSplitter()
        if not r.isNull() and r.isValid() and abs(r.Volume - v0) < 1e-4 * v0:
            s = r
    except Exception:
        pass
    return s

def drill(key, c, axis, r, length):
    HOLES.setdefault(key, []).append(cylc(c, axis, r, length))

def joint(origin, axis, grip, group, keys):
    """3/8" rivet: head at `origin`, shank runs along `axis` through `grip`; drills the parts in `keys`."""
    a = V(axis); a.normalize()
    hole = Part.makeCylinder(HOLE_R, grip + 1.0, origin - a * 0.5, a)
    for k in keys:
        HOLES.setdefault(k, []).append(hole)
    RIVETS.setdefault(group, []).extend([
        Part.makeCylinder(RIV_R, grip, origin, a),
        Part.makeCone(HEAD_R, HEAD_R2, HEAD_H, origin, a * -1),
        Part.makeCylinder(TAIL_R, TAIL_H, origin + a * grip, a)])

# --------------------------------------------------------------------------
# frame rails: mitred sweep of a C-channel along a poly-line centerline
# --------------------------------------------------------------------------
def c_points(c, up, inward, D, BF, TW, TF):
    def pt(t, b):
        return c + inward * (-BF / 2.0 + t) + up * b
    h = D / 2.0
    return [pt(0, -h), pt(BF, -h), pt(BF, -h + TF), pt(TW, -h + TF),
            pt(TW, h - TF), pt(BF, h - TF), pt(BF, h), pt(0, h)]

def segment(P0, P1, side, ext0, ext1):
    d = P1 - P0
    L = d.Length
    d.normalize()
    up = EZ - d * EZ.dot(d)
    up.normalize()
    lat = d.cross(up)
    inward = lat if lat.x * side < 0 else lat * -1
    pts = c_points(P0 - d * ext0, up, inward, RAIL_D, RAIL_BF, RAIL_TW, RAIL_TF)
    return prism(pts, d * (L + ext0 + ext1))

def mitre_box(J, n, remove_positive):
    big = 3000.0
    b = Part.makeBox(big, 2 * big, 2 * big, V(0, -big, -big))
    b.Placement = Placement(J, Rotation(EX, n if remove_positive else n * -1))
    return b

def rail_path(side):
    xf, xr = side * X_C_FRONT, side * X_C_REAR
    return [V(xf, Y_RAIL_FRONT, Z_F), V(xf, Y_JOG0, Z_F), V(xr, Y_JOG1, Z_F),
            V(xr, Y_KICK0, Z_F), V(xr, Y_KICK1, Z_R), V(xr, Y_RAIL_END, Z_R)]

def build_rail(side):
    path = rail_path(side)
    n = len(path) - 1
    segs = [segment(path[i], path[i + 1], side, 300.0 if i > 0 else 0.0,
                    300.0 if i < n - 1 else 0.0) for i in range(n)]
    for i in range(1, n):
        d0 = path[i] - path[i - 1]; d0.normalize()
        d1 = path[i + 1] - path[i]; d1.normalize()
        nv = d0 + d1; nv.normalize()
        segs[i - 1] = segs[i - 1].cut(mitre_box(path[i], nv, True))
        segs[i] = segs[i].cut(mitre_box(path[i], nv, False))
    return fuse_all(segs)

# rail section helpers (valid on the flat sections), for the LEFT rail with centerline x = xc
def x_wo(xc):  return xc + RAIL_BF / 2.0                 # web outer face
def x_wi(xc):  return xc + RAIL_BF / 2.0 - RAIL_TW       # web inner face

SIDES = {'L': +1, 'R': -1}
GREY_RAIL, GREY_CM = (0.33, 0.34, 0.37), (0.45, 0.46, 0.5)
DARK, STEEL, RED = (0.2, 0.2, 0.22), (0.55, 0.57, 0.6), (0.6, 0.25, 0.2)
NAME = {'L': 'left', 'R': 'right'}

for sk, s in SIDES.items():
    add('rail_' + sk, build_rail(s), 'Frame rail - ' + NAME[sk], 'Rails', GREY_RAIL)

# --------------------------------------------------------------------------
# crossmembers (C3, end plates nest in the rail channel and are riveted to the rail web)
# --------------------------------------------------------------------------
def rail_z_at(y):
    return Z_R if y >= Y_KICK1 else Z_F

def rail_xc_at(y):
    return X_C_REAR if y >= Y_JOG1 else X_C_FRONT

for i, ycm in enumerate(CM_YS, 1):
    xc, zc = rail_xc_at(ycm), rail_z_at(ycm)
    plate_in = x_wi(xc) - TP
    half = plate_in + 3.0
    h = CM_D / 2.0
    y0, y1 = ycm - CM_TW / 2.0, ycm + CM_TW / 2.0
    yf = ycm - CM_TW / 2.0 + CM_BF
    pts = [V(-half, y0, zc - h), V(-half, yf, zc - h), V(-half, yf, zc - h + CM_TF),
           V(-half, y1, zc - h + CM_TF), V(-half, y1, zc + h - CM_TF), V(-half, yf, zc + h - CM_TF),
           V(-half, yf, zc + h), V(-half, y0, zc + h)]
    shapes = [prism(pts, V(2 * half, 0, 0))]
    for s in (+1, -1):
        xa, xb = sorted((s * plate_in, s * x_wi(xc)))
        shapes.append(boxr(xa, xb, ycm - 50, ycm + 50, zc - h, zc + h))
    key = 'cm%d' % i
    add(key, fuse_all(shapes), 'Crossmember %d (Y=%d)' % (i, round(ycm)), 'Crossmembers', GREY_CM)
    for sk, s in SIDES.items():
        for dy in (-30.0, 30.0):
            for dz in (-20.0, 20.0):
                joint(V(s * x_wo(xc), ycm + dy, zc + dz), V(-s, 0, 0), RAIL_TW + TP,
                      'Rivets - crossmembers', ['rail_' + sk, key])

# --------------------------------------------------------------------------
# rear leaf springs, U-bolts, hangers, shackles
# --------------------------------------------------------------------------
YC = Y_REAR_AXLE
ZC_ARC = PAD_TOP_Z - LEAF_RB                           # center of the leaf arcs (far below the spring)

def leaf(xc, i, half_len):
    r_in = LEAF_RB + LEAF_T * i
    r_out = r_in + LEAF_T
    th = half_len / (r_in + LEAF_T / 2.0)
    x0 = xc - SPRING_W / 2.0
    def P(phi, r):
        return V(x0, YC + r * math.sin(phi), ZC_ARC + r * math.cos(phi))
    edges = Part.__sortEdges__([
        Part.Arc(P(-th, r_in), P(0, r_in), P(th, r_in)).toShape(),
        Part.makeLine(P(th, r_in), P(th, r_out)),
        Part.Arc(P(th, r_out), P(0, r_out), P(-th, r_out)).toShape(),
        Part.makeLine(P(-th, r_out), P(-th, r_in))])
    return Part.Face(Part.Wire(edges)).extrude(V(SPRING_W, 0, 0))

R_MID_MAIN = LEAF_RB + LEAF_T * 4.5
TH_MAIN = LEAF_HALF[-1] / R_MID_MAIN
EYE_DY = R_MID_MAIN * math.sin(TH_MAIN)
EYE_Z = ZC_ARC + R_MID_MAIN * math.cos(TH_MAIN)
Y_EYE_F, Y_EYE_R = YC - EYE_DY, YC + EYE_DY
SHACKLE_UP_DY, SHACKLE_UP_Z = -36.0, 145.0             # upper shackle pin relative to the rear eye

def build_spring(xc):
    x0 = xc - SPRING_W / 2.0
    leaves = []
    for i, hl in enumerate(LEAF_HALF):
        L = leaf(xc, i, hl)
        if i == len(LEAF_HALF) - 1:
            for ey in (Y_EYE_F, Y_EYE_R):
                L = L.fuse(Part.makeCylinder(20.65, SPRING_W, V(x0, ey, EYE_Z), EX))
            for ey in (Y_EYE_F, Y_EYE_R):
                L = L.cut(Part.makeCylinder(14.3, SPRING_W, V(x0, ey, EYE_Z), EX))
        leaves.append(L)
    for ey in (Y_EYE_F, Y_EYE_R):                      # eye bushings
        leaves.append(Part.makeCylinder(14.3, SPRING_W, V(x0, ey, EYE_Z), EX).cut(
            Part.makeCylinder(8.0, SPRING_W, V(x0, ey, EYE_Z), EX)))
    leaves.append(Part.makeCylinder(4.76, 5 * LEAF_T + 6.35, V(xc, YC, PAD_TOP_Z), EZ))               # center bolt
    leaves.append(Part.makeCylinder(8.0, 6.0, V(xc, YC, PAD_TOP_Z + 5 * LEAF_T + 6.35), EZ))          # bolt head
    return Part.makeCompound(leaves)

def build_ubolts(xc):
    top_z = PAD_TOP_Z + 5 * LEAF_T                     # top of the pack at the axle
    pl = 38.1
    bot = -AXLE_TUBE_HALF - 6.35
    parts = [boxr(xc - pl, xc + pl, YC - 57.15, YC + 57.15, top_z, top_z + 6.35),                  # top plate
             boxr(xc - pl, xc + pl, YC - 57.15, YC + 57.15, bot, -AXLE_TUBE_HALF)]                 # bottom plate
    zr = top_z + 6.35 + 6.35
    for dy in (-44.5, 44.5):
        parts.append(cyl2(V(xc - 32.4, YC + dy, zr), V(xc + 32.4, YC + dy, zr), 6.35))             # U-bolt bend
        for dx in (-32.4, 32.4):
            parts.append(cyl2(V(xc + dx, YC + dy, zr), V(xc + dx, YC + dy, bot - 22), 6.35))
            parts.append(Part.makeCylinder(11.0, 10.0, V(xc + dx, YC + dy, bot - 10), EZ))         # nut
    return Part.makeCompound(parts)

Z_RAIL_BOT_R = Z_R - RAIL_D / 2.0                      # underside of the rear rail
Z_TOPPLATE = Z_RAIL_BOT_R - TP                          # underside of hanger top plates

def side_plate_yz(xa, xb, pts_yz):
    return prism([V(xa, y, z) for y, z in pts_yz], V(xb - xa, 0, 0))

for sk, s in SIDES.items():
    xc = s * X_C_REAR
    nm = NAME[sk]
    add('spring_' + sk, build_spring(xc), 'Leaf spring - ' + nm, 'Rear suspension', DARK)
    add('ubolts_' + sk, build_ubolts(xc), 'U-bolts and plates - ' + nm, 'Rear suspension', STEEL)

    # fixed front hanger: inverted-U bracket straddling the spring, riveted to the rail's bottom flange
    gap = 26.4
    pa = sorted((xc - gap - TP, xc - gap))
    pb = sorted((xc + gap, xc + gap + TP))
    yh = Y_EYE_F
    topp = boxr(pa[0], pb[1], yh - 60, yh + 60, Z_TOPPLATE, Z_RAIL_BOT_R)
    sp = [(yh - 55, Z_TOPPLATE), (yh + 55, Z_TOPPLATE), (yh + 26, EYE_Z - 24), (yh - 26, EYE_Z - 24)]
    key = 'fhanger_' + sk
    add(key, fuse_all([topp, side_plate_yz(pa[0], pa[1], sp), side_plate_yz(pb[0], pb[1], sp)]),
        'Front spring hanger - ' + nm, 'Rear suspension', RED)
    drill(key, V(xc, yh, EYE_Z), EX, 8.0, 120)
    for dx in (-8.0, 8.0):
        for dy in (-35.0, 35.0):
            joint(V(xc + dx, yh + dy, Z_TOPPLATE), EZ, TP + RAIL_TF, 'Rivets - spring hangers', ['rail_' + sk, key])
    add('fpin_' + sk, Part.makeCompound([cylc(V(xc, yh, EYE_Z), EX, 7.9, 2 * (gap + TP) + 4),
                                         cylc(V(xc - (gap + TP + 5), yh, EYE_Z), EX, 12.7, 8),
                                         cylc(V(xc + (gap + TP + 5), yh, EYE_Z), EX, 12.7, 8)]),
        'Front spring pin - ' + nm, 'Rear suspension', STEEL)

    # rear shackle: two plates outside the spring eye, hanger bracket outside the shackle
    sg = 25.9
    sa = sorted((xc - sg - TP, xc - sg))
    sb = sorted((xc + sg, xc + sg + TP))
    p_low = (Y_EYE_R, EYE_Z)
    p_up = (Y_EYE_R + SHACKLE_UP_DY, SHACKLE_UP_Z)
    dvec = (p_up[0] - p_low[0], p_up[1] - p_low[1])
    ln = math.hypot(*dvec)
    nrm = (-dvec[1] / ln * 15.9, dvec[0] / ln * 15.9)
    quad = [(p_low[0] + nrm[0], p_low[1] + nrm[1]), (p_up[0] + nrm[0], p_up[1] + nrm[1]),
            (p_up[0] - nrm[0], p_up[1] - nrm[1]), (p_low[0] - nrm[0], p_low[1] - nrm[1])]
    key = 'shackle_' + sk
    add(key, Part.makeCompound([side_plate_yz(sa[0], sa[1], quad), side_plate_yz(sb[0], sb[1], quad)]),
        'Rear shackle - ' + nm, 'Rear suspension', STEEL)
    for p in (p_low, p_up):
        drill(key, V(xc, p[0], p[1]), EX, 8.0, 120)
    ha = sorted((xc - sg - TP - 0.5 - TP, xc - sg - TP - 0.5))
    hb = sorted((xc + sg + TP + 0.5, xc + sg + TP + 0.5 + TP))
    yu = p_up[0]
    topp = boxr(ha[0], hb[1], yu - 45, yu + 45, Z_TOPPLATE, Z_RAIL_BOT_R)
    sp = [(yu - 45, Z_TOPPLATE), (yu + 45, Z_TOPPLATE), (yu + 22, p_up[1] - 22), (yu - 22, p_up[1] - 22)]
    key = 'shhanger_' + sk
    add(key, fuse_all([topp, side_plate_yz(ha[0], ha[1], sp), side_plate_yz(hb[0], hb[1], sp)]),
        'Shackle hanger - ' + nm, 'Rear suspension', RED)
    drill(key, V(xc, p_up[0], p_up[1]), EX, 8.0, 120)
    for dx in (-8.0, 8.0):
        for dy in (-30.0, 30.0):
            joint(V(xc + dx, yu + dy, Z_TOPPLATE), EZ, TP + RAIL_TF, 'Rivets - spring hangers', ['rail_' + sk, key])
    span = 2 * (sg + TP + 0.5 + TP + 5)
    add('spins_' + sk, Part.makeCompound([
        cylc(V(xc, p_low[0], p_low[1]), EX, 7.9, 2 * (sg + TP) + 10),
        cylc(V(xc, p_up[0], p_up[1]), EX, 7.9, span),
        cylc(V(xc - span / 2.0, p_up[0], p_up[1]), EX, 12.7, 8), cylc(V(xc + span / 2.0, p_up[0], p_up[1]), EX, 12.7, 8),
        cylc(V(xc - (sg + TP + 5), p_low[0], p_low[1]), EX, 12.7, 8),
        cylc(V(xc + (sg + TP + 5), p_low[0], p_low[1]), EX, 12.7, 8)]),
        'Shackle pins - ' + nm, 'Rear suspension', STEEL)

# --------------------------------------------------------------------------
# front torsion-bar suspension
# --------------------------------------------------------------------------
def support_block(yc, xb, s, key, label):
    """Bar support: plate on the outside of the rail web + boss with a bar bore."""
    xc = X_C_FRONT
    xwo = x_wo(xc)
    xa, xb2 = sorted((s * xwo, s * (xwo + TP)))
    plate = boxr(xa, xb2, yc - 45, yc + 45, Z_F - 38.1, Z_F + 38.1)
    xs = sorted((s * (xwo + TP), xb + s * 20.0))
    boss = boxr(xs[0], xs[1], yc - 45, yc + 45, BAR_Z - 20.0, BAR_Z + 20.0)
    shp = fuse_all([plate, boss]).cut(cylc(V(xb, yc, BAR_Z), EY, BAR_R + 0.3, 120))
    add(key, shp, label, 'Front suspension', RED)
    for dy in (-30.0, 30.0):
        for dz in (32.0, 50.0):                          # above the boss, inside the web
            joint(V(s * (xwo + TP), yc + dy, BAR_Z + dz), V(-s, 0, 0), RAIL_TW + TP, 'Rivets - front suspension',
                  ['rail_' + ('L' if s > 0 else 'R'), key])

for sk, s in SIDES.items():
    nm = NAME[sk]
    xc = s * X_C_FRONT
    xb = s * (x_wo(X_C_FRONT) + 30.0)                   # torsion bar axis: outside the rail, 30 mm out from the web

    # torsion bar
    y_front = Y_FA - 34.0
    add('tbar_' + sk, Part.makeCylinder(BAR_R, BAR_REAR_Y - y_front, V(xb, y_front, BAR_Z), EY),
        'Torsion bar - ' + nm, 'Front suspension', STEEL)
    support_block(110.0, xb, s, 'tfront_' + sk, 'Torsion bar front support - ' + nm)
    support_block(BAR_REAR_Y - 25.0, xb, s, 'trear_' + sk, 'Torsion bar rear anchor - ' + nm)

    # twin-plate torsion arm: runs outboard from the bar, level with the axle-end pin, and straddles the axle end.
    # The eye is bushed (the bushing shears to take the sideways shift as the axle moves).
    xt, zt = s * SHOCK_AX_X, SHOCK_AX_Z
    bore = cylc(V(xb, Y_FA, BAR_Z), EY, BAR_R, 120)          # bore each piece separately (a cut after the fuse is invalid)
    tip = cylc(V(xt, Y_FA, zt), EY, EYE_R, 120)
    plates, bush = [], []
    for ya, yb in ((FA_Y0 - 10.0, FA_Y0 - 0.5), (FA_Y1 + 0.5, FA_Y1 + 10.0)):
        pts = [V(xb, ya, BAR_Z + 23.0), V(xt, ya, zt + 16.0), V(xt, ya, zt - 16.0), V(xb, ya, BAR_Z - 23.0)]
        pl = prism(pts, V(0, yb - ya, 0)).fuse(Part.makeCylinder(ARM_BOSS_R, yb - ya, V(xt, ya, zt), EY))
        plates.append(pl.cut(bore).cut(tip))
        ring = Part.makeCylinder(EYE_R, yb - ya, V(xt, ya, zt), EY).cut(Part.makeCylinder(7.9, yb - ya, V(xt, ya, zt), EY))
        bush.append(ring)
    hub = Part.makeCylinder(20.0, FA_Y1 - FA_Y0 + 20.0, V(xb, FA_Y0 - 10.0, BAR_Z), EY).cut(bore)
    arm = fuse_all(plates + [hub])
    add('tarm_' + sk, arm, 'Torsion arm - ' + nm, 'Front suspension', RED)
    add('tarmbush_' + sk, Part.makeCompound(bush), 'Torsion arm bushings - ' + nm, 'Front suspension', DARK)

    # shock: from the axle's original shock-mount hole (eye on the front face) up to a tower on the rail
    Y_SH = FA_Y0 - 21.6                                   # shock eye sits outside the arm's front plate
    xu, zu = s * (X_C_FRONT + 90.0), Z_F + 360.0
    L0, U0 = V(s * SHOCK_AX_X, Y_SH, SHOCK_AX_Z), V(xu, Y_SH, zu)
    dd = U0 - L0
    dl = dd.Length
    dn = V(dd); dn.normalize()
    shock = [cylc(L0, EY, 14.3, 22.2), cylc(U0, EY, 14.3, 22.2),
             Part.makeCylinder(6.35, 110.0, L0 + dn * 14.3, dn),
             Part.makeCylinder(15.0, dl - 14.3 - 124.3, L0 + dn * 124.3, dn)]
    add('shock_' + sk, Part.makeCompound(shock), 'Front shock - ' + nm, 'Front suspension', DARK)
    drill('shock_' + sk, L0, EY, 8.0, 60)
    drill('shock_' + sk, U0, EY, 8.0, 60)
    xsp, zsp = s * SHOCK_AX_X, SHOCK_AX_Z
    add('shockpin_' + sk, Part.makeCompound([
        Part.makeCylinder(7.9, 14.0 - (Y_SH - 11.1), V(xsp, Y_SH - 11.1, zsp), EY),
        Part.makeCylinder(12.7, 8.0, V(xsp, Y_SH - 19.1, zsp), EY),
        Part.makeCylinder(11.0, 8.0, V(xsp, FA_Y1 + 10.0, zsp), EY)]),
        'Shock and arm axle pin - ' + nm, 'Front suspension', STEEL)

    zt = Z_F + RAIL_D / 2.0
    xa, xb2 = sorted((xc - 26, xc + 26))
    base = boxr(xa, xb2, Y_SH - 50, Y_SH + 50, zt, zt + TP)
    xua = abs(xu)
    tp = [(s * (X_C_FRONT - 26.0), zt + TP), (s * (X_C_FRONT + 26.0), zt + TP), (s * (xua + 22.0), zu - 30.0),
          (s * (xua + 22.0), zu + 30.0), (s * (xua - 22.0), zu + 30.0)]
    tpl = [prism([V(x_, yc_ - TP / 2.0, z_) for x_, z_ in tp], V(0, TP, 0)) for yc_ in (Y_SH - 19.7, Y_SH + 19.7)]
    key = 'tower_' + sk
    add(key, fuse_all([base] + tpl).cut(cylc(V(xu, Y_SH, zu), EY, 8.0, 120)),
        'Shock tower - ' + nm, 'Front suspension', RED)
    for dx in (-8.0, 8.0):
        for dy in (-36.0, 36.0):
            joint(V(xc + dx, Y_SH + dy, zt + TP), V(0, 0, -1), TP + RAIL_TF, 'Rivets - front suspension',
                  ['rail_' + sk, key])
    add('towerpin_' + sk, cylc(V(xu, Y_SH, zu), EY, 7.9, 52), 'Shock top pin - ' + nm, 'Front suspension', STEEL)

    # ladder bar: one per side, horizontal at the pin height, rod ends at both ends (no roll lock)
    ax_x = s * PERCH_X
    fr_x = s * LADDER_FR_X
    A_, F_ = V(ax_x, LADDER_AXLE_Y, LADDER_Z), V(fr_x, LADDER_FRAME_Y, LADDER_Z)
    dv = F_ - A_; dv.normalize()
    bar = [cyl2(A_ + dv * 30.0, F_ - dv * 30.0, 15.875), cyl2(A_, A_ + dv * 30.0, 9.525),
           cyl2(F_, F_ - dv * 30.0, 9.525), cylc(A_, EZ, 14.3, 21.4), cylc(F_, EZ, 14.3, 21.4)]
    drill('ladder_' + sk, A_, EZ, 8.0, 60)
    drill('ladder_' + sk, F_, EZ, 8.0, 60)
    add('ladder_' + sk, fuse_all(bar), 'Ladder bar - ' + nm, 'Front suspension', DARK)
    add('ladderpins_' + sk, Part.makeCompound([cylc(P_, EZ, 7.9, 46) for P_ in (A_, F_)]),
        'Ladder bar pins - ' + nm, 'Front suspension', STEEL)

    # frame-side bracket: plate on the OUTSIDE of the rail web, with an ear pair for the bar
    xwo = s * x_wo(X_C_FRONT)
    xa, xb2 = sorted((xwo, xwo + s * TP))
    plate = boxr(xa, xb2, LADDER_FRAME_Y - 60, LADDER_FRAME_Y + 60, LADDER_Z - 60.0, LADDER_Z + 60.0)
    xs = sorted((xwo + s * TP, fr_x + s * 25.0))
    ears = [boxr(xs[0], xs[1], LADDER_FRAME_Y - 25, LADDER_FRAME_Y + 25,
                 LADDER_Z + dz - TP / 2.0, LADDER_Z + dz + TP / 2.0)
            for dz in (-(11.1 + TP / 2.0), (11.1 + TP / 2.0))]
    key = 'ladderfr_' + sk
    add(key, fuse_all([plate] + ears).cut(cylc(F_, EZ, 8.0, 80)), 'Ladder bar frame bracket - ' + nm,
        'Front suspension', RED)
    for dy in (-35.0, 35.0):
        for zz in (LADDER_Z + 8.0, LADDER_Z + 40.0):          # both rivets inside the web
            joint(V(xwo + s * TP, LADDER_FRAME_Y + dy, zz), V(-s, 0, 0), TP + RAIL_TW, 'Rivets - front suspension',
                  ['rail_' + sk, key])

    # axle-side bracket: L-bracket on the spring perch (top leg over the perch stud), a riser up to the
    # bar height, and an ear pair for the rod end
    pz = max(axle_top(abs(ax_x) - 20.0), axle_top(abs(ax_x) + 20.0))          # perch top, beside the stud
    RISER_Y0 = FA_Y1 + 11.0                              # stands off the arm's rear plate (Y 0.5..10)
    leg = boxr(ax_x - 30, ax_x + 30, FA_Y0, RISER_Y0 + TP, pz, pz + TP).cut(cylc(V(ax_x, Y_FA, pz), EZ, 7.0, 60))
    riser = boxr(ax_x - 25, ax_x + 25, RISER_Y0, RISER_Y0 + TP, pz - 5.0, LADDER_Z + 17.5)
    ears = [boxr(ax_x - 25, ax_x + 25, RISER_Y0 + TP, LADDER_AXLE_Y + 25,
                 LADDER_Z + dz - TP / 2.0, LADDER_Z + dz + TP / 2.0)
            for dz in (-(11.1 + TP / 2.0), (11.1 + TP / 2.0))]
    add('ladderax_' + sk, fuse_all([leg, riser] + ears).cut(cylc(A_, EZ, 8.0, 80)),
        'Ladder bar axle bracket - ' + nm, 'Front suspension', RED)

# --------------------------------------------------------------------------
# finalize: drill rivet / pin holes, build the document, save
# --------------------------------------------------------------------------
for k, h in HOLES.items():
    PARTS[k]['shape'] = PARTS[k]['shape'].cut(Part.makeCompound(h))
for g, shapes in RIVETS.items():
    add('rivets_' + g, Part.makeCompound(shapes), g, 'Rivets', (0.12, 0.12, 0.12))

if 'IH_frame' in FreeCAD.listDocuments():
    FreeCAD.closeDocument('IH_frame')
doc = FreeCAD.newDocument('IH_frame')
frame_part = doc.addObject('App::Part', 'IH_Frame')
frame_part.Label = 'IH Frame'
frame_part.Visibility = True
grp_objs = {}
for g in GROUP_ORDER:
    go = doc.addObject('App::DocumentObjectGroup', 'G_' + ''.join(c if c.isalnum() else '_' for c in g))
    go.Label = g
    frame_part.addObject(go)
    go.Visibility = True
    grp_objs[g] = go
for key, p in PARTS.items():
    o = doc.addObject('Part::Feature', 'P_' + key)
    o.Shape = p['shape']
    o.Label = p['label']
    o.Visibility = True
    grp_objs[p['group']].addObject(o)
    try:
        if p['rgb'] and o.ViewObject is not None:
            o.ViewObject.ShapeColor = p['rgb']
    except Exception:
        pass
doc.recompute()
import time
for _try in range(60):                      # the project folder is occasionally unreachable for a few seconds
    try:
        doc.saveAs(OUT_PATH)
        break
    except Exception as _e:
        _last_err = _e
        time.sleep(0.5)
else:
    raise _last_err

def _check(shape):
    if shape.isNull():
        return 'NULL'
    return {'valid': shape.isValid(), 'solids': len(shape.Solids), 'vol_cm3': round(shape.Volume / 1000.0, 1)}

_report = {k: _check(p['shape']) for k, p in PARTS.items()}
_problems = {k: v for k, v in _report.items() if v == 'NULL' or not v['valid'] or v['solids'] == 0}
_result_ = {'parts': len(PARTS), 'rivets': {g: len(v) // 3 for g, v in RIVETS.items()},
            'problems': _problems,
            'rails': {k: _report[k] for k in ('rail_L', 'rail_R')},
            'spring_eye_Y': [round(Y_EYE_F, 1), round(Y_EYE_R, 1)], 'eye_Z': round(EYE_Z, 1),
            'Y_FA': round(Y_FA, 1), 'FA_Y': [round(FA_Y0, 1), round(FA_Y1, 1)]}

print(_result_)
