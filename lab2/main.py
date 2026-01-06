import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  
import os

def bump(t, amp=0.12, freq=1.0):
    return amp * np.sin(np.pi * t * freq) ** 2

def Q(u, v, P00, P10, P01, P11, amp_C0, amp_C1, amp_D0, amp_D1):
    def C0(u): return (1-u)*P00 + u*P10 + np.array([0,0,bump(u, amp=amp_C0)])
    def C1(u): return (1-u)*P01 + u*P11 + np.array([bump(u, amp=amp_C1),0,0])
    def D0(v): return (1-v)*P00 + v*P01 + np.array([bump(v, amp=amp_D0),0,0])
    def D1(v): return (1-v)*P10 + v*P11 + np.array([0,bump(v, amp=amp_D1),0])
    B = (1-u)*(1-v)*P00 + u*(1-v)*P10 + (1-u)*v*P01 + u*v*P11
    return (1-v)*C0(u) + v*C1(u) + (1-u)*D0(v) + u*D1(v) - B

# ---- Функція побудови поверхні ----
def build_surface(P00,P10,P01,P11,amp_C0,amp_C1,amp_D0,amp_D1,Nu=50,Nv=50):
    u_vals = np.linspace(0,1,Nu)
    v_vals = np.linspace(0,1,Nv)
    X = np.zeros((Nu,Nv))
    Y = np.zeros((Nu,Nv))
    Z = np.zeros((Nu,Nv))
    for i,u in enumerate(u_vals):
        for j,v in enumerate(v_vals):
            pt = Q(u,v,P00,P10,P01,P11,amp_C0,amp_C1,amp_D0,amp_D1)
            X[i,j], Y[i,j], Z[i,j] = pt
    return X, Y, Z

# ---- Головна Tkinter аплікація ----
class CoonsApp:
    def __init__(self, root):
        self.root = root
        root.title("Coons Patch Interactive")

        # ---- Параметри ----
        self.params = {
            "P00_x": tk.DoubleVar(value=0.0),
            "P00_y": tk.DoubleVar(value=0.0),
            "P00_z": tk.DoubleVar(value=0.0),
            "P10_x": tk.DoubleVar(value=1.0),
            "P10_y": tk.DoubleVar(value=0.2),
            "P10_z": tk.DoubleVar(value=0.2),
            "P01_x": tk.DoubleVar(value=0.0),
            "P01_y": tk.DoubleVar(value=1.0),
            "P01_z": tk.DoubleVar(value=0.5),
            "P11_x": tk.DoubleVar(value=1.0),
            "P11_y": tk.DoubleVar(value=1.0),
            "P11_z": tk.DoubleVar(value=0.8),
            "amp_C0": tk.DoubleVar(value=0.25),
            "amp_C1": tk.DoubleVar(value=0.12),
            "amp_D0": tk.DoubleVar(value=0.12),
            "amp_D1": tk.DoubleVar(value=0.15)
        }

        self.create_sliders()

        # ---- Кнопки ----
        btn_update = ttk.Button(root, text="Update Surface", command=self.update_surface)
        btn_update.grid(row=6, column=0, columnspan=2, sticky="we", pady=5)
        
        btn_save = ttk.Button(root, text="Save Projections", command=self.save_projections)
        btn_save.grid(row=6, column=2, columnspan=2, sticky="we", pady=5)

        self.fig = plt.figure(figsize=(7,5))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().grid(row=7, column=0, columnspan=4)
        
        self.canvas.mpl_connect("scroll_event", self.zoom)

        self.update_surface()

    def create_sliders(self):
        labels = ["P00_x","P00_y","P00_z","P10_x","P10_y","P10_z",
                  "P01_x","P01_y","P01_z","P11_x","P11_y","P11_z",
                  "amp_C0","amp_C1","amp_D0","amp_D1"]
        row = 0
        col = 0
        for lbl in labels:
            slider = tk.Scale(self.root, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL,
                              label=lbl, variable=self.params[lbl], length=200)
            slider.grid(row=row, column=col, sticky="we")
            col += 1
            if col>3:
                col=0
                row += 1

    def update_surface(self):
        P00 = np.array([self.params["P00_x"].get(), self.params["P00_y"].get(), self.params["P00_z"].get()])
        P10 = np.array([self.params["P10_x"].get(), self.params["P10_y"].get(), self.params["P10_z"].get()])
        P01 = np.array([self.params["P01_x"].get(), self.params["P01_y"].get(), self.params["P01_z"].get()])
        P11 = np.array([self.params["P11_x"].get(), self.params["P11_y"].get(), self.params["P11_z"].get()])
        amp_C0 = self.params["amp_C0"].get()
        amp_C1 = self.params["amp_C1"].get()
        amp_D0 = self.params["amp_D0"].get()
        amp_D1 = self.params["amp_D1"].get()

        X,Y,Z = build_surface(P00,P10,P01,P11,amp_C0,amp_C1,amp_D0,amp_D1)

        self.ax.clear()
        self.ax.plot_surface(X,Y,Z,rstride=1,cstride=1,linewidth=0, alpha=0.9)
        self.ax.set_xlabel('x'); self.ax.set_ylabel('y'); self.ax.set_zlabel('z')
        self.ax.set_title("Coons Patch 3D Surface")
        self.canvas.draw()

    def zoom(self, event):
        scale_factor = 1.2 if event.button == 'up' else 0.8

        xlim = np.array(self.ax.get_xlim())
        ylim = np.array(self.ax.get_ylim())
        zlim = np.array(self.ax.get_zlim())

        xcenter = np.mean(xlim)
        ycenter = np.mean(ylim)
        zcenter = np.mean(zlim)

        x_range = (xlim - xcenter) * scale_factor
        y_range = (ylim - ycenter) * scale_factor
        z_range = (zlim - zcenter) * scale_factor

        self.ax.set_xlim(xcenter + x_range)
        self.ax.set_ylim(ycenter + y_range)
        self.ax.set_zlim(zcenter + z_range)

        self.canvas.draw()


    def save_projections(self):
        import os
        P00 = np.array([self.params["P00_x"].get(), self.params["P00_y"].get(), self.params["P00_z"].get()])
        P10 = np.array([self.params["P10_x"].get(), self.params["P10_y"].get(), self.params["P10_z"].get()])
        P01 = np.array([self.params["P01_x"].get(), self.params["P01_y"].get(), self.params["P01_z"].get()])
        P11 = np.array([self.params["P11_x"].get(), self.params["P11_y"].get(), self.params["P11_z"].get()])
        amp_C0 = self.params["amp_C0"].get()
        amp_C1 = self.params["amp_C1"].get()
        amp_D0 = self.params["amp_D0"].get()
        amp_D1 = self.params["amp_D1"].get()

        X, Y, Z = build_surface(P00, P10, P01, P11, amp_C0, amp_C1, amp_D0, amp_D1)

        save_dir = os.getcwd()

        # ---- 3D поверхня ----
        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111, projection='3d')
        ax1.plot_surface(X,Y,Z,rstride=1,cstride=1,linewidth=0, alpha=0.9, cmap='viridis')
        fig1.savefig(os.path.join(save_dir, "coons_surface_3D.png"))
        plt.close(fig1)

        # ---- Проекція x=0 (yz) ----
        fig2 = plt.figure()
        plt.pcolormesh(Y, Z, Z, shading='auto', cmap='viridis')
        plt.xlabel('y'); plt.ylabel('z'); plt.title('Projection x=0 (yz)')
        plt.colorbar(label='z')
        fig2.savefig(os.path.join(save_dir, "coons_surface_x0.png"))
        plt.close(fig2)

        # ---- Проекція y=0 (xz) ----
        fig3 = plt.figure()
        plt.pcolormesh(X, Z, Z, shading='auto', cmap='viridis')
        plt.xlabel('x'); plt.ylabel('z'); plt.title('Projection y=0 (xz)')
        plt.colorbar(label='z')
        fig3.savefig(os.path.join(save_dir, "coons_surface_y0.png"))
        plt.close(fig3)

        # ---- Проекція z=0 (xy) ----
        fig4 = plt.figure()
        plt.pcolormesh(X, Y, Z, shading='auto', cmap='viridis')
        plt.xlabel('x'); plt.ylabel('y'); plt.title('Projection z=0 (xy)')
        plt.colorbar(label='z')
        fig4.savefig(os.path.join(save_dir, "coons_surface_z0.png"))
        plt.close(fig4)

        tk.messagebox.showinfo("Saved", f"Files saved in:\n{save_dir}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoonsApp(root)
    root.mainloop()
