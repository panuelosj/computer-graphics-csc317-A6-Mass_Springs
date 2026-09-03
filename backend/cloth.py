"""Procedural cloth-grid generation (non-student infrastructure).

Builds a rectangular grid of point masses connected by springs, the data the
student's solver operates on. Edges are the unique edges of the triangulated
grid, which gives both *structural* springs (grid axes) and *shear* springs
(triangle diagonals) — enough for believable cloth.

Nothing here is graded; it just feeds inputs to ``src/``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np


@dataclass
class Cloth:
    V: np.ndarray   # (n, 3) initial vertex positions
    F: np.ndarray   # (f, 3) triangle faces (for display)
    E: np.ndarray   # (m, 2) unique spring edges
    m: np.ndarray   # (n,)   per-vertex masses
    b: np.ndarray   # (c,)   pinned vertex indices
    k: float        # spring stiffness
    delta_t: float  # time step
    uv: np.ndarray = None    # (n, 2) texture coordinates, when the scene has them
    texture: str = None      # path to the scene's texture image, if any


def edges_from_faces(F: np.ndarray) -> np.ndarray:
    """Unique undirected edges of a triangle mesh, as a sorted (m, 2) array."""
    seen = set()
    for f in F:
        for i in range(3):
            a, b = int(f[i]), int(f[(i + 1) % 3])
            seen.add((a, b) if a < b else (b, a))
    return np.array(sorted(seen), dtype=np.int64)


def grid_cloth(nx=12, ny=12, width=1.0, height=1.0, mass=1.0, k=100.0,
               delta_t=1.0 / 30.0, pin="top_row") -> Cloth:
    """Generate a cloth grid hanging in the x-y plane (z = 0 at rest).

    Row 0 is the top (``y = 0``); rows increase downward (``y < 0``). The mesh
    is pinned so gravity (``-y``) makes it drape rather than fall away.

    Parameters
    ----------
    nx, ny : int       grid resolution (vertices per row / column).
    width, height : float   physical extent.
    mass : float       per-vertex mass.
    k : float          spring stiffness.
    delta_t : float    time step.
    pin : str          "top_row" (whole top edge) or "top_corners".
    """
    xs = np.linspace(0.0, width, nx)
    ys = np.linspace(0.0, -height, ny)

    def idx(r, c):
        return r * nx + c

    V = np.zeros((nx * ny, 3), dtype=np.float64)
    for r in range(ny):
        for c in range(nx):
            V[idx(r, c)] = (xs[c], ys[r], 0.0)

    faces = []
    for r in range(ny - 1):
        for c in range(nx - 1):
            v00, v01 = idx(r, c), idx(r, c + 1)
            v10, v11 = idx(r + 1, c), idx(r + 1, c + 1)
            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])
    F = np.array(faces, dtype=np.int64)

    E = edges_from_faces(F)
    m = np.full(nx * ny, float(mass), dtype=np.float64)

    if pin == "top_corners":
        b = np.array([idx(0, 0), idx(0, nx - 1)], dtype=np.int64)
    else:  # "top_row"
        b = np.array([idx(0, c) for c in range(nx)], dtype=np.int64)

    return Cloth(V=V, F=F, E=E, m=m, b=b, k=float(k), delta_t=float(delta_t))


def load_params(path: str) -> dict:
    """Load grid parameters from a small JSON file."""
    with open(path) as f:
        return json.load(f)


def cloth_from_params(path: str) -> Cloth:
    p = load_params(path)
    return grid_cloth(
        nx=int(p.get("nx", 12)),
        ny=int(p.get("ny", 12)),
        width=float(p.get("width", 1.0)),
        height=float(p.get("height", 1.0)),
        mass=float(p.get("m", 1.0)),
        k=float(p.get("k", 100.0)),
        delta_t=float(p.get("delta_t", 1.0 / 30.0)),
        pin=str(p.get("pin", "top_row")),
    )


def _read_scene_obj(path: str):
    """Parse a scene .obj into (V, triangles, explicit_edges, uv).

    These files use faces of mixed arity on purpose: a face with **two**
    vertices is a bare spring (the chain and net scenes are built entirely
    from them and have no surface at all), three or more is a polygon.
    """
    V, VT, tris, edges = [], [], [], []
    uv_of_vertex = {}
    with open(path) as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "v":
                V.append([float(x) for x in parts[1:4]])
            elif parts[0] == "vt":
                VT.append([float(x) for x in parts[1:3]])
            elif parts[0] == "f":
                corners = [p.split("/") for p in parts[1:]]
                idx = [int(c[0]) - 1 for c in corners]
                for c, vi in zip(corners, idx):
                    if len(c) > 1 and c[1]:
                        uv_of_vertex[vi] = int(c[1]) - 1
                if len(idx) == 2:
                    edges.append(idx)
                elif len(idx) == 4:
                    # A quad is fully braced: all six vertex pairs become
                    # springs -- its four sides *and* both diagonals. Without
                    # the diagonals the sheet shears in-plane into a flat
                    # parallelogram instead of buckling into folds, and the
                    # load rides on fewer springs so it stretches ~3x as much.
                    for a in range(4):
                        for c2 in range(a + 1, 4):
                            edges.append([idx[a], idx[c2]])
                    tris.append([idx[0], idx[1], idx[2]])
                    tris.append([idx[0], idx[2], idx[3]])
                elif len(idx) >= 3:
                    for j in range(len(idx)):
                        edges.append([idx[j], idx[(j + 1) % len(idx)]])
                    for j in range(1, len(idx) - 1):
                        tris.append([idx[0], idx[j], idx[j + 1]])
    V = np.asarray(V, dtype=float)
    uv = None
    if VT and uv_of_vertex:
        # These meshes carry one texture coordinate per vertex, so the UVs can
        # live on the vertices directly rather than per face-corner -- which is
        # what a per-vertex renderer needs.
        VT = np.asarray(VT, dtype=float)
        uv = np.zeros((V.shape[0], 2), dtype=float)
        for vi, ti in uv_of_vertex.items():
            if 0 <= ti < VT.shape[0]:
                uv[vi] = VT[ti]
    return (V,
            np.asarray(tris, dtype=np.int64).reshape(-1, 3),
            np.asarray(edges, dtype=np.int64).reshape(-1, 2),
            uv)


def _scene_masses(spec: dict, V, F, path):
    """Per-vertex masses for a scene.

    A scene may state a single mass for every vertex (``"m": 1``). When it does
    not, the mass is the vertex's share of the surface *area* -- a big triangle
    weighs more than a small one. That distinction matters: on the sheets the
    area-weighted mass is a thousand-odd times smaller than a unit mass, and
    getting it wrong leaves the cloth with far too much inertia, so it
    overshoots and looks rubbery instead of settling.
    """
    n = V.shape[0]
    if "m" in spec:
        return np.full(n, float(spec["m"]), dtype=np.float64)
    if F.size == 0:
        raise ValueError(f'{path}: no "m" given and no faces to weigh by area')
    tri = V[F]
    area = 0.5 * np.linalg.norm(
        np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    m = np.zeros(n, dtype=np.float64)
    for j in range(3):                      # barycentric: area/3 per corner
        np.add.at(m, F[:, j], area / 3.0)
    m[m <= 0] = float(area.mean()) / 3.0    # stray unreferenced vertex
    return m


def cloth_from_scene(path: str) -> Cloth:
    """Load one of the sample scenes: a ``.json`` naming a ``.obj``.

    The scene files are the original assignment's::

        {"obj": "net.obj", "k": 3e2, "m": 1, "b": [1,5,35,61,57,27]}

    ``b`` lists the pinned vertices **1-indexed**, as .obj itself numbers
    vertices; they are converted to 0-based here.

    Springs are the unique edges of the triangulated surface plus any bare
    two-vertex faces. Triangulating first is deliberate: it adds the diagonal
    of every quad, giving the shear springs a sheet needs to keep its shape
    instead of collapsing sideways -- the same structural + shear pairing
    :func:`grid_cloth` builds.
    """
    with open(path) as f:
        spec = json.load(f)
    obj = spec.get("obj")
    if not obj:
        raise ValueError(f'{path}: scene has no "obj"')
    full = obj if os.path.isabs(obj) else os.path.join(os.path.dirname(path), obj)
    V, F, explicit, uv = _read_scene_obj(full)

    n = V.shape[0]
    if explicit.size == 0:
        raise ValueError(f"{path}: scene has no springs")
    E = np.unique(np.sort(explicit, axis=1), axis=0)

    b = np.array([int(i) - 1 for i in spec.get("b", [])], dtype=np.int64)
    if b.size and (b.min() < 0 or b.max() >= n):
        raise ValueError(f"{path}: pinned index out of range for {n} vertices")

    return Cloth(
        V=V,
        F=F,
        E=E,
        m=_scene_masses(spec, V, F, path),
        b=b,
        k=float(spec.get("k", 1.0e3)),
        delta_t=float(spec.get("delta_t", 1.0 / 30.0)),
        uv=uv,
        texture=(os.path.join(os.path.dirname(path), spec["png"])
                 if spec.get("png") else None),
    )


def load_cloth(path: str) -> Cloth:
    """Load either scene form: a grid description, or an .obj-backed scene."""
    with open(path) as f:
        spec = json.load(f)
    return cloth_from_scene(path) if "obj" in spec else cloth_from_params(path)


def spring_energy(U: np.ndarray, E: np.ndarray, r: np.ndarray, k: float) -> float:
    """Total spring potential energy ``sum_e 0.5 k (|U_i - U_j| - r_e)^2``."""
    d = U[E[:, 0]] - U[E[:, 1]]
    lengths = np.linalg.norm(d, axis=1)
    return float(0.5 * k * np.sum((lengths - r) ** 2))


def write_obj(path: str, V: np.ndarray, F: np.ndarray) -> None:
    """Write a minimal triangle-mesh ``.obj`` (1-based indices)."""
    with open(path, "w") as f:
        for v in V:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for face in F:
            f.write(f"f {face[0] + 1} {face[1] + 1} {face[2] + 1}\n")
