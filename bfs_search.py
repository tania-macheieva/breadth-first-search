import math
import time
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque

def build_radial_graph(branch_lengths, cross_links=(), tree_only=False,
                        center=(500, 430), r_step=55, start_angle=90):
    nodes = {0: center}
    edges = []
    n_branches = len(branch_lengths)
    node_id = 1
    branch_node_ids = []
    for i, length in enumerate(branch_lengths):
        angle_deg = start_angle + i * (360.0 / n_branches)
        angle = math.radians(angle_deg)
        ids = []
        prev = 0
        for depth in range(1, length + 1):
            r = r_step * depth
            wiggle = 16 * math.sin(depth * 0.9 + i)
            x = center[0] + r * math.cos(angle) + wiggle * math.cos(angle + math.pi / 2)
            y = center[1] + r * math.sin(angle) + wiggle * math.sin(angle + math.pi / 2)
            nodes[node_id] = (x, y)
            edges.append((prev, node_id))
            ids.append(node_id)
            prev = node_id
            node_id += 1
        branch_node_ids.append(ids)
    if not tree_only:
        for (bi, di, bj, dj) in cross_links:
            u = branch_node_ids[bi][di]
            v = branch_node_ids[bj][dj]
            edges.append((u, v))
    return nodes, edges, branch_node_ids, node_id


def make_tree_A():
    """Дерево: 30 вершин, 29 ребер, 5 гілок (ациклічне)."""
    nodes, edges, branches, n = build_radial_graph([6, 6, 5, 5, 7], tree_only=True)
    return nodes, edges, n, "Дерево (5 гілок)"


def make_graph_B():
    """Граф середнього розміру: 32 вершини, 37 ребер, 5 гілок + перехресні ребра."""
    cross = [(0, 5, 1, 5), (2, 4, 3, 4), (3, 4, 4, 4), (0, 2, 1, 2), (2, 2, 3, 2)]
    nodes, edges, branches, n = build_radial_graph([6, 6, 5, 5, 7], cross_links=cross)
    extra = n
    nodes[extra] = (nodes[branches[0][-1]][0] + 40, nodes[branches[0][-1]][1] + 20)
    nodes[extra + 1] = (nodes[branches[4][-1]][0] - 30, nodes[branches[4][-1]][1] + 30)
    edges.append((branches[0][-1], extra))
    edges.append((branches[4][-1], extra + 1))
    edges.append((extra, extra + 1))
    n_total = extra + 2
    return nodes, edges, n_total, "Граф (5 гілок + цикли)"


def make_graph_C():
    """Великий граф: 53 вершини, 62 ребра, 8 гілок - для дослідження впливу розміру/порядку."""
    lengths = [7, 7, 6, 6, 7, 7, 6, 6]
    cross = [(0, 6, 1, 6), (2, 5, 3, 5), (4, 6, 5, 6), (6, 5, 7, 5),
              (0, 3, 4, 3), (1, 3, 5, 3), (2, 2, 6, 2), (3, 2, 7, 2),
              (1, 6, 2, 5), (5, 5, 6, 5)]
    nodes, edges, branches, n = build_radial_graph(lengths, cross_links=cross,
                                                     center=(520, 430), r_step=50)
    return nodes, edges, n, "Великий граф (8 гілок)"


PRESETS = {
    "tree": make_tree_A,
    "graph": make_graph_B,
    "large": make_graph_C,
}

ORDER_MODES = {
    "asc": "За зростанням id",
    "desc": "За спаданням id",
    "orig": "У порядку визначення",
    "rev": "У зворотному порядку визначення",
}

DIRECTION_MODES = {
    "undirected": "Неорієнтований (звичайний граф)",
    "outward": "Орієнтований: від центру до листя",
    "inward": "Орієнтований: від листя до центру",
}


def build_adjacency(edges, node_ids, direction_mode):
    if isinstance(node_ids, int):
        node_ids = range(node_ids)
    adj = {i: [] for i in node_ids}
    for (u, v) in edges:
        if u not in adj or v not in adj:
            continue
        if direction_mode == "undirected":
            adj[u].append(v)
            adj[v].append(u)
        elif direction_mode == "outward":
            adj[u].append(v)
        elif direction_mode == "inward":
            adj[v].append(u)
    return adj


def order_neighbors(neigh, mode):
    if mode == "asc":
        return sorted(neigh)
    if mode == "desc":
        return sorted(neigh, reverse=True)
    if mode == "rev":
        return list(reversed(neigh))
    return list(neigh)  # 'orig'


def bfs_search(adj, start, target, order_mode):
    visited = {start}
    parent = {start: None}
    q = deque([start])
    events = [("enqueue", start, None)]
    expand_order = []
    found = False
    t0 = time.perf_counter()
    while q:
        u = q.popleft()
        expand_order.append(u)
        events.append(("dequeue", u, None))
        if u == target:
            found = True
            break
        for v in order_neighbors(adj[u], order_mode):
            if v not in visited:
                visited.add(v)
                parent[v] = u
                events.append(("enqueue", v, u))
                q.append(v)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    path = []
    if found:
        cur = target
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()

    return {
        "found": found,
        "path": path,
        "events": events,
        "visited_count": len(visited),
        "expanded_count": len(expand_order),
        "time_ms": elapsed_ms,
    }

COLOR_IDLE = "#c9d6e3"
COLOR_QUEUE = "#f5d76e"
COLOR_CURRENT = "#e8743b"
COLOR_VISITED = "#8aa6c1"
COLOR_START = "#2e86de"
COLOR_TARGET = "#c0392b"
COLOR_PATH = "#27ae60"
COLOR_EDGE = "#7f8c8d"
COLOR_PATH_EDGE = "#27ae60"

NODE_R = 12


class BFSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лаб. №1 — Пошук у ширину (BFS) на графах")
        self.root.geometry("1300x900")

        self.direction_mode = tk.StringVar(value="undirected")
        self.order_mode = tk.StringVar(value="asc")
        self.preset_key = tk.StringVar(value="graph")
        self.speed_ms = tk.IntVar(value=180)
        self.instant = tk.BooleanVar(value=False)

        self.nodes = {}
        self.edges = []
        self.n_nodes = 0
        self.node_items = {}
        self.edge_items = []
        self.animating = False
        self.anim_job = None
        self._edit_first_node = None
        self._drag_node = None

        self._build_layout()
        self._load_preset()

    # ---------------------------------------------------------------- layout
    def _build_layout(self):
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True)

        # --- ліва панель керування ---
        panel = ttk.Frame(main, padding=10)
        panel.pack(side="left", fill="y")

        ttk.Label(panel, text="Керування пошуком", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        ttk.Label(panel, text="Граф (порядок і розмір):").pack(anchor="w")
        preset_names = {"tree": "Дерево (30 в., 29 р.)",
                         "graph": "Граф (32 в., 37 р.)",
                         "large": "Великий граф (53 в., 62 р.)"}
        self.preset_combo = ttk.Combobox(panel, state="readonly", width=32,
                                          values=list(preset_names.values()))
        self.preset_combo.set(preset_names["graph"])
        self.preset_combo.pack(anchor="w", pady=(0, 8))
        self._preset_name_to_key = {v: k for k, v in preset_names.items()}
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        ttk.Label(panel, text="Вид ребер:").pack(anchor="w")
        self.dir_combo = ttk.Combobox(panel, state="readonly", width=32,
                                       values=list(DIRECTION_MODES.values()))
        self.dir_combo.set(DIRECTION_MODES["undirected"])
        self.dir_combo.pack(anchor="w", pady=(0, 8))
        self._dir_name_to_key = {v: k for k, v in DIRECTION_MODES.items()}
        self.dir_combo.bind("<<ComboboxSelected>>", self._on_direction_change)

        ttk.Label(panel, text="Початкова вершина:").pack(anchor="w")
        self.start_combo = ttk.Combobox(panel, state="readonly", width=32)
        self.start_combo.pack(anchor="w", pady=(0, 8))

        ttk.Label(panel, text="Цільова вершина:").pack(anchor="w")
        self.target_combo = ttk.Combobox(panel, state="readonly", width=32)
        self.target_combo.pack(anchor="w", pady=(0, 8))

        swap_btn = ttk.Button(panel, text="⇄ Поміняти старт/ціль місцями", command=self._swap_start_target)
        swap_btn.pack(anchor="w", pady=(0, 8))

        ttk.Label(panel, text="Порядок обходу суміжних вершин:").pack(anchor="w")
        self.order_combo = ttk.Combobox(panel, state="readonly", width=32,
                                         values=list(ORDER_MODES.values()))
        self.order_combo.set(ORDER_MODES["asc"])
        self.order_combo.pack(anchor="w", pady=(0, 8))
        self._order_name_to_key = {v: k for k, v in ORDER_MODES.items()}

        ttk.Label(panel, text="Швидкість анімації (мс/крок):").pack(anchor="w")
        speed_scale = ttk.Scale(panel, from_=500, to=10, orient="horizontal",
                                 variable=self.speed_ms)
        speed_scale.pack(anchor="w", fill="x", pady=(0, 2))
        ttk.Checkbutton(panel, text="Миттєво (без анімації)", variable=self.instant).pack(anchor="w", pady=(0, 10))

        ttk.Separator(panel).pack(fill="x", pady=6)

        ttk.Button(panel, text="Побудувати / оновити граф", command=self._load_preset).pack(fill="x", pady=3)
        ttk.Button(panel, text="▶ Запустити пошук (BFS)", command=self._run_search).pack(fill="x", pady=3)
        ttk.Button(panel, text="⏹ Зупинити анімацію", command=self._stop_animation).pack(fill="x", pady=3)
        ttk.Button(panel, text="Порівняти варіанти графів", command=self._run_comparison).pack(fill="x", pady=3)
        ttk.Button(panel, text="Довідка: переваги/недоліки BFS", command=self._show_help).pack(fill="x", pady=3)

        # --- редагування графа ---
        edit_box = ttk.LabelFrame(panel, text="Редагування графа (клік по полотну)", padding=6)
        edit_box.pack(fill="x", pady=(12, 0))

        self.edit_mode = tk.StringVar(value="none")
        self._edit_mode_names = {
            "none": "Перегляд (без редагування)",
            "add_vertex": "Додати вершину (клік по пустому місцю)",
            "del_vertex": "Видалити вершину (клік по ній)",
            "add_edge": "Додати ребро (клік 2 вершини)",
            "del_edge": "Видалити ребро (клік 2 вершини)",
            "move_vertex": "Перемістити вершину (тягнути мишею)",
        }
        self.edit_mode_combo = ttk.Combobox(edit_box, state="readonly", width=30,
                                             values=list(self._edit_mode_names.values()))
        self.edit_mode_combo.set(self._edit_mode_names["none"])
        self.edit_mode_combo.pack(anchor="w", fill="x", pady=(0, 6))
        self._edit_mode_name_to_key = {v: k for k, v in self._edit_mode_names.items()}
        self.edit_mode_combo.bind("<<ComboboxSelected>>", self._on_edit_mode_change)

        self.edit_status_var = tk.StringVar(value="")
        ttk.Label(edit_box, textvariable=self.edit_status_var, wraplength=260,
                  foreground="#8a4b00").pack(anchor="w", pady=(0, 6))

        ttk.Button(edit_box, text="Новий порожній граф", command=self._new_empty_graph).pack(fill="x", pady=2)
        ttk.Button(edit_box, text="Скасувати поточний вибір", command=self._edit_reset_selection).pack(fill="x", pady=2)

        ttk.Separator(panel).pack(fill="x", pady=6)
        self.status_var = tk.StringVar(value="Готово.")
        ttk.Label(panel, textvariable=self.status_var, wraplength=260, foreground="#333").pack(anchor="w")

        legend = ttk.LabelFrame(panel, text="Умовні позначення", padding=6)
        legend.pack(fill="x", pady=(16, 0))
        self._legend_row(legend, COLOR_START, "початкова вершина")
        self._legend_row(legend, COLOR_TARGET, "цільова вершина")
        self._legend_row(legend, COLOR_QUEUE, "у черзі (виявлена)")
        self._legend_row(legend, COLOR_CURRENT, "розкривається зараз")
        self._legend_row(legend, COLOR_VISITED, "розкрита (оброблена)")
        self._legend_row(legend, COLOR_PATH, "вершина/ребро шляху")

        # --- полотно ---
        canvas_frame = ttk.Frame(main)
        canvas_frame.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=1000, height=860)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

    def _legend_row(self, parent, color, text):
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=1)
        sw = tk.Canvas(row, width=14, height=14, highlightthickness=0)
        sw.create_oval(2, 2, 12, 12, fill=color, outline="")
        sw.pack(side="left", padx=(0, 6))
        ttk.Label(row, text=text).pack(side="left")

    # ------------------------------------------------------------- callbacks
    def _on_preset_change(self, event=None):
        self._load_preset()

    def _on_direction_change(self, event=None):
        self._redraw()

    def _swap_start_target(self):
        s, t = self.start_combo.get(), self.target_combo.get()
        self.start_combo.set(t)
        self.target_combo.set(s)

    # ------------------------------------------------------------- graph mgmt
    def _load_preset(self):
        name = self.preset_combo.get()
        key = self._preset_name_to_key.get(name, "graph")
        self.nodes, self.edges, self.n_nodes, _label = PRESETS[key]()
        self.edges = [tuple(e) for e in self.edges]
        self._refresh_start_target_values(reset=True)
        self.status_var.set(f"Граф завантажено: {self.n_nodes} вершин, {len(self.edges)} ребер.")
        self._edit_reset_selection()
        self._redraw()

    def _new_empty_graph(self):
        self._stop_animation()
        self.nodes = {0: (500, 430)}
        self.edges = []
        self.n_nodes = 1
        self._refresh_start_target_values(reset=True)
        self.status_var.set("Створено порожній граф (1 вершина). Додавайте вершини й ребра в режимі редагування.")
        self._edit_reset_selection()
        self._redraw()

    def _refresh_start_target_values(self, reset=False):
        ids = sorted(self.nodes.keys())
        values = [str(i) for i in ids]
        cur_start = self.start_combo.get() if hasattr(self, "start_combo") else None
        cur_target = self.target_combo.get() if hasattr(self, "target_combo") else None
        self.start_combo["values"] = values
        self.target_combo["values"] = values
        if reset or not values:
            if values:
                self.start_combo.set(values[0])
                self.target_combo.set(values[-1])
        else:
            self.start_combo.set(cur_start if cur_start in values else values[0])
            self.target_combo.set(cur_target if cur_target in values else values[-1])

    def _current_direction_key(self):
        return self._dir_name_to_key.get(self.dir_combo.get(), "undirected")

    def _current_order_key(self):
        return self._order_name_to_key.get(self.order_combo.get(), "asc")

    # ------------------------------------------------------------- drawing
    def _redraw(self, node_colors=None, path_edges=None):
        self.canvas.delete("all")
        self.node_items = {}
        directed = self._current_direction_key() != "undirected"
        path_edge_set = set(path_edges) if path_edges else set()

        for (u, v) in self.edges:
            eu, ev = u, v
            if self._current_direction_key() == "inward":
                eu, ev = v, u
            x1, y1 = self.nodes[eu]
            x2, y2 = self.nodes[ev]
            is_path = (u, v) in path_edge_set or (v, u) in path_edge_set
            color = COLOR_PATH_EDGE if is_path else COLOR_EDGE
            width = 3 if is_path else 1.4
            kwargs = dict(fill=color, width=width)
            if directed:
                kwargs["arrow"] = tk.LAST
                kwargs["arrowshape"] = (10, 12, 4)
            self.canvas.create_line(x1, y1, x2, y2, **kwargs)

        for nid, (x, y) in self.nodes.items():
            fill = COLOR_IDLE
            outline = "#5a6b7b"
            width = 1
            if node_colors and nid in node_colors:
                fill = node_colors[nid]
            start_id = self._safe_int(self.start_combo.get())
            target_id = self._safe_int(self.target_combo.get())
            if nid == start_id:
                outline = COLOR_START
                width = 3
            if nid == target_id:
                outline = COLOR_TARGET
                width = 3
            oval = self.canvas.create_oval(x - NODE_R, y - NODE_R, x + NODE_R, y + NODE_R,
                                            fill=fill, outline=outline, width=width)
            text = self.canvas.create_text(x, y, text=str(nid), font=("Segoe UI", 8, "bold"))
            self.node_items[nid] = (oval, text)

    def _safe_int(self, s):
        try:
            return int(s)
        except (TypeError, ValueError):
            return None

    def _set_node_color(self, nid, color):
        oval, _ = self.node_items[nid]
        self.canvas.itemconfig(oval, fill=color)

    # ------------------------------------------------------------- editing
    def _on_edit_mode_change(self, event=None):
        self._edit_reset_selection()
        mode = self._current_edit_mode()
        hints = {
            "none": "",
            "add_vertex": "Клацніть по вільному місцю на полотні, щоб додати нову вершину.",
            "del_vertex": "Клацніть по вершині, щоб видалити її (разом з усіма її ребрами).",
            "add_edge": "Клацніть по першій, потім по другій вершині, щоб з'єднати їх ребром.",
            "del_edge": "Клацніть по двом вершинам існуючого ребра, щоб видалити це ребро.",
            "move_vertex": "Затисніть ліву кнопку миші на вершині й перетягніть у нове місце.",
        }
        self.edit_status_var.set(hints.get(mode, ""))

    def _current_edit_mode(self):
        return self._edit_mode_name_to_key.get(self.edit_mode_combo.get(), "none")

    def _edit_reset_selection(self):
        self._edit_first_node = None
        self._drag_node = None

    def _node_at(self, x, y, tolerance=6):
        """Повертає id вершини під курсором (з невеликим допуском), або None."""
        best_id, best_d = None, None
        for nid, (nx, ny) in self.nodes.items():
            d = math.hypot(nx - x, ny - y)
            if d <= NODE_R + tolerance and (best_d is None or d < best_d):
                best_id, best_d = nid, d
        return best_id

    def _next_free_id(self):
        return (max(self.nodes.keys()) + 1) if self.nodes else 0

    def _on_canvas_click(self, event):
        mode = self._current_edit_mode()
        if mode == "none":
            return
        x, y = event.x, event.y
        clicked = self._node_at(x, y)

        if mode == "add_vertex":
            if clicked is not None:
                self.edit_status_var.set("Тут уже є вершина. Клацніть по вільному місцю.")
                return
            new_id = self._next_free_id()
            self.nodes[new_id] = (x, y)
            self.n_nodes = len(self.nodes)
            self._refresh_start_target_values()
            self.status_var.set(f"Додано вершину {new_id}. Усього вершин: {self.n_nodes}.")
            self._redraw()

        elif mode == "del_vertex":
            if clicked is None:
                self.edit_status_var.set("Клацніть точно по вершині, яку треба видалити.")
                return
            del self.nodes[clicked]
            self.edges = [(u, v) for (u, v) in self.edges if u != clicked and v != clicked]
            self.n_nodes = len(self.nodes)
            self._refresh_start_target_values()
            self.status_var.set(f"Вершину {clicked} видалено разом з інцидентними ребрами. "
                                 f"Залишилось: {self.n_nodes} вершин, {len(self.edges)} ребер.")
            self._redraw()

        elif mode == "add_edge":
            if clicked is None:
                self.edit_status_var.set("Клацніть по вершині (не по пустому місцю).")
                return
            if self._edit_first_node is None:
                self._edit_first_node = clicked
                self.edit_status_var.set(f"Обрано вершину {clicked}. Клацніть другу вершину для ребра.")
                self._redraw(node_colors={clicked: COLOR_QUEUE})
            else:
                u = self._edit_first_node
                v = clicked
                self._edit_first_node = None
                if u == v:
                    self.edit_status_var.set("Не можна з'єднати вершину саму з собою.")
                elif (u, v) in self.edges or (v, u) in self.edges:
                    self.edit_status_var.set(f"Ребро {u}-{v} вже існує.")
                else:
                    self.edges.append((u, v))
                    self.status_var.set(f"Додано ребро {u}-{v}. Усього ребер: {len(self.edges)}.")
                self._redraw()

        elif mode == "del_edge":
            if clicked is None:
                self.edit_status_var.set("Клацніть по вершині (не по пустому місцю).")
                return
            if self._edit_first_node is None:
                self._edit_first_node = clicked
                self.edit_status_var.set(f"Обрано вершину {clicked}. Клацніть другу вершину ребра для видалення.")
                self._redraw(node_colors={clicked: COLOR_TARGET})
            else:
                u = self._edit_first_node
                v = clicked
                self._edit_first_node = None
                before = len(self.edges)
                self.edges = [e for e in self.edges if e != (u, v) and e != (v, u)]
                if len(self.edges) == before:
                    self.edit_status_var.set(f"Ребра між {u} і {v} не знайдено.")
                else:
                    self.status_var.set(f"Ребро {u}-{v} видалено. Залишилось ребер: {len(self.edges)}.")
                self._redraw()

        elif mode == "move_vertex":
            self._drag_node = clicked

    def _on_canvas_drag(self, event):
        if self._current_edit_mode() != "move_vertex" or self._drag_node is None:
            return
        self.nodes[self._drag_node] = (event.x, event.y)
        self._redraw()

    def _on_canvas_release(self, event):
        self._drag_node = None

    # ------------------------------------------------------------- search
    def _stop_animation(self):
        self.animating = False
        if self.anim_job is not None:
            try:
                self.root.after_cancel(self.anim_job)
            except Exception:
                pass
            self.anim_job = None

    def _run_search(self):
        self._stop_animation()
        start = self._safe_int(self.start_combo.get())
        target = self._safe_int(self.target_combo.get())
        if start is None or target is None:
            messagebox.showwarning("Увага", "Оберіть початкову й цільову вершини.")
            return

        if start not in self.nodes or target not in self.nodes:
            messagebox.showwarning("Увага", "Обрана вершина більше не існує в графі.")
            return

        direction = self._current_direction_key()
        order = self._current_order_key()
        self.n_nodes = len(self.nodes)
        adj = build_adjacency(self.edges, self.nodes.keys(), direction)
        result = bfs_search(adj, start, target, order)
        self._last_result = result

        self._redraw()

        if self.instant.get():
            self._apply_final_state(result)
            self._show_result_window(result, direction, order)
            return

        self.animating = True
        self._animate_events(result["events"], 0, result, direction, order)

    def _animate_events(self, events, idx, result, direction, order):
        if not self.animating:
            return
        if idx >= len(events):
            self._apply_final_state(result)
            self._show_result_window(result, direction, order)
            self.animating = False
            return

        kind, node, _parent = events[idx]
        if kind == "enqueue":
            if node not in (self._safe_int(self.start_combo.get()),):
                self._set_node_color(node, COLOR_QUEUE)
            else:
                self._set_node_color(node, COLOR_START)
        elif kind == "dequeue":
            self._set_node_color(node, COLOR_CURRENT)
            if idx > 0:
                # повернути попередню "поточну" у стан "розкрита", якщо це не старт/ціль
                pass

        # трохи згодом перефарбувати попередню "поточну" вершину в "розкрита"
        delay = 0 if self.instant.get() else max(5, int(self.speed_ms.get()))
        self.anim_job = self.root.after(delay, lambda: self._post_step(events, idx))

    def _post_step(self, events, idx):
        kind, node, _parent = events[idx]
        if kind == "dequeue":
            start_id = self._safe_int(self.start_combo.get())
            target_id = self._safe_int(self.target_combo.get())
            if node not in (start_id, target_id):
                self._set_node_color(node, COLOR_VISITED)
        self._animate_events(events, idx + 1, self._last_result,
                              self._current_direction_key(), self._current_order_key())

    def _apply_final_state(self, result):
        start_id = self._safe_int(self.start_combo.get())
        target_id = self._safe_int(self.target_combo.get())
        colors = {}
        for kind, node, _p in result["events"]:
            if node not in (start_id, target_id):
                colors[node] = COLOR_VISITED
        path_edges = []
        if result["found"]:
            path = result["path"]
            for i in range(len(path) - 1):
                path_edges.append((path[i], path[i + 1]))
            for nid in path:
                if nid not in (start_id, target_id):
                    colors[nid] = COLOR_PATH
        self._redraw(node_colors=colors, path_edges=path_edges)

    # ------------------------------------------------------------- results
    def _show_result_window(self, result, direction, order):
        win = tk.Toplevel(self.root)
        win.title("Результат пошуку в ширину (BFS)")
        win.geometry("560x520")

        frame = ttk.Frame(win, padding=14)
        frame.pack(fill="both", expand=True)

        found_text = "ЗНАЙДЕНО" if result["found"] else "НЕ ЗНАЙДЕНО"
        color = "#1e8449" if result["found"] else "#c0392b"
        ttk.Label(frame, text=f"Шлях: {found_text}", font=("Segoe UI", 14, "bold"),
                  foreground=color).pack(anchor="w")

        ttk.Separator(frame).pack(fill="x", pady=8)

        info = [
            ("Граф", self.preset_combo.get()),
            ("Вид ребер", DIRECTION_MODES[direction]),
            ("Порядок обходу сусідів", ORDER_MODES[order]),
            ("Початкова вершина", self.start_combo.get()),
            ("Цільова вершина", self.target_combo.get()),
            ("Довжина шляху (ребер)", str(len(result["path"]) - 1) if result["found"] else "—"),
            ("Кількість розкритих вершин (dequeue)", str(result["expanded_count"])),
            ("Кількість виявлених вершин (visited)", str(result["visited_count"])),
            ("Усього вершин у графі", str(self.n_nodes)),
            ("Час виконання алгоритму", f"{result['time_ms']:.4f} мс"),
        ]
        for label, value in info:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label + ":", width=32).pack(side="left", anchor="w")
            ttk.Label(row, text=value, font=("Segoe UI", 9, "bold")).pack(side="left", anchor="w")

        ttk.Separator(frame).pack(fill="x", pady=8)
        ttk.Label(frame, text="Знайдений шлях (послідовність вершин):").pack(anchor="w")
        path_str = " → ".join(map(str, result["path"])) if result["found"] else "шлях відсутній"
        txt = tk.Text(frame, height=6, wrap="word")
        txt.insert("1.0", path_str)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=False, pady=4)

        ttk.Button(frame, text="Закрити", command=win.destroy).pack(anchor="e", pady=(10, 0))

    # ------------------------------------------------------------- comparison
    def _run_comparison(self):
        order = self._current_order_key()
        start_sel = self._safe_int(self.start_combo.get())
        target_sel = self._safe_int(self.target_combo.get())

        rows = []
        for key, builder in PRESETS.items():
            nodes, edges, n, label = builder()
            s = 0 if start_sel is None or start_sel >= n else start_sel
            t = (n - 1) if target_sel is None or target_sel >= n else target_sel
            for dkey, dlabel in DIRECTION_MODES.items():
                adj = build_adjacency(edges, n, dkey)
                r = bfs_search(adj, s, t, order)
                rows.append((label, f"{n} / {len(edges)}", dlabel, s, t,
                              "так" if r["found"] else "ні",
                              (len(r["path"]) - 1) if r["found"] else "—",
                              r["expanded_count"], r["visited_count"],
                              f"{r['time_ms']:.4f}"))

        win = tk.Toplevel(self.root)
        win.title("Порівняння варіантів графів")
        win.geometry("1150x420")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        cols = ("Граф", "Верш./Ребер", "Вид ребер", "Старт", "Ціль", "Знайдено?",
                "Довж. шляху", "Розкрито", "Виявлено", "Час, мс")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=len(rows))
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110, anchor="center")
        tree.column("Граф", width=170, anchor="w")
        tree.column("Вид ребер", width=220, anchor="w")
        for row in rows:
            tree.insert("", "end", values=row)
        tree.pack(fill="both", expand=True)

        note = ("Порівняння виконано для порядку обходу сусідів: '" +
                ORDER_MODES[order] + "'. Старт/ціль обрані відповідно до поточного вибору, "
                "з корекцією індексів під розмір кожного графа.")
        ttk.Label(frame, text=note, wraplength=1100, foreground="#555").pack(anchor="w", pady=(8, 0))

    # ------------------------------------------------------------- help
    def _show_help(self):
        win = tk.Toplevel(self.root)
        win.title("Довідка: пошук у ширину (BFS)")
        win.geometry("680x560")
        frame = ttk.Frame(win, padding=14)
        frame.pack(fill="both", expand=True)

        text = (
            "ПОШУК У ШИРИНУ (BFS) — короткий опис\n\n"
            "Алгоритм розкриває вершини графа «хвилями» по рівнях відстані від "
            "початкової вершини, використовуючи чергу FIFO. Завдяки цьому BFS "
            "гарантовано знаходить найкоротший шлях (за кількістю ребер) у "
            "неваженому графі.\n\n"
            "ПЕРЕВАГИ\n"
            "  • Гарантована оптимальність шляху за кількістю ребер у неваженому графі.\n"
            "  • Простота реалізації та передбачувана складність O(V + E).\n"
            "  • Не залежить від «удачі» вибору напрямку розкриття вершин (на відміну "
            "від DFS, який може зайти у довгу неоптимальну гілку).\n"
            "  • Природно підходить для задач «найкоротший маршрут за кількістю кроків», "
            "пошуку компонент зв'язності, перевірки дворольності графа тощо.\n\n"
            "НЕДОЛІКИ\n"
            "  • Значні витрати пам'яті: потрібно зберігати чергу та множину "
            "відвіданих вершин, у гіршому випадку O(V).\n"
            "  • Не враховує ваги ребер — для зважених графів потрібні інші алгоритми "
            "(наприклад, Дейкстра).\n"
            "  • На «широких» графах з великим коефіцієнтом розгалуження досліджує "
            "значно більше вершин, ніж спрямовані (евристичні) методи, наприклад A*.\n"
            "  • На орграфах результат сильно залежить від напряму дуг: якщо всі дуги "
            "напрямлені «від старту», зворотний пошук (ціль → старт) може взагалі "
            "не знайти шляху, хоча відповідний неорієнтований граф — зв'язний.\n\n"
            "ЯК НАПРЯМ ОБХОДУ СУСІДІВ ВПЛИВАЄ НА РЕЗУЛЬТАТ\n"
            "  Порядок сканування суміжних вершин НЕ впливає на ДОВЖИНУ знайденого "
            "найкоротшого шляху (вона завжди мінімальна), але впливає на КОНКРЕТНИЙ "
            "шлях, коли існує кілька шляхів однакової довжини, а також на порядок, "
            "у якому вершини потрапляють у чергу і розкриваються.\n\n"
            "ЯК ТИП ГРАФА ВПЛИВАЄ НА РЕЗУЛЬТАТ\n"
            "  • Дерево: між будь-якими двома вершинами існує рівно один шлях — BFS "
            "завжди розкриває практично всі вершини графа (до досягнення цілі), "
            "оскільки альтернативних маршрутів немає.\n"
            "  • Граф із циклами: з'являються альтернативні (рівні за довжиною або "
            "коротші) шляхи; BFS може досягти цілі, розкривши МЕНШЕ вершин, ніж усього "
            "є у графі, якщо ціль розташована «близько» через перехресне ребро.\n"
            "  • Збільшення порядку й розміру графа (більше вершин/ребер) збільшує "
            "кількість розкритих вершин і час виконання приблизно лінійно (O(V+E)), "
            "але довжина найкоротшого шляху залежить від конкретної топології, а не "
            "прямо від розміру графа.\n"
            "  • Орграф: заміна частини ребер на односторонні дуги може як "
            "«обрізати» шлях (пошук взагалі не знаходить цілі), так і не змінити "
            "результат — залежно від того, чи збігається напрям дуг з напрямом пошуку."
        )
        txt = tk.Text(frame, wrap="word")
        txt.insert("1.0", text)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True)
        ttk.Button(frame, text="Закрити", command=win.destroy).pack(anchor="e", pady=(8, 0))


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = BFSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
