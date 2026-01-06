import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

# --- ВІКНА ВІДСІКАННЯ З ПРІОРИТЕТАМИ ---
WINDOWS = [
    {"bounds": (50, 50, 250, 250), "priority": 1, "color": "#e74c3c", "name": "Вікно 1 (пріоритет 1)"},
    {"bounds": (150, 100, 280, 200), "priority": 2, "color": "#3498db", "name": "Вікно 2 (пріоритет 2)"},
    {"bounds": (80, 150, 220, 270), "priority": 3, "color": "#f39c12", "name": "Вікно 3 (пріоритет 3)"},
]

# Коди для алгоритму Коена-Сазерленда
INSIDE = 0  # 0000
LEFT   = 1  # 0001
RIGHT  = 2  # 0010
BOTTOM = 4  # 0100
TOP    = 8  # 1000

class ClipperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Алгоритми відсікання відрізків з множинними вікнами")
        self.root.configure(bg="#f0f0f0")
        
        self.drawing_mode = False
        self.current_line_start = None
        self.temp_line = None
        self.user_lines = []
        self.show_original = tk.BooleanVar(value=True)
        self.show_windows = tk.BooleanVar(value=True)
        self.show_steps = tk.BooleanVar(value=True)
        self.max_random_lines = tk.IntVar(value=5)
        self.animation_speed = tk.IntVar(value=500)
        self.use_multiple_windows = tk.BooleanVar(value=False)
        
        self.setup_ui()

    def setup_ui(self):
        # Верхня панель
        control_frame = tk.Frame(self.root, bg="#2c3e50", pady=10)
        control_frame.pack(fill=tk.X)
        
        title_label = tk.Label(control_frame, text=" Відсікання відрізків з пріоритетними вікнами", 
                               font=("Segoe UI", 14, "bold"), bg="#2c3e50", fg="white")
        title_label.pack(pady=(0, 10))
        
        # Кнопки
        btn_frame = tk.Frame(control_frame, bg="#2c3e50")
        btn_frame.pack()
        
        btn_style = {"font": ("Segoe UI", 10), "padx": 15, "pady": 8, "relief": tk.FLAT, "cursor": "hand2"}
        
        tk.Button(btn_frame, text=" Випадкові відрізки", 
                 command=self.run_demo, bg="#3498db", fg="white", 
                 activebackground="#2980b9", **btn_style).pack(side=tk.LEFT, padx=5)
        
        self.btn_draw = tk.Button(btn_frame, text=" Малювати", 
                                  command=self.toggle_drawing_mode, bg="#27ae60", fg="white",
                                  activebackground="#229954", **btn_style)
        self.btn_draw.pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text=" Очистити", 
                 command=self.clear_all, bg="#e74c3c", fg="white",
                 activebackground="#c0392b", **btn_style).pack(side=tk.LEFT, padx=5)
        
        # Налаштування
        settings_frame = tk.Frame(control_frame, bg="#2c3e50")
        settings_frame.pack(pady=10)
        
        chk_style = {"font": ("Segoe UI", 9), "bg": "#2c3e50", "fg": "white", 
                     "selectcolor": "#34495e", "activebackground": "#2c3e50"}
        
        tk.Checkbutton(settings_frame, text="Показувати оригінал", 
                      variable=self.show_original, command=self.update_display, **chk_style).pack(side=tk.LEFT, padx=10)
        
        tk.Checkbutton(settings_frame, text="Показувати вікна", 
                      variable=self.show_windows, command=self.update_display, **chk_style).pack(side=tk.LEFT, padx=10)
        
        # tk.Checkbutton(settings_frame, text="Показувати кроки", 
        #               variable=self.show_steps, **chk_style).pack(side=tk.LEFT, padx=10)
        
        tk.Checkbutton(settings_frame, text="Множинні вікна", 
                      variable=self.use_multiple_windows, command=self.update_display, **chk_style).pack(side=tk.LEFT, padx=10)
        
        # Слайдери
        slider_frame = tk.Frame(control_frame, bg="#2c3e50")
        slider_frame.pack(pady=5)
        
        tk.Label(slider_frame, text="Відрізків:", font=("Segoe UI", 9), 
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Scale(slider_frame, from_=1, to=20, orient=tk.HORIZONTAL,
                variable=self.max_random_lines, length=150,
                bg="#34495e", fg="white", highlightthickness=0).pack(side=tk.LEFT, padx=5)
        
        # Основна область
        canvas_container = tk.Frame(self.root, bg="#ecf0f1")
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.canvases = []
        titles = ["4.1 Простий алгоритм", "4.2 Коен-Сазерленд", "4.3 Середня точка"]
        colors = ["#e8f4f8", "#fff4e6", "#f0e6ff"]
        
        for i in range(3):
            frame = tk.Frame(canvas_container, bg=colors[i], relief=tk.RAISED, borderwidth=2)
            frame.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.BOTH)
            
            tk.Label(frame, text=titles[i], font=("Segoe UI", 11, "bold"), 
                    bg=colors[i], fg="#2c3e50").pack(pady=(10, 5))
            
            canvas = tk.Canvas(frame, width=320, height=320, bg="white", 
                             highlightthickness=1, highlightbackground="#bdc3c7")
            canvas.pack(padx=10, pady=(0, 10))
            self.canvases.append(canvas)
            
            canvas.bind("<Button-1>", self.on_canvas_click)
            canvas.bind("<Motion>", self.on_canvas_motion)
        
        # Статус і легенда
        status_frame = tk.Frame(self.root, bg="#34495e")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = tk.Label(status_frame, text="Готово", 
                                   font=("Segoe UI", 9), bg="#34495e", fg="white", 
                                   anchor=tk.W, padx=10, pady=5)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        legend_frame = tk.Frame(status_frame, bg="#34495e")
        legend_frame.pack(side=tk.RIGHT, padx=10)
        
        legend_items = [
            ("Повністю видимі", "#27ae60"),
            ("Частково видимі", "#f39c12"),
            ("Невидимі", "#e74c3c"),
            ("Оригінал", "#bdc3c7")
        ]
        
        for text, color in legend_items:
            frame = tk.Frame(legend_frame, bg="#34495e")
            frame.pack(side=tk.LEFT, padx=5)
            tk.Canvas(frame, width=15, height=15, bg=color, highlightthickness=1, 
                     highlightbackground="white").pack(side=tk.LEFT, padx=2)
            tk.Label(frame, text=text, font=("Segoe UI", 8), 
                    bg="#34495e", fg="white").pack(side=tk.LEFT)

    def toggle_drawing_mode(self):
        self.drawing_mode = not self.drawing_mode
        if self.drawing_mode:
            self.btn_draw.config(bg="#f39c12", text="✏️ Малювання активне")
            self.status_bar.config(text="Клікніть для початку відрізка")
        else:
            self.btn_draw.config(bg="#27ae60", text="✏️ Малювати")
            self.status_bar.config(text="Готово")
            self.current_line_start = None
            if self.temp_line:
                self.canvases[0].delete(self.temp_line)
                self.temp_line = None

    def on_canvas_click(self, event):
        if not self.drawing_mode:
            return
        
        canvas = event.widget
        
        if self.current_line_start is None:
            self.current_line_start = (event.x, event.y, canvas)
            self.status_bar.config(text="Клікніть для кінця відрізка")
        else:
            if self.current_line_start[2] == canvas:
                line = ((self.current_line_start[0], self.current_line_start[1]), (event.x, event.y))
                self.user_lines.append(line)
                
                if self.temp_line:
                    self.current_line_start[2].delete(self.temp_line)
                    self.temp_line = None
                
                self.current_line_start = None
                self.status_bar.config(text=f"Відрізок додано | Всього: {len(self.user_lines)}")
                self.update_display()

    def on_canvas_motion(self, event):
        if not self.drawing_mode or self.current_line_start is None:
            return
        
        canvas = event.widget
        if self.current_line_start[2] == canvas:
            if self.temp_line:
                canvas.delete(self.temp_line)
            self.temp_line = canvas.create_line(
                self.current_line_start[0], self.current_line_start[1],
                event.x, event.y, fill="#95a5a6", width=1, dash=(4, 4)
            )

    def clear_all(self):
        self.user_lines = []
        self.current_line_start = None
        if self.temp_line and self.current_line_start:
            self.current_line_start[2].delete(self.temp_line)
            self.temp_line = None
        self.update_display()
        self.status_bar.config(text="Очищено")

    def run_demo(self):
        num_lines = self.max_random_lines.get()
        self.user_lines = []
        for _ in range(num_lines):
            x1, y1 = random.randint(0, 320), random.randint(0, 320)
            x2, y2 = random.randint(0, 320), random.randint(0, 320)
            self.user_lines.append(((x1, y1), (x2, y2)))
        
        self.status_bar.config(text=f"Згенеровано {len(self.user_lines)} відрізків")
        self.update_display()

    def update_display(self):
        for canvas in self.canvases:
            canvas.delete("all")
            
            # Малюємо вікна відсікання
            if self.show_windows.get():
                if self.use_multiple_windows.get():
                    for window in WINDOWS:
                        x1, y1, x2, y2 = window["bounds"]
                        canvas.create_rectangle(x1, y1, x2, y2, 
                                              outline=window["color"], width=2, dash=(5, 3))
                        canvas.create_text(x1+5, y1+5, text=f"P{window['priority']}", 
                                         anchor="nw", fill=window["color"], 
                                         font=("Segoe UI", 8, "bold"))
                else:
                    x1, y1, x2, y2 = WINDOWS[0]["bounds"]
                    canvas.create_rectangle(x1, y1, x2, y2, 
                                          outline=WINDOWS[0]["color"], width=2, dash=(5, 3))
        
        if not self.user_lines:
            return
        
        # Обробка для кожного алгоритму
        self.process_lines(self.canvases[0], self.user_lines, SimpleClipper.clip)
        self.process_lines(self.canvases[1], self.user_lines, CohenSutherlandClipper.clip)
        self.process_lines(self.canvases[2], self.user_lines, MidpointClipper.clip)

    def process_lines(self, canvas, lines, clip_func):
        visible_count = 0
        invisible_count = 0
        partial_count = 0
        
        windows = WINDOWS if self.use_multiple_windows.get() else [WINDOWS[0]]
        
        for (p1, p2) in lines:
            # Малюємо оригінал
            if self.show_original.get():
                canvas.create_line(p1[0], p1[1], p2[0], p2[1], 
                                 fill="#bdc3c7", width=1, dash=(2, 2))
            
            # Обробка з пріоритетом вікон
            clipped = False
            for window in sorted(windows, key=lambda w: w["priority"]):
                x_min, y_min, x_max, y_max = window["bounds"]
                
                # Перша ітерація: перевірка повної видимості
                if (x_min <= p1[0] <= x_max and y_min <= p1[1] <= y_max and
                    x_min <= p2[0] <= x_max and y_min <= p2[1] <= y_max):
                    # Повністю видимий
                    canvas.create_line(p1[0], p1[1], p2[0], p2[1], 
                                     fill="#27ae60", width=3)
                    for x, y in [p1, p2]:
                        canvas.create_oval(x-3, y-3, x+3, y+3, 
                                         fill="#2ecc71", outline="#27ae60")
                    visible_count += 1
                    clipped = True
                    break
                
                # Перевірка повної невидимості
                if ((p1[0] < x_min and p2[0] < x_min) or 
                    (p1[0] > x_max and p2[0] > x_max) or
                    (p1[1] < y_min and p2[1] < y_min) or 
                    (p1[1] > y_max and p2[1] > y_max)):
                    # Повністю невидимий (показуємо червоним якщо показуються кроки)
                    if self.show_steps.get():
                        canvas.create_line(p1[0], p1[1], p2[0], p2[1], 
                                         fill="#e74c3c", width=1, dash=(1, 3))
                    continue
                
                # Часткова видимість - застосовуємо алгоритм відсікання
                result = clip_func(p1[0], p1[1], p2[0], p2[1], 
                                  x_min, y_min, x_max, y_max)
                
                if result:
                    rx1, ry1, rx2, ry2 = result
                    canvas.create_line(rx1, ry1, rx2, ry2, 
                                     fill="#f39c12", width=3)
                    for x, y in [(rx1, ry1), (rx2, ry2)]:
                        canvas.create_oval(x-3, y-3, x+3, y+3, 
                                         fill="#f39c12", outline="#e67e22")
                    partial_count += 1
                    clipped = True
                    break
            
            if not clipped:
                invisible_count += 1


# --- АЛГОРИТМИ ---
class SimpleClipper:
    @staticmethod
    def clip(x1, y1, x2, y2, x_min, y_min, x_max, y_max):
        if (x_min <= x1 <= x_max and y_min <= y1 <= y_max and
            x_min <= x2 <= x_max and y_min <= y2 <= y_max):
            return (x1, y1, x2, y2)
        return CohenSutherlandClipper.clip(x1, y1, x2, y2, x_min, y_min, x_max, y_max)


class CohenSutherlandClipper:
    @staticmethod
    def compute_code(x, y, x_min, y_min, x_max, y_max):
        code = INSIDE
        if x < x_min: code |= LEFT
        elif x > x_max: code |= RIGHT
        if y < y_min: code |= BOTTOM
        elif y > y_max: code |= TOP
        return code

    @staticmethod
    def clip(x1, y1, x2, y2, x_min, y_min, x_max, y_max):
        code1 = CohenSutherlandClipper.compute_code(x1, y1, x_min, y_min, x_max, y_max)
        code2 = CohenSutherlandClipper.compute_code(x2, y2, x_min, y_min, x_max, y_max)
        accept = False

        while True:
            if code1 == 0 and code2 == 0:
                accept = True
                break
            elif (code1 & code2) != 0:
                break
            else:
                code_out = code1 if code1 != 0 else code2

                if code_out & TOP:
                    x = x1 + (x2 - x1) * (y_max - y1) / (y2 - y1)
                    y = y_max
                elif code_out & BOTTOM:
                    x = x1 + (x2 - x1) * (y_min - y1) / (y2 - y1)
                    y = y_min
                elif code_out & RIGHT:
                    y = y1 + (y2 - y1) * (x_max - x1) / (x2 - x1)
                    x = x_max
                elif code_out & LEFT:
                    y = y1 + (y2 - y1) * (x_min - x1) / (x2 - x1)
                    x = x_min

                if code_out == code1:
                    x1, y1 = x, y
                    code1 = CohenSutherlandClipper.compute_code(x1, y1, x_min, y_min, x_max, y_max)
                else:
                    x2, y2 = x, y
                    code2 = CohenSutherlandClipper.compute_code(x2, y2, x_min, y_min, x_max, y_max)

        if accept:
            return (x1, y1, x2, y2)
        return None


class MidpointClipper:
    @staticmethod
    def clip(x1, y1, x2, y2, x_min, y_min, x_max, y_max):
        def is_visible(x, y):
            return x_min <= x <= x_max and y_min <= y <= y_max

        if is_visible(x1, y1) and is_visible(x2, y2):
            return (x1, y1, x2, y2)
            
        if ((x1 < x_min and x2 < x_min) or (x1 > x_max and x2 > x_max) or
            (y1 < y_min and y2 < y_min) or (y1 > y_max and y2 > y_max)):
            return None

        if abs(x1 - x2) < 1 and abs(y1 - y2) < 1:
            if is_visible(x1, y1): 
                return (x1, y1, x1, y1)
            return None

        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        
        res1 = MidpointClipper.clip(x1, y1, xm, ym, x_min, y_min, x_max, y_max)
        res2 = MidpointClipper.clip(xm, ym, x2, y2, x_min, y_min, x_max, y_max)
        
        if res1 and res2:
            return (res1[0], res1[1], res2[2], res2[3])
        elif res1:
            return res1
        elif res2:
            return res2
        return None


if __name__ == "__main__":
    root = tk.Tk()
    app = ClipperApp(root)
    root.mainloop() 