"""IH rat rod - frame, rear leaf-spring suspension, front transverse torsion bars with roller arms, vertical hairpins and panhard.

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
X_C_FRONT = 271.0                   # rail centreline up front: outer web face at 291; the torsion arms sit just outside it, inboard of the pad bracket and hairpins
SHOCK_TOP_X = 415.0                 # shock tower top |X| (where it was with the rails at 325)
X_C_REAR = 495.3                    # = rear axle spring-perch X (39.0" between perches)
Z_F = 0.0                           # rail centerline height, front section (lowered so the level torsion bars clear the bottom flange)
Z_R = 225.0                         # rail centerline height, rear (kicked-up) section
Y_RAIL_FRONT, Y_RAIL_END = 15.0, 3550.0
Y_JOG0, Y_JOG1 = 1450.0, 1700.0     # abrupt step from 20" to 39" wide
Y_KICK0, Y_KICK1 = 1750.0, 2150.0   # kick-up over the rear axle

CM_YS = [70.0, 620.0, 900.0, 1350.0, 2400.0, None, 3450.0]   # 70 = front crossmember; None -> rear axle Y

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
PERCH_X = 345.0                     # the axle's spring pad (centre-bolt indent), re-measured from the axle
SHOCK_AX_X, SHOCK_AX_Z = 596.5, -28.5   # the axle's original shock-mount holes (re-measured from the axle)
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

def axle_mid(x):
    """Z of the middle of the front axle beam at |x| (live from the assembly)."""
    try:
        c = _fa.common(Part.makeBox(10, 400, 1000, V(abs(x) - 5, -200, -500)))
        return (c.BoundBox.ZMin + c.BoundBox.ZMax) / 2.0
    except Exception:
        return -175.0

try:                                    # find the spring-pad indent and the shock-mount hole on the real axle
    for _f in _fa.Faces:
        _sf, _b = _f.Surface, _f.BoundBox
        if _sf.__class__.__name__ != 'Cylinder' or _b.XMin < 0:
            continue
        if abs(_sf.Axis.z) > 0.99 and abs(_sf.Radius - 9.525) < 0.2:
            PERCH_X = (_b.XMin + _b.XMax) / 2.0
        elif abs(_sf.Axis.y) > 0.99 and abs(_sf.Radius - 9.5) < 0.2 and _f.Area > 2000:
            SHOCK_AX_X, SHOCK_AX_Z = (_b.XMin + _b.XMax) / 2.0, (_b.ZMin + _b.ZMax) / 2.0
except Exception:
    pass

BAR_Z = SHOCK_AX_Z                  # torsion bars level, parallel to the axle; arms swing about this axis (clears the rail's bottom flange)
ARM_CC = {'L': 16.5 * IN, 'R': 16.5 * IN}   # custom torsion arms, both 16.5 in: hub centre to tip hole
ARM_T = 0.75 * IN                   # arm thickness (forged aluminium I-beam, 2" wide at the hub)
ARM_HUB_R = 1.0 * IN                # arm hub boss, 2" across
ARM_TIP_R = 14.0                    # arm tip boss (assumed)
SPLINE_R = 1.13 * IN / 2.0          # 48-spline bar end / arm hub bore, 1.13" OD (arm bore is cut to the bar end)
ROLLER_R, ROLLER_W = 15.0, 26.6     # roller on the arm tip, centred on the spring perch, inboard of the arm
SADDLE_T = 1.0 * IN                 # custom axle bracket: saddle plate on the axle's spring pad (roller bearing surface), plus risers
AX_FLAT_TOP = axle_top(320.0)       # top of the axle's flared spring pad (the saddle plate sits on it)
AX_PAD_T = 12.7                     # spring pad plate thickness on the axle (see front axle.FCStd, SpringPad)
ROLLER_PIN_R = 6.35                 # 1/2" roller pin (tip hole size assumed)
SHOCK_TOWER_Y = 60.0                # shock towers, set back from the axle
SHOCK_EYE_Y = FA_Y1 + 11.6          # lower shock eye, against the back face of the axle
HP_ROD = 27.0 * IN                  # hairpin: 27" bend-to-heim length (Speedway 91635023 pattern)
HP_HALF = 2.5 * IN                  # hairpin: legs 5" centre to centre at the axle bracket, one above the other
HP_AXLE_X = PERCH_X                 # hairpin axle ears: centred on the spring pad, on the pad bracket
HP_Z = AX_FLAT_TOP - 12.0 + HP_HALF    # hairpin centre height: lower leg just below the pad top (clears the panhard bar), upper leg 5" above
HP_AXLE_Y = 57.0                    # heims at the axle, behind the bracket's riser plate (the pad's rear edge is at 28)
HP_BEND_Y = HP_AXLE_Y + HP_ROD      # bend (frame pivot) Y
HP_TUBE_R = 0.625 * IN              # placeholder: 1-1/4" OD fabricated tube (size to be confirmed)
HP_HEIM_R = 20.0                    # heim housing radius
HP_HEIM_HALF = HP_TUBE_R + 1.0      # heim housing half-width: the ears clear the leg tube
PIN_R = 7.9                         # 5/8" pins
PAN_CC = 27.5 * IN                  # panhard: Speedway 28-34 Ford 4-bar bar, 27.5" eye to eye
PAN_TUBE_R = 0.625 * IN / 2.0       # 5/8" tube
PAN_BOLT_R = 0.25 * IN              # 1/2" bolts and heims
PAN_HEIM_R, PAN_HEIM_HALF = 12.0, 8.0   # heim housing radius and half-width (assumed)
PAN_FR_OFF = 14.0                   # frame pivot: 14 mm outboard of the right rail's bracket plate (inboard of the right hairpin leg)
PAN_AX_X = PAN_CC - (X_C_FRONT + RAIL_BF / 2.0 + TP + PAN_FR_OFF)   # axle end of the panhard: the frame end is PAN_CC away, at the right rail
PAN_Z = axle_mid(PAN_AX_X) - AX_PAD_T / 2.0   # panhard bar, level, at mid-depth of the axle beam (spring pad excluded)

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
# front transverse torsion bars: parallel to the axle, set back in the frame. Each bar passes through its own rail
# to a custom torsion arm outside the frame. The bars are stacked: the left bar sits one stack pitch above the right,
# so the two equal-length arms reach the roller at slightly different angles and nearly the same lever.
# --------------------------------------------------------------------------
BAR_STACK = 1.25 * IN               # vertical pitch of the stacked bars: 1" bar plus clearance
BAR_ZS = {'L': BAR_Z + BAR_STACK, 'R': BAR_Z}   # bar axis height, by side
xwi_f, xwo_f = x_wi(X_C_FRONT), x_wo(X_C_FRONT)
ARM_WEB_GAP = 9.0                   # torsion arm inner face to the rail web's outer face (clears the rivet heads)
HUB_CX = xwo_f + ARM_WEB_GAP + ARM_T / 2.0   # arm hub centre, |X|: the arm is inboard of the roller, just outside the rail
# the roller rests on the top of the custom axle bracket's saddle plate, centred on the spring perch. With equal arm
# lengths, each bar's Y position follows from its height above the roller
SADDLE_TOP = AX_FLAT_TOP + SADDLE_T
zr, yr = SADDLE_TOP + ROLLER_R, Y_FA
BAR_Y = {sk: yr + math.sqrt(ARM_CC[sk] ** 2 - (BAR_ZS[sk] - zr) ** 2) for sk in SIDES}

def bar_plates(sw):
    """Plate on the inside of the web of rail `sw`, bored for both bars. This rail's own bar bears on it and the
    opposite bar is anchored to it, so the two stacked bores share one plate. The rivets sit between and outside
    the bores."""
    xwi, xwo = x_wi(X_C_FRONT), x_wo(X_C_FRONT)
    ys, zs = [BAR_Y[k] for k in SIDES], [BAR_ZS[k] for k in SIDES]
    xa, xb2 = sorted((sw * (xwi - TP), sw * xwi))
    plate = boxr(xa, xb2, min(ys) - 28.0, max(ys) + 28.0, min(zs) - 13.5, max(zs) + 20.0)
    for k in SIDES:
        plate = plate.cut(cylc(V(sw * (xwi - TP / 2.0), BAR_Y[k], BAR_ZS[k]), EX, BAR_R + 0.3, 60))
    side = 'L' if sw > 0 else 'R'
    add('tplate_' + side, plate, 'Torsion bar bearing and anchor plate - ' + NAME[side], 'Front suspension', RED)
    for yv in (min(ys) - 23.5, max(ys) + 23.5):
        for zv in (-30.0, 14.0):
            joint(V(sw * xwo, yv, zv), V(-sw, 0, 0), RAIL_TW + TP, 'Rivets - front suspension',
                  ['rail_' + side, 'tplate_' + side])

bar_plates(+1.0)
bar_plates(-1.0)
for sk, s in SIDES.items():
    nm = NAME[sk]
    yb, zb = BAR_Y[sk], BAR_ZS[sk]
    xr = s * PERCH_X                                     # roller centre: over the spring pad
    xroll0 = xr - s * ROLLER_W / 2.0                     # inner face of the roller
    xi0 = s * (xwo_f + ARM_WEB_GAP)                      # inner face of the arm: just outside the rail web (the arm is inboard of the roller)
    xi1 = xi0 + s * ARM_T                                # outer face of the arm

    # torsion bar: anchored on the opposite rail, through the bores of both bearing plates and the web of this rail;
    # the splined end (1.13") sits in the arm hub
    x_start = -s * xwi_f
    x_end = xi1 + s * 4.0
    x_stub = xi0 - s * 4.0
    bar = Part.makeCylinder(BAR_R, abs(x_stub - x_start), V(x_start, yb, zb), V(s, 0, 0)).fuse(
        Part.makeCylinder(SPLINE_R, abs(x_end - x_stub), V(x_stub, yb, zb), V(s, 0, 0)))
    add('tbar_' + sk, bar, 'Torsion bar - ' + nm, 'Front suspension', STEEL)
    drill('rail_' + sk, V(s * (xwi_f + xwo_f) / 2.0, yb, zb), EX, BAR_R + 0.3, 20.0)

    # custom torsion arm: the hub clamps the bar end outside the rail and the arm runs forward (perpendicular to the
    # axle) over the axle end. The roller on the tip sits inboard of the arm. Nothing is fastened to the axle: the axle
    # pushes up on the roller and the bar holds the arm down onto it.
    u = V(0, yr - yb, zr - zb)
    L = u.Length
    u.normalize()
    n = V(0, -u.z, u.y)

    def at(d, k, x):
        """Point d along the arm from the hub centre, k across it, in the plane X = x."""
        return V(x, yb + u.y * d + n.y * k, zb + u.z * d + n.z * k)

    def half_w(d):
        return ARM_HUB_R + (ARM_TIP_R - ARM_HUB_R) * d / L

    body = prism([at(0, ARM_HUB_R, xi0), at(L, ARM_TIP_R, xi0), at(L, -ARM_TIP_R, xi0), at(0, -ARM_HUB_R, xi0)],
                 V(s * ARM_T, 0, 0))
    body = body.fuse(Part.makeCylinder(ARM_HUB_R, ARM_T, V(xi0, yb, zb), V(s, 0, 0)))
    body = body.fuse(Part.makeCylinder(ARM_TIP_R, ARM_T, V(xi0, yr, zr), V(s, 0, 0)))
    web_t = 6.0                                          # I-beam: a 6 mm web between 5 mm rims, pocketed both sides
    pocket_d = (ARM_T - web_t) / 2.0
    d1, d2 = ARM_HUB_R + 7.0, L - ARM_TIP_R - 5.0
    for xf, sgn in ((xi0, 1.0), (xi1, -1.0)):
        pk = [at(d1, half_w(d1) - 5.0, xf), at(d2, half_w(d2) - 5.0, xf),
              at(d2, -(half_w(d2) - 5.0), xf), at(d1, -(half_w(d1) - 5.0), xf)]
        body = body.cut(prism(pk, V(s * sgn * pocket_d, 0, 0)))
    body = body.cut(Part.makeCylinder(SPLINE_R, ARM_T + 20.0, V(xi0 - s * 10.0, yb, zb), V(s, 0, 0)))
    body = body.cut(cylc(V(xi0, yr, zr), EX, ROLLER_PIN_R, 200))
    body = body.cut(boxr(*sorted((xi0, xi1)), yb, yb + ARM_HUB_R + 2.0, zb - 1.0, zb + 1.0))   # clamp slit
    xmid, y_pb = (xi0 + xi1) / 2.0, yb + 20.0
    body = body.cut(cylc(V(xmid, y_pb, zb), EZ, 4.0, 60))                                            # pinch bolt hole
    add('tarm_' + sk, body, 'Torsion arm (custom 16.5 in) - ' + nm, 'Front suspension', RED)
    add('tpinch_' + sk, cylc(V(xmid, y_pb, zb), EZ, 4.0, 34.0), 'Arm pinch bolt (shank) - ' + nm,
        'Front suspension', STEEL)
    add('roller_' + sk, Part.makeCylinder(ROLLER_R, ROLLER_W, V(xroll0, yr, zr), V(s, 0, 0)).cut(
        cylc(V(xr, yr, zr), EX, ROLLER_PIN_R, 200)), 'Arm roller - ' + nm, 'Front suspension', DARK)
    add('rollerpin_' + sk, Part.makeCylinder(ROLLER_PIN_R, abs(xr + s * ROLLER_W / 2.0 - xi0) + 6.0,
                                             V(xi0 - s * 3.0, yr, zr), V(s, 0, 0)),
        'Arm roller pin - ' + nm, 'Front suspension', STEEL)
    add('rollerspacer_' + sk, Part.makeCylinder(ROLLER_PIN_R + 5.0, abs(xroll0 - xi1), V(xi1, yr, zr), V(s, 0, 0)).cut(
        cylc(V(xr, yr, zr), EX, ROLLER_PIN_R, 200)), 'Arm roller spacer - ' + nm, 'Front suspension', STEEL)

    # shock: from the axle's own shock-mount hole (eye against the back face) up to the tower top
    xu, zu = s * SHOCK_TOP_X, Z_F + 360.0
    L0, U0 = V(s * SHOCK_AX_X, SHOCK_EYE_Y, SHOCK_AX_Z), V(xu, SHOCK_TOWER_Y, zu)
    dd = U0 - L0
    dl = dd.Length
    dn = V(dd); dn.normalize()
    shock = [cylc(L0, EY, 14.3, 22.2), cylc(U0, EY, 14.3, 22.2),
             Part.makeCylinder(6.35, 110.0, L0 + dn * 14.3, dn),
             Part.makeCylinder(15.0, dl - 30.0 - 124.3, L0 + dn * 124.3, dn),
             Part.makeCylinder(6.35, 15.7, U0 - dn * 30.0, dn)]          # neck up to the top eye
    add('shock_' + sk, Part.makeCompound(shock), 'Front shock - ' + nm, 'Front suspension', DARK)
    drill('shock_' + sk, L0, EY, 8.0, 60)
    drill('shock_' + sk, U0, EY, 8.0, 60)

    # lower shock pin: through the axle's shock-mount hole, with the head on the back
    xsp = s * SHOCK_AX_X
    y_pin0, y_pin1 = FA_Y0 - 10.0, SHOCK_EYE_Y + 11.1
    add('shockpin_' + sk, Part.makeCompound([
        Part.makeCylinder(PIN_R, y_pin1 - y_pin0, V(xsp, y_pin0, SHOCK_AX_Z), EY),
        Part.makeCylinder(12.7, 8.0, V(xsp, y_pin1, SHOCK_AX_Z), EY)]),
        'Shock pin - ' + nm, 'Front suspension', STEEL)

# --------------------------------------------------------------------------
# front hairpin radius rods and shock towers
# --------------------------------------------------------------------------
def xbox(xa_, xb_, y0, y1, z0, z1):
    """Box spanning two X values (in either order)."""
    return boxr(min(xa_, xb_), max(xa_, xb_), y0, y1, z0, z1)

# shock towers: one tubular frame for both sides - feet on the rail tops, two legs per side, a Y tube
# at the top of each leg pair, a cross brace across the car, and ears that hold the top of each shock
LEG_R = 0.5 * IN                     # 1" tube
ZB = Z_F + 360.0 + 32.0              # height of the tower top tubes and cross brace
tower = []
for sk, s in SIDES.items():
    nm = NAME[sk]
    xu, zu = s * SHOCK_TOP_X, Z_F + 360.0
    zt = Z_F + RAIL_D / 2.0          # top of the rail
    tower.append(xbox(s * X_C_FRONT - 22.0, s * X_C_FRONT + 22.0, SHOCK_TOWER_Y - 50.0, SHOCK_TOWER_Y + 50.0,
                      zt, zt + TP))                                    # foot on the rail top
    for d in (-1.0, 1.0):
        yl = SHOCK_TOWER_Y + d * 46.0
        tower.append(cyl2(V(s * X_C_FRONT, yl, zt + TP), V(xu, yl, ZB), LEG_R))      # leg (starts on the foot)
        ya, yb = sorted((SHOCK_TOWER_Y + d * 12.0, SHOCK_TOWER_Y + d * (12.0 + TP)))
        tower.append(boxr(xu - 20.0, xu + 20.0, ya, yb, zu - 10.0, ZB))              # shock ear, above the rod end
        for dx in (-8.0, 8.0):                                         # rivets into the rail top
            joint(V(s * X_C_FRONT + dx, SHOCK_TOWER_Y + d * 24.0, zt + TP), V(0, 0, -1), TP + RAIL_TF,
                  'Rivets - front suspension', ['rail_' + sk, 'shocktower'])
    tower.append(cyl2(V(xu, SHOCK_TOWER_Y - 46.0, ZB), V(xu, SHOCK_TOWER_Y + 46.0, ZB), LEG_R))   # top tube
    drill('shocktower', V(xu, SHOCK_TOWER_Y, zu), EY, 8.0, 60)
    add('shocktoppin_' + sk, cylc(V(xu, SHOCK_TOWER_Y, zu), EY, PIN_R, 2 * (12.0 + TP)),
        'Shock top pin - ' + nm, 'Front suspension', STEEL)
tower.append(cyl2(V(-SHOCK_TOP_X, SHOCK_TOWER_Y, ZB), V(SHOCK_TOP_X, SHOCK_TOWER_Y, ZB), LEG_R))  # cross brace
add('shocktower', fuse_all(tower), 'Shock towers (tubing, both sides)', 'Front suspension', RED)

for sk, s in SIDES.items():
    nm = NAME[sk]
    # hairpin radius rod (fabricated, placeholder tube), mounted upright: one U per side. Two legs, one above the
    # other (5" centre to centre), run rearward from the axle bracket to a bend that pivots in a housing on a bracket
    # behind the rail web.
    xh = s * HP_AXLE_X
    legs_z = [HP_Z - HP_HALF, HP_Z + HP_HALF]
    key = 'hp_' + sk
    legs = [cyl2(V(xh, HP_AXLE_Y, z), V(xh, HP_BEND_Y, z), HP_TUBE_R) for z in legs_z]
    crossbar = cyl2(V(xh, HP_BEND_Y, legs_z[0]), V(xh, HP_BEND_Y, legs_z[1]), HP_TUBE_R)
    heims = [cylc(V(xh, HP_AXLE_Y, z), EX, HP_HEIM_R, 2 * HP_HEIM_HALF) for z in legs_z]
    for z in legs_z:
        drill(key, V(xh, HP_AXLE_Y, z), EX, PIN_R, 60)
    add(key, fuse_all(legs + [crossbar] + heims), 'Hairpin radius rod - ' + nm, 'Front suspension', STEEL)

    # frame-side bracket: a bearing housing around the (vertical) bend bar, a plate back to the rail web, and a
    # plate on the OUTSIDE of the web (riveted). The bend sits behind the rail front end, clear of the legs
    xwo = s * x_wo(X_C_FRONT)
    hb = Part.makeSphere(HP_HEIM_R, V(xh, HP_BEND_Y, HP_Z))
    hb = hb.cut(cylc(V(xh, HP_BEND_Y, HP_Z), EZ, HP_TUBE_R + 0.3, 140))               # bend tube passes through
    y_arm = HP_BEND_Y + 17.2
    arm_pl = boxr(*sorted((xwo, xh)), y_arm, y_arm + TP, HP_Z - 20.0, HP_Z + 20.0)
    web_pl = boxr(*sorted((xwo, xwo + s * TP)), y_arm, y_arm + 52.0, HP_Z - 25.0, Z_F + 8.0)
    key_fr = 'hpfr_' + sk
    add(key_fr, fuse_all([hb, arm_pl, web_pl]), 'Hairpin frame bracket - ' + nm, 'Front suspension', RED)
    for dy in (27.2, 49.2):
        for rz in (-30.0, -12.0):                        # on the web, above the bottom flange
            joint(V(xwo + s * TP, HP_BEND_Y + dy, rz), V(-s, 0, 0), TP + RAIL_TW, 'Rivets - front suspension',
                  ['rail_' + sk, key_fr])

# --------------------------------------------------------------------------
# panhard bar (Speedway 27.5" eye to eye, 5/8" tube, 1/2" heims): level, from a bracket on the back of the axle, left of
# centre, to the outside of the right rail web. The frame end sits behind the front crossmember's end plates (Y 120).
PAN_Y = 150.0                                         # bar Y
pan_xa = PAN_AX_X                                     # axle pivot X
pan_xf = pan_xa - PAN_CC                              # frame pivot X (outside the right rail)
xw_r = -x_wo(X_C_FRONT)                               # outer face of the right rail web
ear_dy = PAN_HEIM_HALF + TP / 2.0                     # ear centres either side of the heim
ear_out = ear_dy + TP / 2.0                           # outer face of each ear pair

pan_rod = fuse_all([cyl2(V(pan_xf, PAN_Y, PAN_Z), V(pan_xa, PAN_Y, PAN_Z), PAN_TUBE_R),
                    cylc(V(pan_xf, PAN_Y, PAN_Z), EY, PAN_HEIM_R, 2 * PAN_HEIM_HALF),
                    cylc(V(pan_xa, PAN_Y, PAN_Z), EY, PAN_HEIM_R, 2 * PAN_HEIM_HALF)])
for px in (pan_xf, pan_xa):
    drill('panhard', V(px, PAN_Y, PAN_Z), EY, PAN_BOLT_R, 40)
add('panhard', pan_rod, 'Panhard bar (Speedway, 27.5" eye to eye)', 'Front suspension', STEEL)

# frame bracket: a plate on the outside of the right rail web (riveted), stopping above the bar, with an ear pair
# that hangs down outside the web to the heim (the bar passes under the plate and the rail)
z_pl0 = PAN_Z + 23.0                                  # bottom of the plate, above the bar
pan_fr = [boxr(*sorted((xw_r, xw_r - TP)), 128.0, 174.0, z_pl0, Z_F + 8.0)]
for d in (-ear_dy, ear_dy):
    pan_fr.append(boxr(pan_xf - 14.0, xw_r - TP, PAN_Y + d - TP / 2.0, PAN_Y + d + TP / 2.0, PAN_Z - 18.0, z_pl0 + 12.0))
add('panbk_fr', fuse_all(pan_fr), 'Panhard frame bracket', 'Front suspension', RED)
drill('panbk_fr', V(pan_xf, PAN_Y, PAN_Z), EY, PAN_BOLT_R, 60)
for dy in (138.0, 164.0):
    for rz in (-30.0, -12.0):
        joint(V(xw_r - TP, dy, rz), V(1.0, 0, 0), TP + RAIL_TW, 'Rivets - front suspension', ['rail_R', 'panbk_fr'])

# custom axle bracket on the spring pad: it clamps to the pad the way the original leaf spring did (saddle plate on the
# pad, two U-bolts through the pad's holes, a plate under the beam) and is centred on the pad. The top of the saddle is
# the bearing surface for the torsion arm's roller; the hairpin ears and (on the left) the panhard ears hang off its
# rear side. The U-bolt bends sit in grooves in the saddle top so the arm clears them.
UB_HX, UB_HY = 2.625 * IN / 2.0, 3.0 * IN / 2.0       # U-bolt hole half spacing on the pad: across / along the spring
UB_R = 6.35                                           # 1/2" U-bolt
PAD_HALF_Y = 50.0                                     # fore-aft half depth of the axle's spring pad (front axle.FCStd)
PAD_Y0, PAD_Y1 = Y_FA - PAD_HALF_Y, Y_FA + PAD_HALF_Y
SADDLE_HX = 24.0                                      # saddle half width (X), between the U-bolt legs
GROOVE_HW, GROOVE_D = 7.0, 13.0                       # U-bolt grooves across the saddle top
BP_T, BP_HX, BP_HY = 9.5, 45.0, 48.0                  # plate under the beam
try:
    AX_BOT = _fa.common(Part.makeBox(8, 400, 1000, V(PERCH_X - 4.0, -200, -500))).BoundBox.ZMin   # flat underside at the pad centre
except Exception:
    AX_BOT = -205.0
ear_h = HP_HEIM_HALF + TP / 2.0                       # hairpin ear centres either side of the heim
riser_hx = ear_h + TP / 2.0                           # riser half width = outer face of the ear pair
web_x0 = pan_xa + 22.0                                # panhard: web plate outboard of the heim, running back to the ears
for sk, s in SIDES.items():
    nm = NAME[sk]
    xp = s * PERCH_X
    legs_z = [HP_Z - HP_HALF, HP_Z + HP_HALF]
    key = 'perchbk_' + sk
    saddle = boxr(*sorted((xp - SADDLE_HX, xp + SADDLE_HX)), PAD_Y0, PAD_Y1, AX_FLAT_TOP, SADDLE_TOP)
    for dy in (-UB_HY, UB_HY):
        saddle = saddle.cut(boxr(xp - SADDLE_HX - 1.0, xp + SADDLE_HX + 1.0, Y_FA + dy - GROOVE_HW, Y_FA + dy + GROOVE_HW,
                                 SADDLE_TOP - GROOVE_D, SADDLE_TOP + 1.0))
    parts = [saddle]
    parts.append(boxr(xp - riser_hx, xp + riser_hx, PAD_Y1, PAD_Y1 + TP,
                      legs_z[0] - 25.0, legs_z[1] + 25.0))                       # riser behind the pad for the stacked hairpin heims
    for dx in (-ear_h, ear_h):                                                    # one ear pair serves both heims
        parts.append(boxr(xp + dx - TP / 2.0, xp + dx + TP / 2.0,
                          PAD_Y1 + TP, HP_AXLE_Y + 20.0, legs_z[0] - 18.0, legs_z[1] + 18.0))
    if sk == 'L':
        parts.append(boxr(xp - riser_hx, web_x0 + TP, PAD_Y1, PAD_Y1 + TP, PAN_Z - 25.0, PAN_Z + 25.0))   # low riser out to the panhard web, under the hairpin
        parts.append(boxr(web_x0, web_x0 + TP, PAD_Y1, PAN_Y + ear_out + 1.5, PAN_Z - 25.0, PAN_Z + 25.0))
        for d in (-ear_dy, ear_dy):
            parts.append(boxr(pan_xa - 14.0, web_x0 + TP / 2.0, PAN_Y + d - TP / 2.0, PAN_Y + d + TP / 2.0,
                              PAN_Z - 16.0, PAN_Z + 16.0))
    shp = fuse_all(parts)
    if _fa is not None:
        shp = shp.cut(_fa)
    add(key, shp, 'Axle bracket on the spring pad - ' + nm, 'Front suspension', RED)
    for z in legs_z:
        drill(key, V(s * HP_AXLE_X, HP_AXLE_Y, z), EX, PIN_R, 120)
    if sk == 'L':
        drill(key, V(pan_xa, PAN_Y, PAN_Z), EY, PAN_BOLT_R, 60)
    add('hppin_' + sk, Part.makeCompound([cylc(V(s * HP_AXLE_X, HP_AXLE_Y, z), EX, PIN_R, 2 * (ear_h + TP) + 4)
                                          for z in legs_z]),
        'Hairpin axle pins - ' + nm, 'Front suspension', STEEL)

    # plate under the beam and the two U-bolts (legs through the pad's holes, bends in the saddle grooves)
    bp_bot = AX_BOT - BP_T
    plt = boxr(xp - BP_HX, xp + BP_HX, Y_FA - BP_HY, Y_FA + BP_HY, bp_bot, AX_BOT)
    if _fa is not None:
        plt = plt.cut(_fa)                                                        # pocketed where the beam dips toward the centre
    add('axplate_' + sk, plt, 'U-bolt plate under the axle - ' + nm, 'Front suspension', RED)
    ub = []
    zc = SADDLE_TOP - UB_R
    for dy in (-UB_HY, UB_HY):
        ub.append(cyl2(V(xp - UB_HX, Y_FA + dy, zc), V(xp + UB_HX, Y_FA + dy, zc), UB_R))             # bend
        for dx in (-UB_HX, UB_HX):
            ub.append(cyl2(V(xp + dx, Y_FA + dy, zc), V(xp + dx, Y_FA + dy, bp_bot - 22.0), UB_R))    # leg
            ub.append(Part.makeCylinder(11.0, 10.0, V(xp + dx, Y_FA + dy, bp_bot - 10.0), EZ))         # nut
            drill('axplate_' + sk, V(xp + dx, Y_FA + dy, bp_bot + BP_T / 2.0), EZ, UB_R + 0.4, 30)
    add('axubolts_' + sk, Part.makeCompound(ub), 'Axle U-bolts - ' + nm, 'Front suspension', STEEL)

# panhard bolts: head against one ear, nut against the other
bolts = []
for px in (pan_xf, pan_xa):
    y0 = PAN_Y - ear_out - 5.0
    bolts.append(Part.makeCylinder(PAN_BOLT_R, 2 * ear_out + 10.0, V(px, y0, PAN_Z), EY))
    bolts.append(Part.makeCylinder(9.5, 5.0, V(px, y0, PAN_Z), EY))
    bolts.append(Part.makeCylinder(9.0, 5.0, V(px, PAN_Y + ear_out, PAN_Z), EY))
add('panpins', Part.makeCompound(bolts), 'Panhard bolts', 'Front suspension', STEEL)

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
