import tkinter as tk
import re
from PIL import ImageGrab
import win32clipboard
from io import BytesIO

# --- Движок работы с буфером обмена Windows ---
def send_to_clipboard(image):
    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    finally: win32clipboard.CloseClipboard()

class VibePainter:
    def __init__(self, root):
        self.root = root
        self.root.title("Drawly - Mini Language IDE")
        
        # 1. Холст 800x600
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white", highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # 2. Текстовое поле для кода (Темная тема)
        self.code_text = tk.Text(root, height=15, width=95, font=("Consolas", 11), 
                                 bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
        self.code_text.pack(pady=5)
        
        # Демо-код для проверки всех функций
        demo = """bg(black)
sprite star {
  color(yellow)
  width(1)
  line(0, 10, 0, -10)
  line(-10, 0, 10, 0)
}

sprite tree {
  color(brown)
  rect_f(0, -20, 15, 40)
  color(green)
  polygon_f(-40, 0, 40, 0, 0, 60)
}

star(-200, 200)
star(150, 180, 0.5)
tree(0, -100, 1.5)
tree(150, -80)

color(white)
text(0, 250, 20, "Drawly Engine V1.0")
circle_f(-300, 200, 30) # Луна"""
        #self.code_text.insert("1.0", demo)

        # 3. Панель управления
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=10)
        
        tk.Button(btn_frame, text="🚀 Run Script", command=self.run, bg="#4ec9b0", width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="📋 Paste", command=self.paste, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🧹 Clear", command=self.clear_all, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="📸 ScreenShot", command=self.screenshot, width=15).pack(side="left", padx=5)

        self.sprites = {}
        self.draw_grid()

    def to_screen(self, x, y, dx=0, dy=0, scale=1.0):
        # Математические координаты: 0,0 в центре, Y вверх
        return (400 + dx + x * scale), (300 - (dy + y * scale))

    def draw_grid(self):
        # Координатная сетка 50x50
        for i in range(0, 801, 50):
            if i != 400:
                self.canvas.create_line(i, 0, i, 600, fill="#909090", dash=(2, 4), tags="grid")
            else:
                self.canvas.create_line(i, 0, i, 600, fill="#909090", tags="grid")
            
        for i in range(0, 601, 50):
            if i != 300:
                self.canvas.create_line(0, i, 800, i, fill="#909090", dash=(2, 4), tags="grid")
            else:
                self.canvas.create_line(0, i, 800, i, fill="#909090", tags="grid")

    def clear_all(self):
        self.canvas.delete("all")
        self.canvas.config(bg="white")
        self.draw_grid()

    def parse_and_execute(self, script, dx=0, dy=0, scale=1.0, color="black", width=1):
        pattern = r"(\w+)\s*\((.*?)\)"
        curr_color = color
        curr_width = width
        
        for match in re.finditer(pattern, script):
            cmd = match.group(1).lower()
            raw_args = match.group(2)
            
            try:
                # 1. Управление окружением
                if cmd == "bg":
                    self.canvas.config(bg=raw_args.strip().strip("'\""))
                    continue
                if cmd == "color":
                    curr_color = raw_args.strip().strip("'\"")
                    continue
                if cmd == "width":
                    curr_width = int(float(raw_args.strip()))
                    continue

                # 2. Текст (особый парсинг строки)
                if cmd == "text":
                    parts = raw_args.split(',')
                    tx, ty = self.to_screen(float(parts[0]), float(parts[1]), dx, dy, scale)
                    txt_val = parts[3].strip().strip("'\"")
                    self.canvas.create_text(tx, ty, text=txt_val, font=("Arial", int(float(parts[2])*scale)), fill=curr_color)
                    continue

                # 3. Геометрия
                args = [float(a.strip()) for a in raw_args.split(',') if a.strip() and not a.strip().startswith(('"', "'"))]

                if cmd == "line":
                    x1, y1 = self.to_screen(args[0], args[1], dx, dy, scale)
                    x2, y2 = self.to_screen(args[2], args[3], dx, dy, scale)
                    self.canvas.create_line(x1, y1, x2, y2, fill=curr_color, width=curr_width)

                elif cmd in ["circle", "circle_f"]:
                    cx, cy = self.to_screen(args[0], args[1], dx, dy, scale)
                    r = args[2] * scale
                    f = curr_color if "_f" in cmd else ""
                    self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=curr_color, fill=f, width=curr_width)

                elif cmd in ["rect", "rect_f", "oval", "oval_f"]:
                    cx, cy = self.to_screen(args[0], args[1], dx, dy, scale)
                    w, h = (args[2]*scale)/2, (args[3]*scale)/2
                    f = curr_color if "_f" in cmd else ""
                    self.canvas.create_oval(cx-w, cy-h, cx+w, cy+h, outline=curr_color, fill=f, width=curr_width) if "oval" in cmd else \
                    self.canvas.create_rectangle(cx-w, cy-h, cx+w, cy+h, outline=curr_color, fill=f, width=curr_width)

                elif cmd in ["polygon", "polygon_f"]:
                    pts = []
                    for i in range(0, len(args), 2):
                        sx, sy = self.to_screen(args[i], args[i+1], dx, dy, scale)
                        pts.extend([sx, sy])
                    f = curr_color if "_f" in cmd else ""
                    self.canvas.create_polygon(pts, outline=curr_color, fill=f, width=curr_width)

                # 4. Вызов спрайта
                elif cmd in self.sprites:
                    sx = args[0] if len(args) > 0 else 0
                    sy = args[1] if len(args) > 1 else 0
                    ss = args[2] if len(args) > 2 else 1.0
                    self.parse_and_execute(self.sprites[cmd], dx+sx, dy+sy, scale*ss, curr_color, curr_width)
            except Exception as e:
                print(f"Error in command '{cmd}({raw_args})': {e}")

    def run(self):
        txt = self.code_text.get("1.0", tk.END)
        # Парсим спрайты
        sp_pat = r"sprite\s+(\w+)\s*\{(.*?)\}"
        self.sprites = {n.lower(): b.strip() for n, b in re.findall(sp_pat, txt, re.DOTALL)}
        # Очищаем основной код и запускаем
        main_s = re.sub(sp_pat, "", txt, flags=re.DOTALL)
        self.parse_and_execute(main_s)

    def paste(self):
        try: self.code_text.insert(tk.INSERT, self.root.clipboard_get())
        except: pass

    def screenshot(self):
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        img = ImageGrab.grab(bbox=(x, y, x + 800, y + 600))
        send_to_clipboard(img)

if __name__ == "__main__":
    root = tk.Tk()
    VibePainter(root)
    root.mainloop()
