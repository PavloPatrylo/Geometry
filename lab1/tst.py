import tkinter as tk          # Імпортуємо бібліотеку Tkinter для створення GUI
from tkinter import ttk       # Імпортуємо ttk (розширені віджети Tkinter)
import threading              # Імпортуємо threading для запуску pygame у фоні
import pygame                 # Імпортуємо pygame для візуалізації поліедра
import numpy as np            # Імпортуємо numpy для роботи з масивами та векторами
import math                   # Імпортуємо math для математичних функцій

# ==== Глобальні змінні ====
current_shape = "cube"        # Поточна фігура (за замовчуванням куб)
current_angular_speed = 0     # Швидкість обертання фігури навколо осі
current_trajectory_speed = 0  # Швидкість руху осі по колу
shape_changed = True          # Прапорець, що означає: фігуру змінили в GUI


# ==== Геометрія ====
def get_vertices(shape):      # Функція повертає координати вершин вибраної фігури
    if shape == 'cube':       # Якщо вибраний куб
        return np.array([[x, y, z] for x in [-0.5, 0.5] 
                                     for y in [-0.5, 0.5] 
                                     for z in [-0.5, 0.5]], dtype=float)
    elif shape == 'tetrahedron':  # Якщо тетраедр
        s = 0.5 / np.sqrt(2)      # Обчислюємо параметр для координат
        return np.array([
            [0.5, 0, -s],         # Перша вершина
            [-0.5, 0, -s],        # Друга вершина
            [0, 0.5, s],          # Третя вершина
            [0, -0.5, s]          # Четверта вершина
        ], dtype=float)
    elif shape == 'octahedron':   # Якщо октаедр
        return np.array([
            [0.5, 0, 0],          # Вершини вздовж осей
            [-0.5, 0, 0],
            [0, 0.5, 0],
            [0, -0.5, 0],
            [0, 0, 0.5],
            [0, 0, -0.5]
        ], dtype=float)


def rotate_around_axis(vertices, y0, z0, dphi):  # Функція обертання навколо осі (y0,z0)
    cos_dphi = math.cos(dphi)    # Косинус кута обертання
    sin_dphi = math.sin(dphi)    # Синус кута обертання
    new_vertices = vertices.copy()  # Копія вершин
    new_vertices[:, 1] -= y0     # Зміщення по осі y
    new_vertices[:, 2] -= z0     # Зміщення по осі z
    y_new = new_vertices[:, 1] * cos_dphi - new_vertices[:, 2] * sin_dphi  # Нова координата y
    z_new = new_vertices[:, 1] * sin_dphi + new_vertices[:, 2] * cos_dphi  # Нова координата z
    new_vertices[:, 1] = y_new + y0  # Повертаємо зміщення
    new_vertices[:, 2] = z_new + z0
    return new_vertices            # Повертаємо обернені вершини


def get_edges(shape):              # Функція повертає список ребер для фігури
    if shape == 'cube':            # Ребра куба
        return [
            [0, 1], [0, 2], [0, 4], [1, 3], [1, 5], [2, 3], [2, 6], [3, 7],
            [4, 5], [4, 6], [5, 7], [6, 7]
        ]
    elif shape == 'tetrahedron':   # Ребра тетраедра
        return [
            [0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]
        ]
    elif shape == 'octahedron':    # Ребра октаедра
        return [
            [0, 2], [0, 3], [0, 4], [0, 5],
            [1, 2], [1, 3], [1, 4], [1, 5],
            [2, 4], [2, 5], [3, 4], [3, 5]
        ]


def create_trajectory_circle(radius=1.5, segments=64):
    # Створюємо суцільне коло
    points = []
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        y = radius * math.cos(theta)
        z = radius * math.sin(theta)
        points.append([0, y, z])  # Додаємо точку

    solid_segments = []
    for i in range(segments):
        start = points[i]
        end = points[(i + 1) % segments]
        solid_segments.append([start, end])  # Всі сегменти малюємо цілими

    return solid_segments  # Повертаємо список сегментів



def project(vertices, width, height, fov=256, distance=4, camera_theta=0, camera_phi=0):
    # Проекція 3D-точок у 2D-координати екрана
    cos_theta = math.cos(camera_theta)
    sin_theta = math.sin(camera_theta)
    cos_phi = math.cos(camera_phi)
    sin_phi = math.sin(camera_phi)

    # Матриця повороту по Y
    rot_y = np.array([
        [cos_theta, 0, sin_theta],
        [0, 1, 0],
        [-sin_theta, 0, cos_theta]
    ])
    # Матриця повороту по X
    rot_x = np.array([
        [1, 0, 0],
        [0, cos_phi, -sin_phi],
        [0, sin_phi, cos_phi]
    ])
    rot = np.dot(rot_x, rot_y)  # Загальна матриця обертання

    projected = []  # Масив 2D-точок
    for v in vertices:          # Перетворюємо кожну вершину
        v_rot = np.dot(rot, v)  # Повертаємо в просторі
        x, y, z = v_rot
        factor = fov / (distance + z) if distance + z != 0 else 0  # Масштаб залежно від глибини
        proj_x = x * factor + width / 2   # Перетворення у координати екрана
        proj_y = -y * factor + height / 2 #-y робить так, щоб вгору в 3D відповідав вверх на екрані, а не вниз.
        projected.append((int(proj_x), int(proj_y)))  # Додаємо точку
    return projected


def run_pygame(radius=1.5):   # Основний цикл pygame
    global current_shape, current_angular_speed, current_trajectory_speed, shape_changed

    pygame.init()             # Ініціалізуємо pygame
    width, height = 800, 600  # Розмір вікна
    screen = pygame.display.set_mode((width, height))  # Створюємо вікно
    pygame.display.set_caption("Polyhedron Viewer")    # Заголовок вікна
    clock = pygame.time.Clock()                       # Годинник для FPS

    vertices = get_vertices(current_shape)            # Отримуємо вершини
    edges = get_edges(current_shape)                  # Отримуємо ребра
    trajectory_circle = create_trajectory_circle(radius=radius)  # Коло для осі

    running = True
    t = 0.0                      # Час для руху по колу
    camera_theta = 0             # Кут камери навколо Y
    camera_phi = 0               # Кут камери навколо X
    mouse_dragging = False       # Чи тягнемо мишею
    last_mouse_pos = None        # Попередня позиція миші

    while running:               # Основний цикл
        for event in pygame.event.get():   # Обробка подій
            if event.type == pygame.QUIT:  # Якщо закрили вікно
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:      # Натисли ЛКМ
                    mouse_dragging = True
                    last_mouse_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:      # Відпустили ЛКМ
                    mouse_dragging = False
            elif event.type == pygame.MOUSEMOTION and mouse_dragging:  # Рух мишею
                current_pos = event.pos
                dx = current_pos[0] - last_mouse_pos[0]
                dy = current_pos[1] - last_mouse_pos[1]
                camera_theta += dx * 0.005   # Обертаємо камеру по Y
                camera_phi += dy * 0.005     # Обертаємо камеру по X
                camera_phi = max(-math.pi/2 + 0.01, min(math.pi/2 - 0.01, camera_phi))  # Обмежуємо
                last_mouse_pos = current_pos

        if shape_changed:   # Якщо змінили фігуру
            vertices = get_vertices(current_shape) # отримуємо нові вершини
            edges = get_edges(current_shape) # отримуємо нові ребра
            shape_changed = False

        screen.fill((0, 0, 0))   # Очищаємо екран чорним

        theta = 2 * math.pi * t * current_trajectory_speed  # Кут для руху по колу
        y0 = radius * math.cos(theta)  # Центр осі по y
        z0 = radius * math.sin(theta)  # Центр осі по z

        vertices = rotate_around_axis(vertices, y0, z0, current_angular_speed)  # Обертання фігури

        for segment in trajectory_circle:   # Малюємо пунктирне коло
            proj_segment = project(segment, width, height, camera_theta=camera_theta, camera_phi=camera_phi)
            pygame.draw.line(screen, (100, 100, 100), proj_segment[0], proj_segment[1], 1)

        projected = project(vertices, width, height, camera_theta=camera_theta, camera_phi=camera_phi)  # Проекція фігури

        for edge in edges:  # Малюємо ребра
            pygame.draw.line(screen, (255, 255, 255), projected[edge[0]], projected[edge[1]], 2) # Малюємо лінію між двома вершинами ребра (edge[0] та edge[1]) після проекції у 2D
        axis_pts = np.array([[-2, y0, z0], [2, y0, z0]], dtype=float)  # Лінія осі
        proj_axis = project(axis_pts, width, height, camera_theta=camera_theta, camera_phi=camera_phi)
        pygame.draw.line(screen, (255, 0, 0), proj_axis[0], proj_axis[1], 2)  # Червона вісь

        pygame.display.flip()  # Оновлюємо екран
        clock.tick(60)         # FPS = 60
        t += 1 / 60            # Збільшуємо час

    pygame.quit()  # Виходимо з pygame


# ==== Tkinter GUI ====
def update_shape(event=None):    # Функція зміни фігури з Combobox
    global current_shape, shape_changed
    current_shape = shape_var.get()
    shape_changed = True


def update_angular_speed(val):   # Функція зміни швидкості обертання
    global current_angular_speed
    current_angular_speed = float(val)


root = tk.Tk()                   # Створюємо вікно Tkinter
root.title("Керування поліедром")# Назва вікна

# Вибір фігури
tk.Label(root, text="Оберіть фігуру:").pack(pady=5)
shape_var = tk.StringVar(value="cube")  # Значення за замовчуванням
shape_combo = ttk.Combobox(root, textvariable=shape_var, 
                           values=["cube", "tetrahedron", "octahedron"], state="readonly")
shape_combo.bind("<<ComboboxSelected>>", update_shape) # Викликає зміну фігури
shape_combo.pack(pady=5)

# Повзунок швидкості обертання фігури
tk.Label(root, text="Швидкість обертання фігури:").pack(pady=5)
tk.Scale(root, from_=0.0, to=0.2, resolution=0.01, orient="horizontal",
         command=update_angular_speed).pack(pady=5)

# Фіксована швидкість руху осі (не змінюється користувачем)
current_trajectory_speed = 0.03  # Константа швидкості руху осі

# Запускаємо pygame у фоні в окремому потоці
threading.Thread(target=run_pygame, daemon=True).start()

root.mainloop()  # Запускаємо головний цикл Tkinter
