import tkinter as tk
import math
import random


class Particle:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.5, 2.5)
        self.radius = random.randint(3, 7)
        hue = random.randint(0, 360)
        r, g, b = self._hsl_to_rgb(hue, 80, 55)
        self.color = f"#{r:02x}{g:02x}{b:02x}"
        self.tail_color = f"#{r:02x}{g:02x}{b:02x}"
        self.shape = self.canvas.create_oval(
            x - self.radius, y - self.radius,
            x + self.radius, y + self.radius,
            fill=self.color, outline="", tags="particle"
        )

    @staticmethod
    def _hsl_to_rgb(h, s, l):
        """h in [0,360], s and l in [0,100]"""
        s /= 100.0
        l /= 100.0
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

    def move(self, w, h, time):
        self.angle += random.uniform(-0.05, 0.05)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        if self.x < -self.radius:
            self.x = w + self.radius
        elif self.x > w + self.radius:
            self.x = -self.radius
        if self.y < -self.radius:
            self.y = h + self.radius
        elif self.y > h + self.radius:
            self.y = -self.radius

        self.canvas.coords(
            self.shape,
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius
        )


class Animation:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Particle Animation")
        self.root.resizable(False, False)

        self.width = 800
        self.height = 600
        self.canvas = tk.Canvas(
            self.root, width=self.width, height=self.height,
            bg="#0a0a1e", highlightthickness=0
        )
        self.canvas.pack()

        self.particles = []
        for _ in range(80):
            p = Particle(
                self.canvas,
                random.uniform(0, self.width),
                random.uniform(0, self.height)
            )
            self.particles.append(p)

        self.time = 0
        self._update()

        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.mainloop()

    def _update(self):
        self.time += 0.02
        for p in self.particles:
            p.move(self.width, self.height, self.time)

        connections = self._draw_connections()
        self.canvas.tag_lower("connection")
        self.canvas.tag_raise("particle")
        self.root.after(30, self._update)

    def _draw_connections(self):
        self.canvas.delete("connection")
        threshold = 120
        for i, a in enumerate(self.particles):
            for b in self.particles[i + 1:]:
                dx = a.x - b.x
                dy = a.y - b.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < threshold:
                    alpha = int((1 - dist / threshold) * 60)
                    self.canvas.create_line(
                        a.x, a.y, b.x, b.y,
                        fill=f"#4488ff{alpha:02x}",
                        width=1, tags="connection"
                    )


if __name__ == "__main__":
    Animation()
