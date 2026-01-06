import pygame
import math
import random
import tkinter as tk
from tkinter import simpledialog

def run_animation(max_circles, growth_speed):
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Анімація концентричних кіл")
    clock = pygame.time.Clock()
    CENTER = (WIDTH // 2, HEIGHT // 2)

    circles = []
    time = 0
    line_width = 2  
    pulsation_amplitude = 5  

    def add_circle():
        if len(circles) < max_circles:
            new_radius = 10
            new_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            circles.append([new_radius, new_color, growth_speed])

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        time += 0.05
        new_circles = []

        for circle in sorted(circles, key=lambda c: c[0], reverse=True):
            radius, color, speed = circle
            pulsation = pulsation_amplitude * math.sin(time)
            radius += speed + pulsation

            if radius > 500:
                continue

            pygame.draw.circle(screen, color, CENTER, int(radius), line_width)
            new_circles.append([radius, color, speed])

        circles = new_circles

        if pygame.time.get_ticks() % 5 == 0:
            add_circle()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


root = tk.Tk()
root.withdraw()  

max_circles = simpledialog.askinteger("Параметр", "Введіть кількість кіл:", minvalue=1, maxvalue=50)
growth_speed = simpledialog.askfloat("Параметр", "Швидкість росту кіл:", minvalue=0.1, maxvalue=10.0)

run_animation(max_circles, growth_speed)
