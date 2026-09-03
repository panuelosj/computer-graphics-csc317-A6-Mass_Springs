#!/usr/bin/env python3
"""Assignment 6 demo backend: simulate a falling/draping cloth.

Generates a cloth grid (see ``backend/cloth.py``), then advances it with YOUR
``src/`` functions using the "fast mass springs" local-global solver. The cloth
hangs from its pinned top edge and sags under gravity; optional wind adds a
time-varying force.

Interactive (default):

    python main.py

  * **Click and drag any cloth vertex** to pull the cloth around. The grabbed
    vertex becomes a temporary pin at the mouse position (your
    precomputation is re-run with the extra pin, then released).
  * Keys (also available as GUI buttons):
      [space]  pause and advance ONE time step
      A        toggle the animation on/off
      R        reset to the initial configuration
      W        toggle wind
      L        show/hide the spring network

Headless (used by CI / grading; no window needed):

    python main.py --headless            # simulate, write OBJ frames to out/
    python main.py --headless --dense    # use the dense solver path
    python main.py --steps 120 --wind    # more steps, with wind

The default solver path is SPARSE; pass --dense for the dense path.
"""

import argparse
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# `cgcommon` (shared helpers) normally sits next to this file. If several
# assignments are checked out together it lives two levels up instead.
if not os.path.isdir(os.path.join(HERE, "cgcommon")):
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

from backend.cloth import load_cloth, spring_energy, write_obj

DEFAULT_PARAMS = os.path.join(HERE, "data", "cloth.json")


def make_fext(U, m, t, wind, bbd):
    """External force per vertex: gravity (-y) plus optional sinusoidal wind."""
    n = U.shape[0]
    fext = np.zeros((n, 3), dtype=np.float64)
    # Gravity: a constant -9.8 force per vertex (with the default unit
    # masses this equals -9.8*m).
    fext[:, 1] = -9.8
    if wind:
        x = U[:, 0] / bbd
        # Phase the wind by the simulation time t rather than the wall clock,
        # so a run is reproducible.
        phi = x + t
        fext[:, 0] += 3.0 + 3.0 * 0.5 * (1.0 + np.cos(5.0 * phi))
        fext[:, 2] += 2.0 * 0.5 * np.sin(phi)
        fext[:, 1] += 1.0 * (1.0 + np.cos(0.3 + phi))
    return fext


def build_solver(use_dense):
    """Import the matching precomputation + step pair from the student's src/."""
    if use_dense:
        from src.fast_mass_springs_precomputation_dense import (
            fast_mass_springs_precomputation_dense as precompute,
        )
        from src.fast_mass_springs_step_dense import (
            fast_mass_springs_step_dense as step,
        )
    else:
        from src.fast_mass_springs_precomputation_sparse import (
            fast_mass_springs_precomputation_sparse as precompute,
        )
        from src.fast_mass_springs_step_sparse import (
            fast_mass_springs_step_sparse as step,
        )
    return precompute, step


def run_headless(cloth, use_dense, n_steps, wind):
    precompute, step = build_solver(use_dense)
    V, E, k, m, b, dt = cloth.V, cloth.E, cloth.k, cloth.m, cloth.b, cloth.delta_t

    t0 = time.perf_counter()
    r, M, A, C, pre = precompute(V, E, k, m, b, dt)
    precompute_time = time.perf_counter() - t0

    bbd = float(np.linalg.norm(V.max(axis=0) - V.min(axis=0)))
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)

    U0 = V.copy()
    Uprev = U0.copy()
    Ucur = U0.copy()

    label = "dense" if use_dense else "sparse"
    print(f"[{label}] {V.shape[0]} masses, {E.shape[0]} springs, "
          f"{len(b)} pinned. precompute={precompute_time*1e3:.1f} ms")
    print(f"  {'step':>4}  {'time(ms)':>9}  {'energy':>12}  {'max|disp|':>10}")

    frame_every = max(1, n_steps // 10)
    for s in range(n_steps):
        fext = make_fext(Ucur, m, s * dt, wind, bbd)
        ts = time.perf_counter()
        Unext = step(V, E, k, b, dt, fext, r, M, A, C, pre, Uprev, Ucur)
        step_ms = (time.perf_counter() - ts) * 1e3
        Unext = np.asarray(Unext)
        Uprev, Ucur = Ucur, Unext
        if s % frame_every == 0 or s == n_steps - 1:
            energy = spring_energy(Ucur, E, r, k)
            disp = float(np.linalg.norm(Ucur - U0, axis=1).max())
            print(f"  {s:>4}  {step_ms:>9.2f}  {energy:>12.4f}  {disp:>10.4f}")
            write_obj(os.path.join(out_dir, f"{label}_frame_{s:04d}.obj"),
                      Ucur, cloth.F)

    np.save(os.path.join(out_dir, f"{label}_final_positions.npy"), Ucur)
    # sanity: pinned vertices stay put
    pin_drift = float(np.linalg.norm(Ucur[b] - U0[b], axis=1).max())
    print(f"  final positions -> out/{label}_final_positions.npy "
          f"(pin drift {pin_drift:.2e})")


def run_interactive(cloth, use_dense, wind_default, max_frames=None):
    from cgcommon import viewer
    try:
        viewer.ensure_init()
    except viewer.ViewerUnavailable as exc:
        print(f"polyscope unavailable ({exc}); falling back to --headless.")
        return False

    import polyscope as ps
    import polyscope.imgui as psim
    from cgcommon.interact import PointDragger, key_pressed

    precompute, step = build_solver(use_dense)
    V, E, k, m, b, dt = cloth.V, cloth.E, cloth.k, cloth.m, cloth.b, cloth.delta_t

    # The default solver: original pins only.
    base = precompute(V, E, k, m, b, dt)
    bbd = float(np.linalg.norm(V.max(axis=0) - V.min(axis=0)))

    U0 = V.copy()
    state = {
        "Uprev": U0.copy(), "Ucur": U0.copy(), "t": 0.0,
        "wind": wind_default, "simulating": True, "show_springs": True,
        # active drag: (vertex index, solver tuple with extra pin, pin targets)
        "grab": None,
    }

    mesh = ps.register_surface_mesh("cloth", V, cloth.F, smooth_shade=True)
    mesh.set_color((0.35, 0.55, 0.80))
    net = ps.register_curve_network("springs", V, E, radius=0.0015)
    net.set_color((0.1, 0.1, 0.1))
    pinned_pc = ps.register_point_cloud("pinned", V[b], radius=0.008)
    pinned_pc.set_color((0.75, 0.75, 0.78))         # silver, like the original
    grabbed_pc = None

    dragger = PointDragger(grab_radius=0.05 * bbd)

    def do_step():
        if state["grab"] is None:
            solver, b_now, V_pin = base, b, V
        else:
            _, solver, V_pin = state["grab"]
            b_now = state["grab_b"]
        r, M, A, C, pre = solver
        fext = make_fext(state["Ucur"], m, state["t"], state["wind"], bbd)
        Unext = np.asarray(step(V_pin, E, k, b_now, dt, fext, r, M, A, C, pre,
                                state["Uprev"], state["Ucur"]))
        state["Uprev"], state["Ucur"] = state["Ucur"], Unext
        state["t"] += dt

    def reset():
        state["Uprev"], state["Ucur"], state["t"] = U0.copy(), U0.copy(), 0.0

    def callback():
        nonlocal grabbed_pc
        # --- keyboard ---
        if key_pressed("Space"):
            state["simulating"] = False
            do_step()
        if key_pressed("A"):
            state["simulating"] = not state["simulating"]
        if key_pressed("R"):
            reset()
        if key_pressed("W"):
            state["wind"] = not state["wind"]
        if key_pressed("L"):
            state["show_springs"] = not state["show_springs"]
            net.set_enabled(state["show_springs"])

        # --- GUI ---
        _, state["simulating"] = psim.Checkbox("simulating (A)", state["simulating"])
        psim.SameLine()
        if psim.Button("step once (space)"):
            state["simulating"] = False
            do_step()
        _, state["wind"] = psim.Checkbox("wind (W)", state["wind"])
        psim.SameLine()
        if psim.Button("reset (R)"):
            reset()
        changed, state["show_springs"] = psim.Checkbox(
            "show springs (L)", state["show_springs"])
        if changed:
            net.set_enabled(state["show_springs"])
        psim.TextUnformatted("click + drag any cloth vertex to pull it")

        # --- mouse grab-and-drag: temporary pin at the mouse position ---
        event, idx, pos = dragger.update(state["Ucur"])
        if event == "grab":
            b2 = np.unique(np.concatenate([b, [idx]])).astype(b.dtype)
            solver = precompute(V, E, k, m, b2, dt)   # student's precompute!
            V_pin = V.copy()
            V_pin[idx] = state["Ucur"][idx]
            state["grab"] = (idx, solver, V_pin)
            state["grab_b"] = b2
            grabbed_pc = ps.register_point_cloud(
                "grabbed", state["Ucur"][idx][None, :], radius=0.012)
            grabbed_pc.set_color((0.9, 0.45, 0.65))   # pink
        elif event == "drag":
            _, solver, V_pin = state["grab"]
            V_pin[idx] = np.asarray(pos, dtype=float)
            grabbed_pc.update_point_positions(V_pin[idx][None, :])
        elif event == "release":
            state["grab"] = None
            state.pop("grab_b", None)
            if grabbed_pc is not None:
                grabbed_pc.remove()
                grabbed_pc = None

        # step the simulation (always while dragging, so the cloth follows)
        if state["simulating"] or state["grab"] is not None:
            do_step()

        mesh.update_vertex_positions(state["Ucur"])
        net.update_node_positions(state["Ucur"])
        pinned_pc.update_point_positions(state["Ucur"][b])

    ps.set_user_callback(callback)
    print("Interactive: drag cloth vertices with the mouse; keys: "
          "[space] single step, A animate, R reset, W wind, L springs.")
    if max_frames is not None:
        for _ in range(max_frames):
            ps.frame_tick()
    else:
        viewer.show()
    return True


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("params", nargs="?", default=DEFAULT_PARAMS,
                        help="cloth parameters JSON (default: data/cloth.json)")
    parser.add_argument("--headless", action="store_true",
                        help="run without a window; write OBJ frames to out/")
    parser.add_argument("--dense", action="store_true",
                        help="use the dense solver path (default: sparse)")
    parser.add_argument("--steps", type=int, default=90,
                        help="number of time steps (headless)")
    parser.add_argument("--wind", action="store_true", help="enable wind")
    parser.add_argument("--frames", type=int, default=None,
                        help=argparse.SUPPRESS)  # debug: tick N frames and exit
    args = parser.parse_args(argv[1:])

    cloth = load_cloth(args.params)

    if args.headless:
        run_headless(cloth, args.dense, args.steps, args.wind)
        return

    ok = run_interactive(cloth, args.dense, args.wind, max_frames=args.frames)
    if not ok:
        run_headless(cloth, args.dense, args.steps, args.wind)


if __name__ == "__main__":
    main(sys.argv)
