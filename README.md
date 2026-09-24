# BFS Graph Search Visualizer

A desktop application that demonstrates the **Breadth-First Search (BFS)** algorithm on explicitly defined branching graphs.

The graphs are **deterministic**: vertex coordinates are calculated from the branch angle and the radius based on the vertex depth. No randomization is used, so the graph layout remains the same between runs.

## Features

* Three predefined graphs of different sizes:

  * **Tree** — 30 vertices, 29 edges, 5 branches
  * **Graph** — 32 vertices, 37 edges, 5 branches with cross edges and cycles
  * **Large Graph** — 53 vertices, 62 edges, 8 branches
* Switch between:

  * undirected graph
  * directed graph from center to leaves
  * directed graph from leaves to center
* Select the **start** and **target** vertices.
* Choose the order in which adjacent vertices are explored:

  * ascending ID
  * descending ID
  * definition order
  * reverse definition order
* Step-by-step animated BFS visualization on a **Canvas**.
* Adjustable animation speed and instant execution mode.
* Results window showing:

  * found path
  * number of discovered and expanded vertices
  * execution time
* **Comparison mode** for running BFS on all three graphs and different edge-direction modes and displaying the results in a table.
* Help window describing the main advantages and disadvantages of BFS.

## BFS

Breadth-First Search explores a graph **level by level**, starting from the selected vertex. For an unweighted graph, BFS can find a shortest path in terms of the number of edges.

## Running the Application

Run the main application file:

```bash
python main.py
```

The exact command may differ depending on the project structure and Python environment.

## Technologies

* Python
* Tkinter
* Canvas
* BFS (Breadth-First Search)
