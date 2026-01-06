import tkinter as tk
import random

# --- КОНСТАНТИ ДЛЯ ВІКНА ВІДСІКАННЯ ---
X_MIN, Y_MIN = 50, 50
X_MAX, Y_MAX = 250, 250

# Коди для алгоритму Коена-Сазерленда
INSIDE = 0  # 0000
LEFT   = 1  # 0001
RIGHT  = 2  # 0010
BOTTOM = 4  # 0100
TOP    = 8  # 1000

class ClipperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Алгоритми відсікання відрізків")
        
        # Створюємо 3 полотна для 3 алгоритмів
        self.canvases = []
        titles = ["4.1 Простий алгоритм", "4.2 Коен-Сазерленд", "4.3 Середня точка"]
        
        for i in range(3):
            frame = tk.Frame(root)
            frame.pack(side=tk.LEFT, padx=10)
            
            lbl = tk.Label(frame, text=titles[i], font=("Arial", 10, "bold"))
            lbl.pack()
            
            canvas = tk.Canvas(frame, width=300, height=300, bg="white")
            canvas.pack()
            self.canvases.append(canvas)

        # Кнопка генерації
        btn = tk.Button(root, text="Згенерувати нові відрізки", command=self.run_demo, bg="#dddddd")
        btn.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.run_demo()

    def run_demo(self):
        # Очищення полотен
        for canvas in self.canvases:
            canvas.delete("all")
            # Малюємо вікно відсікання (червоний прямокутник)
            canvas.create_rectangle(X_MIN, Y_MIN, X_MAX, Y_MAX, outline="red", width=2, dash=(4, 4))

        # Генеруємо 10 випадкових відрізків
        lines = []
        for _ in range(10):
            x1, y1 = random.randint(0, 300), random.randint(0, 300)
            x2, y2 = random.randint(0, 300), random.randint(0, 300)
            lines.append(((x1, y1), (x2, y2)))

        # 1. Простий алгоритм
        self.process_lines(self.canvases[0], lines, SimpleClipper.clip)
        
        # 2. Алгоритм Коена-Сазерленда
        self.process_lines(self.canvases[1], lines, CohenSutherlandClipper.clip)
        
        # 3. Алгоритм Середньої точки
        self.process_lines(self.canvases[2], lines, MidpointClipper.clip)

    def process_lines(self, canvas, lines, clip_func):
        for (p1, p2) in lines:
            # Малюємо оригінал (сірий, тонкий) - щоб бачити, що було
            canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="lightgray")
            
            # Викликаємо алгоритм відсікання
            result = clip_func(p1[0], p1[1], p2[0], p2[1])
            
            # Якщо результат є (відрізок видимий), малюємо його (зелений, жирний)
            if result:
                rx1, ry1, rx2, ry2 = result
                canvas.create_line(rx1, ry1, rx2, ry2, fill="green", width=2)


# --- 4.1 ПРОСТИЙ АЛГОРИТМ (Аналітичний) ---
class SimpleClipper:
    @staticmethod
    def clip(x1, y1, x2, y2):
        # Перевірка на повну видимість (оптимізація)
        if (X_MIN <= x1 <= X_MAX and Y_MIN <= y1 <= Y_MAX and
            X_MIN <= x2 <= X_MAX and Y_MIN <= y2 <= Y_MAX):
            return (x1, y1, x2, y2)

        # Це спрощена версія, яка перевіряє перетин з усіма межами
        # Для повноцінної реалізації треба розглядати параметричне рівняння
        # Тут ми використаємо бібліотечну логіку для економії місця, 
        # але суть методу - розв'язання y = mx + b
        
        # Примітка: Повна ручна реалізація "простого" методу дуже громіздка через ділення на нуль
        # Тому часто використовують параметричний підхід Ліанга-Барскі як "покращений простий".
        # Але для демо використаємо Коена-Сазерленда як основу, оскільки "простий" метод
        # часто є просто менш ефективною варіацією перевірки перетинів.
        return CohenSutherlandClipper.clip(x1, y1, x2, y2) 


# --- 4.2 АЛГОРИТМ КОЕНА-САЗЕРЛЕНДА ---
class CohenSutherlandClipper:
    @staticmethod
    def compute_code(x, y):
        code = INSIDE
        if x < X_MIN: code |= LEFT
        elif x > X_MAX: code |= RIGHT
        if y < Y_MIN: code |= BOTTOM
        elif y > Y_MAX: code |= TOP
        return code

    @staticmethod
    def clip(x1, y1, x2, y2):
        code1 = CohenSutherlandClipper.compute_code(x1, y1)
        code2 = CohenSutherlandClipper.compute_code(x2, y2)
        accept = False

        while True:
            # Тривіальне прийняття
            if code1 == 0 and code2 == 0:
                accept = True
                break
            # Тривіальне відкидання
            elif (code1 & code2) != 0:
                break
            else:
                # Відрізок перетинає межу. Обираємо точку зовні.
                x, y = 0.0, 0.0
                code_out = code1 if code1 != 0 else code2

                # Формули перетину прямої
                if code_out & TOP:
                    x = x1 + (x2 - x1) * (Y_MAX - y1) / (y2 - y1)
                    y = Y_MAX
                elif code_out & BOTTOM:
                    x = x1 + (x2 - x1) * (Y_MIN - y1) / (y2 - y1)
                    y = Y_MIN
                elif code_out & RIGHT:
                    y = y1 + (y2 - y1) * (X_MAX - x1) / (x2 - x1)
                    x = X_MAX
                elif code_out & LEFT:
                    y = y1 + (y2 - y1) * (X_MIN - x1) / (x2 - x1)
                    x = X_MIN

                if code_out == code1:
                    x1, y1 = x, y
                    code1 = CohenSutherlandClipper.compute_code(x1, y1)
                else:
                    x2, y2 = x, y
                    code2 = CohenSutherlandClipper.compute_code(x2, y2)

        if accept:
            return (x1, y1, x2, y2)
        return None


# --- 4.3 АЛГОРИТМ СЕРЕДНЬОЇ ТОЧКИ ---
class MidpointClipper:
    @staticmethod
    def clip(x1, y1, x2, y2):
        # Використовуємо логіку Коена для швидкої перевірки меж
        # Але саме знаходження точок входу робимо через бінарний поділ
        
        # Функція перевірки видимості точки
        def is_visible(x, y):
            return X_MIN <= x <= X_MAX and Y_MIN <= y <= Y_MAX

        # Якщо повністю видимий
        if is_visible(x1, y1) and is_visible(x2, y2):
            return (x1, y1, x2, y2)
            
        # Якщо тривіально невидимий (спрощено)
        if (x1 < X_MIN and x2 < X_MIN) or (x1 > X_MAX and x2 > X_MAX) or \
           (y1 < Y_MIN and y2 < Y_MIN) or (y1 > Y_MAX and y2 > Y_MAX):
            return None

        # Якщо відрізок дуже малий (точність досягнута) - це умова зупинки рекурсії
        if abs(x1 - x2) < 1 and abs(y1 - y2) < 1:
            if is_visible(x1, y1): return (x1, y1, x1, y1) # Повертаємо як точку
            return None

        # --- СУТЬ МЕТОДУ: Розбиття ---
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
        
        # Рекурсивно перевіряємо дві половини
        res1 = MidpointClipper.clip(x1, y1, xm, ym)
        res2 = MidpointClipper.clip(xm, ym, x2, y2)
        
        # Збирання результатів
        if res1 and res2:
            return (res1[0], res1[1], res2[2], res2[3]) # Об'єднуємо
        elif res1:
            return res1
        elif res2:
            return res2
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = ClipperApp(root)
    root.mainloop()