# Computer Graphics – Mass-Spring Systems

> **To get started:** Clone this repository:
>
>     git clone git@github.com:panuelosj/computer-graphics-csc317-A6-Mass_Springs.git
>
> **Do not fork:** Clicking "Fork" will create a _public_ repository. If you'd
> like to use GitHub while you work on your assignment, then mirror this repo as
> a new _private_ repository:
> https://stackoverflow.com/questions/10065526/github-how-to-make-a-fork-of-public-repository-private

<img src="docs/images/flag.gif" alt="a flag simulated as a mass-spring network, waving in the wind" width="460">

## Introduction

In this assignment we animate a deformable shape (a piece of cloth) by treating
it as a network of [point
masses](https://en.wikipedia.org/wiki/Point_particle) connected by
[springs](https://en.wikipedia.org/wiki/Effective_mass_(spring%E2%80%93mass_system)).
We think of the shape as a
[graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)): every
vertex is a point mass and every edge is a spring. Given initial positions and
velocities we step physics forward in time following Newton's laws, using the
fast **local-global** ("fast mass springs") solver of Liu et al. 2013.

## Learning objectives

By completing this assignment you will be able to:

* model a deformable object as a **mass-spring network** and encode its
  topology in a **signed incidence matrix**;
* derive implicit time integration as an **energy minimization** (the
  variational form of implicit Euler);
* implement the **local-global** solver: a nonlinear per-spring "local" step
  alternating with a **prefactorized** global linear solve;
* enforce pinned-vertex constraints with a **penalty method**;
* contrast **dense and sparse** linear algebra, and explain why caching a
  Cholesky/LU factorization makes real-time simulation possible.

## Prerequisite knowledge

* **Math**: linear systems and positive-definite matrices; Cholesky
  factorization (conceptually); Newton's second law; finite differences in
  time; gradients of quadratic energies.
* **Programming**: `scipy.sparse` matrices and factorizations
  (`cho_factor`/`splu` are introduced in the stubs); `numpy`.
* **Course**: A5's objective/gradient mindset; edges-of-a-mesh conventions
  from A4.

### Prerequisite installation and setup

This assignment ships with everything it needs. From the **root of this
repository**, create its virtual environment once:

```bash
./init.sh            # macOS / Linux
# or, on Windows (PowerShell):
.\init.ps1
```

That creates `./venv` here and installs the dependencies (`numpy`, `pillow`,
`scipy`, `polyscope`). Then activate it in every new shell:

```bash
source venv/bin/activate           # macOS / Linux
# .\venv\Scripts\Activate.ps1      # Windows
```

Each assignment has its own `venv`, so activate the one belonging to the
assignment you are working on.

### Layout

All assignments share a similar directory layout:

    README.md            this file: background, tasks, and grading
    init.sh / init.ps1   one-time setup: creates ./venv and installs deps
    main.py              the main script that runs your code end-to-end
    run_tests.py         runs the unit checks and reports how many pass
    check_my_work.py     the same checks, but weighted by each function's allocated marks
    export_expected.py   exports the public tests' inputs and expected outputs as readable text and images
    cgcommon/            code shared by every assignment (do not edit)
    src/                 one file per function that YOU implement
    backend/             non-student infrastructure (cloth grid generation)
    tests/               the unit checks and their reference results (do not edit)
    tests/expected/      the public test data, readable (INDEX.md, .txt, .png)
    docs/images/         the sample results shown in this README
    data/                the cloth grid, plus the sample scenes (.json + .obj)

The `src/` directory contains *empty implementations* (stubs) of the functions
you must write. **This is the only directory you edit.** Do **not** change
`tests/`.

### Running the demo

```bash
python main.py                 # interactive viewer (polyscope) if available
python main.py --headless      # simulate headless, write OBJ frames to out/
python main.py --dense         # use the dense solver path (default is sparse)
python main.py --steps 120 --wind
python main.py data/net.json   # run one of the sample scenes
```

Any scene file can be given as the first argument. `data/cloth.json` (the
default) describes a generated grid; the rest name an `.obj` and the vertices
to pin, in the same format the original assignment used:

```json
{ "obj": "horizontal-chain.obj", "b": [1,10], "k": 5e2, "m": 1 }
```

`b` lists the pinned vertices, numbered from 1 as `.obj` numbers them. The
scenes range from two masses to nearly ten thousand:

| scene | masses | springs |
|---|---:|---:|
| `single-spring-horizontal` | 2 | 1 |
| `horizontal-chain` | 10 | 9 |
| `trap` | 56 | 61 |
| `net` | 61 | 156 |
| `eiffel` | 197 | 602 |
| `flag` | 3,200 | 9,361 |
| `shirt` | 3,713 | 11,005 |
| `skirt` | 9,840 | 29,040 |

In headless mode the backend prints energy and per-step timing and writes a
handful of `.obj` frames plus the final positions to `out/`.

The interactive viewer:

* **Click and drag any cloth vertex** to pull the cloth around — the grabbed
  vertex becomes a temporary pin at the mouse position (your precomputation
  is re-run with the extra pin and released when you let go).
* Pinned vertices are shown **silver**; the grabbed vertex turns pink.
* Keys (also available as GUI buttons):
  `[space]` pause and advance ONE step · `A` toggle the animation ·
  `R` reset · `W` toggle wind · `L` show/hide the spring network.

### Checking your work

This repo ships with two tools that could potentially be useful for working on 
this assignment: `run_tests.py` and `check_my_work.py`.

```bash
python run_tests.py                  # PASS/FAIL table + "Validated X/6"
python run_tests.py --only signed_incidence_matrix_dense   # focus on a single function
python check_my_work.py              # scores your implementation
```

`run_tests.py` tells you *what* is broken. `check_my_work.py` runs the same
checks but reports them as marks per function, so you can see where you stand
before submitting. Keep going until you see `Validated 6/6`. Note that the 
function only marks it against the public unit tests, we will also validate 
against internal examples that are not released in this repo. 

When a check fails and the message alone is not enough, look at the data it
used: [`tests/expected/`](tests/expected/INDEX.md) holds every input and
expected output the public tests compare against, written out as readable text
(and as `.png` images where the array is a picture).
You can also load the fixture directly:

```python
import numpy as np
g = np.load("tests/golden/a6_golden.npz")
print(g.files)        # every array the tests use
g["<name>"]           # one of them
```

## Sample results

A 14x14 cloth simulated with just gravity, and with wind enabled.

| `python main.py` | `python main.py --wind` |
|:---:|:---:|
| <img src="docs/images/cloth.gif" alt="a cloth pinned along its top row settling under gravity" width="360"> | <img src="docs/images/cloth-wind.gif" alt="the same cloth held in motion by wind" width="360"> |

## Background

### Read Chapter 16.5 of _Fundamentals of Computer Graphics (4th Edition)_, and ["Fast Simulation of Mass-Spring Systems" [Tiantian Liu et al. 2013]](https://www.cs.utah.edu/~ladislav/liu13fast/liu13fast.pdf).

### Mass-Spring Systems

In this assignment we'll consider animating a deformable shape.

We _model_ the shape's physical behavior by treating it as a network of [point
masses](https://en.wikipedia.org/wiki/Point_particle) and
[springs](https://en.wikipedia.org/wiki/Effective_mass_(spring–mass_system)). We
can think of our shape as a
[graph](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)) where each
vertex is a point mass and each edge is a spring.

Given _initial conditions_ (each point's starting position and starting
velocity, if any) we will create an animation following the laws of physics
forward in time. In the real world, physics is deterministic: if we know the
current state, we can be sure of what the next state will be (at least at the
scales we're considering). This will also be true of our physical simulation.

The law that we start with is Newton's second law, which states that the forces
$\mathbf{f} \in  \mathbf{R}^3$ acting on a body must equal its mass $m$ times its acceleration
$\mathbf{a}\in \mathbf{R}^3$:

$$
\mathbf{f} = m \mathbf{a}.
$$

Notice that $\mathbf{f}$ and $\mathbf{a}$ are vectors, each having a magnitude and a direction.
We will build our computational simulation by asking for this equation to be
true for each point mass  in our network. The forces $\mathbf{f}_i$ acting on the $i$-th point
mass are simply the sum of forces coming from any incident spring edge $ij$ and
any external force (such as gravity).

[Personifying](https://en.wikipedia.org/wiki/Personification) physical objects, we say
that they are _at rest_ when their potential energy is zero. When the object is
_not at rest_ then it exerts a force pushing it toward its rest state ([elastic
force](https://en.wikipedia.org/wiki/Elasticity_(physics))), decreasing its
potential energy as fast as possible. The force is the negative gradient of the potential
energy.

A simple spring is defined by its stiffness $k>0$ and _rest_ length $r_{ij} \in  \mathbf{R}$.
Its potential energy measures the squared difference of the current length and
the rest length times the stiffness:

$$
V(\mathbf{p}_i,\mathbf{p}_j) = \frac12 k( \| \mathbf{p}_i - \mathbf{p}_j\|  - r_{ij} )^2.
$$

<img src="docs/images/potential-energy.png" alt="the spring potential energy as a function of the distance between its two masses" width="420">

The force exerted by the spring on each mass is the [partial
derivative](https://en.wikipedia.org/wiki/Partial_derivative) of the potential
energy $V$ with respect to the corresponding mass position. For example, for
$\mathbf{p}_i$ we have

$$
\mathbf{f}_{ij} = -\frac{\partial V}{\partial \mathbf{p}_i} \in  \mathbf{R}^3.
$$

For now, we can postpone expanding $\partial V/\partial \mathbf{p}_i$, and just recognize that it is a
3D vector. 

Our problem is to determine _where_ all of the mass will be after a small
duration in time ($\Delta t$). 

> **Question:** What is a reasonable choice for the value of $\Delta t$ ?
>
> **Hint:** 🎞️ or 🖥️
>

We'll assume we know the current positions for each
mass $\mathbf{p}^t_i\in \mathbf{R}^3$ at the current time ($t$) and the current velocities
$\dot{\mathbf{p}}^t_i = \partial \mathbf{p}_i(t)/\partial t \in \mathbf{R}^3$. When $t=0$ then we call these the [initial
conditions](https://en.wikipedia.org/wiki/Initial_condition) of the entire
simulation. For $t\ge 0$, we can still think of these values as the initial
conditions for the remaining time.

In the real world, the trajectory of an object follows a continuous curve as a
function of time. In our simulation, we only need to know the position of each
pass at [discrete moments in
time](https://en.wikipedia.org/wiki/Discrete_time_and_continuous_time). We use
this to build discrete approximation of the time derivatives (velocities and
accelerations) that we encounter. Immediately, we can replace the current
velocties $\dot{\mathbf{p}}^t_i$ with a _backward_ [finite
difference](https://en.wikipedia.org/wiki/Finite_difference) of the positions
over the small time step:

$$
\dot{\mathbf{p}}^t_i = \frac{\mathbf{p}^t_i - \mathbf{p}^{t-\Delta t}_i}{\Delta t}
$$

where $\mathbf{p}^{t-\Delta t}_i \in  \mathbf{R}^3$ is the position at the _previous_ time.

We can also use a _central_ finite difference to define the acceleration at time
$t$:

$$
\mathbf{a}_i^t = 
\ddot{\mathbf{p}}^t_i = 
\frac{\partial ^2 \mathbf{p}_i(t)}{\partial t^2 } = 
\frac{\dot{\mathbf{p}}^{t+\Delta t}_i - \dot{\mathbf{p}}^{t}_i}{\Delta t} =
\frac{\mathbf{p}^{t+\Delta t}_i - \mathbf{p}^{t}_i}{\Delta t^2}
-\frac{\mathbf{p}^t_i - \mathbf{p}^{t-\Delta t}_i}{\Delta t^2}=
\frac{\mathbf{p}^{t+\Delta t}_i - 2 \mathbf{p}^{t}_i + \mathbf{p}^{t-\Delta t}}{\Delta t^2 }.
$$

This expression mentions our _unknown_ variables $\mathbf{p}^{t+\Delta t}_i$ for the first
time. We'll soon that based on definition of the potential spring energy above
and the acceleration here we can _solve_ for the values of these unknown
variables.

### Time integration as energy optimization

In the equation $\mathbf{f} = m \mathbf{a}$, the acceleration term $\mathbf{a}$ depends _linearly_ on the
unknowns $\mathbf{p}^{t+\Delta t}$. Unfortunately, even for a simple spring the forces $\mathbf{f} = \partial V/\partial \mathbf{p}^{t+\Delta t}$ depend _non-linearly_ on $\mathbf{p}^{t+\Delta t}$. This means we have a
_non-linear_ system of equations, which can be tricky to satisfy directly.

<!--
If we expanded this as an expression, we
might write:

$$
\frac{\partial  V(\mathbf{p}^{t+\Delta t})}{\partial  \mathbf{p}} = 
\mathbf{M} \left(
\frac{\mathbf{p}^{t+\Delta t}_i - 2 \mathbf{p}^{t}_i + \mathbf{p}^{t-\Delta t}}{\Delta t^2 }.
$$

-->

> **Question:** We've _chosen_ to define $\mathbf{f}$ as the forces that implicitly
> depend on the unknown positions $\mathbf{p}^{t+\Delta t}$ at the end of the
> time step $t+\Delta t$. What would happen if we defined the forces to explicitly
> depend on the (known) current positions $\mathbf{p}^t$?

An alternative is to view physics simulation as an optimization problem. We
will define an energy that will be minimized by the value of $\mathbf{p}^{t+\Delta t}$ that
satisfies $\mathbf{f} = m \mathbf{a}$. The minimizer $\mathbf{p}$ of some function $E(x)$ will satisfy
$\partial E/\partial \mathbf{p} = 0$. So we construct an energy $E$ such that $\partial E/\partial \mathbf{p} = \mathbf{f} - m\mathbf{a}$:

$$
\mathbf{p}^{t+\Delta t} = \mathop{\text{argmin}}_\mathbf{p}
\underbrace{
\left(\sum\limits_{ij} \frac12 k( \| \mathbf{p}_i-\mathbf{p}_j\|  - r_{ij})^2\right) +
\frac{\Delta t^2}{2} \left(\sum\limits_i m_i \left(\frac{\mathbf{p}_i - 2 \mathbf{p}^{t}_i + \mathbf{p}_i^{t-\Delta t}}{\Delta t^2 }\right)^2 \right) - 
\left(\sum\limits_i \mathbf{p}_i^\top \mathbf{f}^\text{ext}_i \right)
}_{E(\mathbf{p})}
$$

Keen observers will identify that the first term is potential energy and the
second term resembles [kinetic
energy](https://en.wikipedia.org/wiki/Kinetic_energy). Intuitively, we can see
the first term as trying to return the spring to rest length (elasticity) and
the second term as trying to keep masses [moving in the same
direction](https://en.wikipedia.org/wiki/Newton%27s_laws_of_motion#Newton%27s_first_law). 

Because of the $\| \mathbf{p}_i-\mathbf{p}_j\|  - r_{ij}$ term, minimizing $E$ is a non-linear
optimization problem. The standard approach would be to apply [gradient
descent](https://en.wikipedia.org/wiki/Gradient_descent) (slow), [Gauss-Newton
method](https://en.wikipedia.org/wiki/Gauss–Newton_algorithm), or [Newton's
Method](https://en.wikipedia.org/wiki/Newton%27s_method_in_optimization) (too
complicated for this assignment).

In a relatively recent SIGGRAPH paper ["Fast Simulation of Mass-Spring
Systems"](http://graphics.berkeley.edu/papers/Liu-FSM-2013-11/Liu-FSM-2013-11.pdf),
Tiantian Liu et al. made a neat observation that makes designing an algorithm to
minimize $E$ quite simple and fast. For each spring $ij$, they observe that the
non-linear energy can be written as a small optimization problem:

$$
(\| \mathbf{p}_i - \mathbf{p}_j\|  - r_{ij})^2  = \mathop{\text{min}}_{\mathbf{d}_{ij}\in \mathbf{R}^3,\| \mathbf{d}\|  = r_{ij}} \| (\mathbf{p}_i - \mathbf{p}_j) - \mathbf{d}_{ij}\| ^2.
$$

It may seem like we've just created extra work. We took a closed-form expression 
(left) and replaced it with an optimization problem (right). Yet this
optimization problem is small ($\mathbf{d}_{ij}$ is a single 3D vector) and can be
easily solved _independently_ (and even in parallel) for each spring (i.e.,
$\mathbf{d}_{ij}$ doesn't depend on $\mathbf{d}_{\ell k}$ etc.). Reading the right-hand side in
English it says, find the vector of length $r_{ij}$ that is as close as possible
to the current spring vector $\mathbf{p}_i - \mathbf{p}_j$. 

<img src="docs/images/dij-rij-closest-vector.png" alt="the closest vector of length r to the current spring vector d" width="460">

Now, suppose we somehow _knew already_ the vector $\mathbf{d}_{ij}$ corresponding to the
_unknown_ optimal solution $\mathbf{p}^{t+\Delta t}$, then treating $\mathbf{d}_{ij}$ as a _constant_ we could
find the optimal solution by solving the _quadratic_ optimization problem:

$$
\mathbf{p}^{t+\Delta t} = \mathop{\text{argmin}}_\mathbf{p}
\underbrace{
\left(\sum\limits_{ij} \frac12 k\| (\mathbf{p}_i-\mathbf{p}_j) - \mathbf{d}_{ij}\| ^2\right)  +
\frac{\Delta t^2}{2} \left(\sum\limits_i m_i \left(\frac{\mathbf{p}_i - 2 \mathbf{p}^{t}_i + \mathbf{p}_i^{t-\Delta t}}{\Delta t^2 }\right)^2 \right) -
\left(\sum\limits_i \mathbf{p}_i^\top \mathbf{f}^\text{ext}_i \right)
}_{\tilde{E}(\mathbf{p})}.
$$

The modified energy $\tilde{E}(\mathbf{p})$ is _quadratic_ with respect to the unknowns
$\mathbf{p}$, therefore the solution is found when we set the first derivative equal to
zero: 

$$
\frac{d\tilde{E}}{d\mathbf{p}} = 0.
$$

This leads to a straightforward "local-global" iterative algorithm:

 - Step 1 (local): Given current values of $\mathbf{p}$ determine $\mathbf{d}_{ij}$ for each
   spring.
 - Step 2 (global): Given all $\mathbf{d}_{ij}$ vectors, find positions $\mathbf{p}$ that
   minimize quadratic energy $\tilde{E}$.
 - Step 3: if "not satisfied", go to Step 1.

For the purposes of this assignment we will assume that we're "satisfied" after
a fixed number of iterations (e.g., 50). More advanced _stopping criteria_ could
(should) be employed in general.

### Matrices

The [subtext](https://en.wikipedia.org/wiki/Subtext) of this assignment is
understanding the computational aspects of large matrices. In the algorithm
above, Step 1 is easy and relies on "local" information for each spring.

Step 2 on the other hand involves all springs simultaneously.
[Matrices](https://en.wikipedia.org/wiki/Matrix_(mathematics)) are our
convenient notation for representing both the [linear
operators](https://en.wikipedia.org/wiki/Linear_operator) (e.g., in the equation
$\frac{d\tilde{E}}{d\mathbf{p}} = 0$) and the [quadratic
forms](https://en.wikipedia.org/wiki/Quadratic_form) (e.g., in the energy
$\tilde{E}$).

Let's begin by being precise about some notation. We will stack up all of the
$n$ unknown mass positions $\mathbf{p}_i \in  \mathbf{R}^3$ as the rows of a matrix $\mathbf{p}\in \mathbf{R}^{n\times 3}$.
We can do the same for the _known_ previous time steps' positions
$\mathbf{p}^{t},\mathbf{p}^{t-\Delta t}\in \mathbf{R}^{n\times 3}$.

We can then express the inertial term using matrices:

$$
\begin{align*}
\frac{\Delta t^2}{2} \left(\sum\limits_i m_i \left(\frac{\mathbf{p}_i - 2 \mathbf{p}^{t}_i + \mathbf{p}_i^{t-\Delta t}}{\Delta t^2 }\right)^2 \right) &=
\frac{1}{2\Delta t^2} \left(\sum\limits_i 
\left(\mathbf{p}_i - 2 \mathbf{p}^{t}_i + \mathbf{p}_i^{t-\Delta t}\right)^\top
m_i
\left(\mathbf{p}_i - 2 \mathbf{p}^{t}_i + \mathbf{p}_i^{t-\Delta t}\right)
\right) \\ &=
\frac{1}{2\Delta t^2} 
\mathop{\text{tr}}\left(
\left(\mathbf{p} - 2\mathbf{p}^{t} + \mathbf{p}^{t-\Delta t}\right)^\top \mathbf{M} \left(\mathbf{p} - 2\mathbf{p}^{t} + \mathbf{p}^{t-\Delta t}\right)
\right),
\end{align*}
$$

where $\mathop{\text{tr}}{\left(\mathbf{X}\right)}$ computes the [trace](https://en.wikipedia.org/wiki/Trace_(linear_algebra)) of $\mathbf{X}$ (sums up the diagonal entries: $\mathbf{X}_{11}+\mathbf{X}_{22}+\dots$).

and the entries of the square matrix $\mathbf{M}\in \mathbf{R}^{n\times n}$ are set to 

$$
\mathbf{M}_{ij} = \begin{cases} m_{i} & \text{ if $i=j$ } \\\\
0 & \text{ otherwise.} \end{cases}.
$$

The potential energy term can be similarly written with matrices. We'll start by
introducing the _signed incidence_ matrix of our mass-psring network of $n$
vertices and $m$ edges $\mathbf{A}\in \mathbf{R}^{m \times  n}$. The _rows_ of $\mathbf{A}$ correspond to an arbitrary
(but fixed) ordering of the edges in the network. In a mass-spring network, the
edges are un-oriented in the sense that the spring acts symmetrically on its
vertices. For convenience, we'll pick an orientation for edge anyway. For the
$e$-th edge $ij$, we should be sure to use the same orientation when computing
$\mathbf{d}_{ij}$ and for the following entries of $\mathbf{A}$. So, for the $e$-th row of $\mathbf{A}$
corresponding to edge connecting vertices $i$ and $j$ we'll assign values:

$$
\mathbf{A}_{ek} = \begin{cases} +1 & \text{ if $k=i$ } \\\\
-1 & \text{ else if $k==j$ } \\\\
0 & \text{ otherwise.} \end{cases}
$$

Using this matrix $\mathbf{A}$ as a linear operator we can compute the spring vectors for
each edge:

$$
\mathbf{v} = \mathbf{A} \mathbf{p}  \leftrightarrow  \mathbf{v}_{ij} = \mathbf{p}_i - \mathbf{p}_j.
$$

We can now write the modified potential energy of $\tilde{E}$ in matrix form:

$$
\left(\sum\limits_{ij} \frac12 k\| (\mathbf{p}_i-\mathbf{p}_j) - \mathbf{d}_{ij}\| ^2\right)  = \\\\
\frac{k}{2} \mathop{\text{tr}}{\left((\mathbf{A} \mathbf{p} - \mathbf{d})^\top (\mathbf{A} \mathbf{p} - \mathbf{d})\right)},
$$

where we stack the vector $\mathbf{d}_{ij}$ for each edge in the corresponding rows of $\mathbf{d}\in \mathbf{R}^{m \times  3}$.

Combining our two matrix expressions together we can write $\tilde{E}$ entirely
in matrix form:

$$
\begin{align*}
\tilde{E}(\mathbf{p}) &= 
\frac{k}{2} \mathop{\text{tr}}{\left((\mathbf{A} \mathbf{p} - \mathbf{d})^\top (\mathbf{A} \mathbf{p} - \mathbf{d})\right)} + 
\frac{1}{2\Delta t^2}\mathop{\text{tr}}{\left(
\left(\mathbf{p} - 2\mathbf{p}^{t} + \mathbf{p}^{t-\Delta t}\right)^\top \mathbf{M} \left(\mathbf{p} - 2\mathbf{p}^{t} + \mathbf{p}^{t-\Delta t}\right)
\right)} -
\mathop{\text{tr}}{\left(\mathbf{p}^\top \mathbf{f}^\text{ext}\right)} \\&=
\frac{1}{2} \mathop{\text{tr}}{\left( \mathbf{p}^\top (k \mathbf{A}^\top \mathbf{A} + \frac{1}{\Delta t^2 }\mathbf{M}) \mathbf{p} \right)} - \mathop{\text{tr}}{\left(\mathbf{p}^\top(k \mathbf{A}^\top \mathbf{d} + \frac{1}{\Delta t^2 }\mathbf{M} (2\mathbf{p}^t - \mathbf{p}^{t-\Delta t}) + \mathbf{f}^\text{ext})\right)} + \text{ constants }.
\end{align*}
$$

> **Question:** Why do we not bother to write out the terms that are constant with
> respect to $\mathbf{p}$?

We can clean this up by introducing a few auxiliary matrices:

$$
\begin{align*}
\mathbf{Q} &:= (k \mathbf{A}^\top \mathbf{A} + \frac{1}{\Delta t^2 }\mathbf{M}) \in  \mathbf{R}^{n\times n} \\
\mathbf{y} &:= \frac{1}{\Delta t^2 }\mathbf{M} (2\mathbf{p}^t - \mathbf{p}^{t-\Delta t}) + \mathbf{f}^\text{ext} \in  \mathbf{R}^{n\times 3} \\
\mathbf{b} &:= k \mathbf{A}^\top \mathbf{d} + \mathbf{y} \in  \mathbf{R}^{n\times 3}.
\end{align*}
$$

Now our optimization problem is neatly written as:

$$
\mathbf{p}^{t+\Delta t} = \mathop{\text{argmin}}_\mathbf{p} \frac12  \mathop{\text{tr}}{\left( \mathbf{p}^\top \mathbf{Q} \mathbf{p} \right)} - \mathop{\text{tr}}{\left(\mathbf{p}^\top \mathbf{b}\right)}.
$$

> **Recall:** The trace operator behaves very nicely when differentiating.
>
> $$\frac{\partial  \mathop{\text{tr}}{\left(\mathbf{x}^\top \mathbf{y}\right)}}{\partial  \mathbf{x}} = \mathbf{y}$$
> and 
>
> $$\frac{\partial  \frac12 \mathop{\text{tr}}{\left(\mathbf{x}^\top \mathbf{Y} \mathbf{x}\right)}}{\partial  \mathbf{x}} = \mathbf{Y} \mathbf{x}$$
>

Taking a derivative with respect to $\mathbf{p}$ and setting the expression to zero
reveals the minimizer of this quadratic energy:

$$
\mathbf{Q} \mathbf{p} = \mathbf{b}.
$$

Since $\mathbf{Q}$ is a square invertible matrix we can _solve_ this system, which we
often write as:

$$
\mathbf{p} = \mathbf{Q}^{-1} \mathbf{b}.
$$

#### Solving as the _action_ of multiplying by a matrix's inverse

From an algorithmic point of view the notation $\mathbf{p} = \mathbf{Q}^{-1} \mathbf{b}$ is misleading. It
might suggest first constructing `Qinv = inverse(Q)` and then conducting matrix
multiply `p = Qinv * b`. This is almost always a bad idea. Constructing `Qinv` 
be very expensive $O(n^3 )$ and numerically unstable.

Instead, we should think of the _action_ of multiplying by the inverse of a
matrix as a single "solve" operation: `p = solve(Q,b)`. Some programming
languages (such as MATLAB) indicate using operator overloading "matrix
division": `p = Q \ b`.

All good matrix libraries (including [NumPy](https://numpy.org) and
[SciPy](https://scipy.org)) will implement this "solve" action. A very common approach is to compute a 
factorization of the matrix into a 
[lower triangular matrix](https://en.wikipedia.org/wiki/Triangular_matrix)
times it's transpose:

$$
\mathbf{Q} = \mathbf{L} \mathbf{L}^\top.
$$

Finding this $\mathbf{L}$ matrix takes $O(n^3 )$ time in general.

The action of solving against a triangular matrix is simple
[forward-/back-substitution](https://en.wikipedia.org/wiki/Triangular_matrix#Forward_and_back_substitution)
and takes $O(n^2 )$ time. We can conceptually rewrite our system as 
$\mathbf{Q} \mathbf{p} = \mathbf{b}$ with $\mathbf{L} \mathbf{L}^\top \mathbf{p} = \mathbf{b}$.

A key insight of the Liu et al. paper is that our $\mathbf{Q}$ matrix is always same
(regardless of the iterations in our algorithm above and even regardless of the
time $t$ that we're computing positions for).  We can split our solve routine
into two steps: precomputation done once when the mass-spring system is loaded
in and fast substitution at run-time:

```
// Once Q is known
L = precompute_factorization(Q)
// ... each time step
// ... ... each iteration
p = back_substitution(transpose(L),forward_substitution(L,b))
```

### Sparse Matrices

For small mass spring systems, $O(n^3 )$ at loading time and $O(n^2 )$ at runtime
may be acceptable. But for even medium sized systems this will become
intractable $(n=1000 \rightarrow  n^3 =1,000,000,000.)$

Fortunately, we can avoid this worst-case behavior by observing a special
structure in our matrices. Let's start with the mass matrix $\mathbf{M} \in  \mathbf{R}^{n\times n}$. All
of the values of this matrix are zero except the diagonal. Storing this as a
general matrix we would be storing $n^2 -n$ zeros. Instead, we can acknowlede that
this matrix is [sparse](https://en.wikipedia.org/wiki/Sparse_matrix) and store
only the non-zeros along the diagonal.

Similarly, the matrix $\mathbf{A}^{m\times n}$ has $2m$ non-zeros (a $+1$ and $-1$ per edge)
and the other $mn-2m$ entries are zero. Furthermore, the result of the product $\mathbf{A}^\top\mathbf{A}$ and by
extension $\mathbf{Q} \in  \mathbf{R}^{n\times n}$ will mostly contain zeros. The number of non-zeros is
in fact $O(m + n)$. Large mass-spring systems tend to have $m=O(n)$ edges, so we
can happily think of the number of non-zeros as $O(n)$.

We've reduced the storage required from $O(n^2 )$ to $O(n)$.  What's the catch?
General (or "dense") matrices can be easily mapped to memory linearly. For a an
arbitrary sparse matrix, we need store additional information to know _where_
each non-zero entry is. The most common general approach is to stored a sorted
list of values in each column (or row) of the matrix. This is a rather awkward
data-structure to manipulate directly. Similar to the pitfalls of [bubble
sort](https://en.wikipedia.org/wiki/Insertion_sort), inserting values one at a
time can be quite slow since we'd have to keep the lists sorted after each
operation. 

Because of this most sparse matrix libraries require (or prefer) to insert all
entries at once and presort non-zeros indices prefer creating the datastructure.
Friendly sparse matrix libraries like SciPy, will let us create a list list of
$(i,j,v)$ triplets for each non-zero and then insert all values
(`scipy.sparse.coo_matrix((v, (i, j)))`). 

So if our dense matrix code looked something like:

```
Afull = zero(m,n)
for each pair i j
  Afull(i,j) += v
end
```

> By convention we use `+=` instead of `=` to allow for repeated $(i,j)$ pairs
> in the list. 

then we can replace this with 

```
triplet_list = []
for each pair i j
  triplet_list.append( i, j, v)
end
Asparse = construct_from_triplets( triplet_list )
```

> **Warning:**
>
> Do not attempt to set values of a sparse matrix directly. That is, **_do
> not_** write:
>
> ```
> A_sparse(i,j) = v
> ```
>

Storing only the non-zero entries means we must rewrite all basic matrix
operations including (matrix-vector product, matrix addition, matrix-matrix
product, transposition, etc.). This is outside the scope of our assignment and
we will use SciPy's `scipy.sparse` matrices.
 
Most important to our mass spring system is the _solve action_ discussed above.
Similar to the dense case, we can precompute a factorization and use
substitution at runtime. For our sparse matrix, these steps will
be $O(n^{\approx 1.5})$, with substitution faster and nearly $O(n)$.

### Pinned Vertices

Subject to the external force of gravity in $\mathbf{f}^\text{ext}$ our spring networks
will just accelerate downward off the screen.

We can pin down vertices (e.g., those listed in `b`) at their intial positions,
by requiring that their corresponding positions values $\mathbf{p}_i$ are always forced
to be equal to their initial values $\mathbf{p}^\text{rest}_b$:

$$
\mathbf{p}_i = \mathbf{p}^\text{rest}_i \ \forall  i \text{ in pinned vertices}.
$$

There are various ways we can introduce this simple linear equality constraint
into the energy optimization above. For this assignment, we'll use the
easy-to-implement [penalty
method](https://en.wikipedia.org/wiki/Penalty_method). We will add an additional
quadratic energy term which is minimized when our pinning constraints are
satisfied:

$$
\frac{w}{2} \sum\limits_{i \text{ in pinned vertices}} \| \mathbf{p}_i - \mathbf{p}^\text{rest}_i \| ^2,
$$

where the $w$ should be set to some large value (e.g., `w=1e10`). We can write this in matrix form as:

$$
\frac{w}{2} \mathop{\text{tr}}{\left((\mathbf{C} \mathbf{p} - \mathbf{C} \mathbf{p}^\text{rest})^\top(\mathbf{C} \mathbf{p} - \mathbf{C} \mathbf{p}^\text{rest})\right)}  = \\\\
\frac{1}{2} \mathop{\text{tr}}{\left(\mathbf{p}^\top (w \mathbf{C}^\top \mathbf{C}) \mathbf{p}\right)} - \mathop{\text{tr}}{\left(\mathbf{p}^\top w\mathbf{C}^\top \mathbf{C} \mathbf{p}^\text{rest}\right)} + \text{constant}
$$

where $\mathbf{C} \in \mathbf{R}^{|\text{pinned}| \times  n}$ has one row per pinned vertex with a
$+1$ in the corresponding column.

We can add these quadratic and linear coefficients to $\mathbf{Q}$ and $\mathbf{b}$ above correspondingly.

## Tasks

> Every assignment, including this one, will contain a **Tasks** section. This will
> enumerate all of the tasks a student will need to complete for this assignment.

> Implementations of nearly any task you're asked to implemented in this course can be found 
> online. AI can also now fairly reliably accomplish these tasts. Do not copy these and avoid 
> googling for code or using AI; instead, search the internet for explanations. Many topics 
> have relevant wikipedia articles. Use these as references. Always remember to cite any 
> references in your comments.


Implement each function in `src/`. Every file has a stub raising
`NotImplementedError`; replace it with your implementation. The unit checks in
`run_tests.py` validate each one. Write the dense versions first.

| File | Marks | What it does |
| ---- | ----: | ------------ |
| `src/signed_incidence_matrix_dense.py` | 12 | Dense signed incidence matrix `A` (`+1`/`-1` per edge). |
| `src/signed_incidence_matrix_sparse.py` | 12 | Same, returning a `scipy.sparse` matrix built from triplets. |
| `src/fast_mass_springs_precomputation_dense.py` | 19 | Rest lengths `r`, `M`, `A`, `C`, and the Cholesky factor of `Q` (dense). |
| `src/fast_mass_springs_precomputation_sparse.py` | 19 | Same using `scipy.sparse` + a sparse factorization. |
| `src/fast_mass_springs_step_dense.py` | 19 | One local-global time step (dense). |
| `src/fast_mass_springs_step_sparse.py` | 19 | One local-global time step (sparse). |

**Total: 100 marks.**

Write your dense code first. This will be simpler to debug.

At this point you should be able to run on small examples.

For example, running `python main.py data/single-spring-horizontal.json --dense`
should produce a swinging, bouncing spring:

<img src="docs/images/single-spring-horizontal.gif" alt="a single spring swinging and bouncing" width="360">

If the single spring example is not working, debug immediately before proceeding
to examples with more than one spring.

Running `python main.py data/horizontal-chain.json --dense`
will produce a hanging [catenary chain](https://en.wikipedia.org/wiki/Catenary):

<img src="docs/images/horizontal-chain.gif" alt="a chain of masses hanging in a catenary" width="400">

Running `python main.py data/net.json --dense`
will produce a hanging net:

<img src="docs/images/net.gif" alt="a net of springs hanging from six pinned corners" width="400">

If you try to run `python main.py data/flag.json --dense` you'll end up waiting
a while.

Start your sparse implementations by copying-and-pasting your correct dense
code. Remove any dense operations and construct all matrices using triplet
lists.

Now you should be able to see more complex examples, such as running
`python main.py data/flag.json` or `python main.py data/skirt.json`:

| `flag.json` | `skirt.json` |
|:---:|:---:|
| <img src="docs/images/flag.gif" alt="a flag waving in the wind" width="360"> | <img src="docs/images/skirt.gif" alt="a skirt settling under gravity" width="360"> |

### Conventions used by the checks and the backend

* The penalty weight is `w = 1e10`.
* The system matrix is `Q = k Aᵀ A + (1/Δt²) M + w Cᵀ C`.
* The local-global loop runs **50** iterations per time step.
* The auxiliary right-hand side is
  `y = (1/Δt²) M (2 Ucur - Uprev) + fext + w Cᵀ (C V)`.
* `prefactorization` is the object the precomputation returns and the step
  consumes. For the **dense** path it is `scipy.linalg.cho_factor(Q)`, solved
  with `scipy.linalg.cho_solve`. For the **sparse** path it is
  `scipy.sparse.linalg.splu(Q_csc)`, solved with `prefactorization.solve(rhs)`.

## Grading

Your `src/*.py` files are graded by the same unit checks you run locally, mapped
to the marks above, as well as additional internal examples. Submit only your 
`src/` directory (all the `.py` files inside the folder). Do not modify `tests/`.

### How your mark is computed

Each function's marks are split between two sets of tests:

| | share | what it is |
|---|---:|---|
| **public** | 30% | the tests in `tests/` that ship with this assignment — the ones `run_tests.py` and `check_my_work.py` run, whose inputs and expected outputs you can read in `tests/expected/` |
| **private** | 70% | the *same* checks run against a different set of inputs |

Both tests are run in the same way, just with different data. Note that the public
test data should be sufficient to fully test your code, the private tests are just
to avoid code that simply reproduces the published numbers but does not actually 
implement the functions asked.

### Submission

Submit your completed homework on MarkUs. Open the [MarkUs](https://markus.teach.cs.toronto.edu/markus) course
page and submit all the `.py` files in your `src/` directory under
Assignment 6: Mass Springs.

### Questions?

Direct your questions to the [Issues page of this
repository](https://github.com/panuelosj/computer-graphics-csc317-A6-Mass_Springs/issues).

### Answers?

Help your fellow students by answering questions or positions helpful tips on
[Issues page of this
repository](https://github.com/panuelosj/computer-graphics-csc317-A6-Mass_Springs/issues).
