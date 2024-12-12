import tkinter as tk
from PIL import Image, ImageTk

class Etat:
    def __init__(self, libres, sur, surtable, braslibre, tenu):
        self.libres = set(libres)
        self.sur = dict(sur)
        self.surtable = set(surtable)
        self.braslibre = braslibre
        self.tenu = tenu

    def tenir(self, cube):
        if self.braslibre and cube in self.libres:
            self.braslibre = False
            self.tenu = cube
            self.libres.remove(cube)
            if cube in self.surtable:
                self.surtable.remove(cube)
            elif cube in self.sur:
                below = self.sur[cube]
                self.libres.add(below)
                del self.sur[cube]
            return True
        return False

    def poser(self, cube, target):
        if self.tenu == cube:
            if target == "table":
                self.surtable.add(cube)
            else:
                self.sur[cube] = target
                self.libres.remove(target)
            self.braslibre = True
            self.tenu = None
            self.libres.add(cube)
            return True
        return False


class AnimatedCubeWorld:
    def __init__(self, master):
        self.master = master
        self.master.title("Animated Cube World")
        self.master.geometry("600x400")
        self.canvas = tk.Canvas(master, width=600, height=400, bg="white")
        self.canvas.pack()

        # Add table image
        self.table_image = ImageTk.PhotoImage(Image.open("table.png"))  # Load your table image
        self.canvas.create_image(300, 350, image=self.table_image, anchor="s")  # Place table at bottom center

        # Logical state
        self.state = Etat(
            libres=["a", "b", "c"],
            sur={},
            surtable=["a", "b", "c"],
            braslibre=True,
            tenu=None
        )

        # Draw cubes and labels
        self.cubes = {
            "a": self.canvas.create_rectangle(100, 300, 150, 350, fill="gray", outline="black"),
            "b": self.canvas.create_rectangle(200, 300, 250, 350, fill="gray", outline="black"),
            "c": self.canvas.create_rectangle(300, 300, 350, 350, fill="gray", outline="black"),
        }
        self.labels = {
            "a": self.canvas.create_text(125, 325, text="A", fill="black", font=("Arial", 14)),
            "b": self.canvas.create_text(225, 325, text="B", fill="black", font=("Arial", 14)),
            "c": self.canvas.create_text(325, 325, text="C", fill="black", font=("Arial", 14)),
        }

        # Load robot hand image
        self.hand_image = ImageTk.PhotoImage(Image.open("robot_hand.png"))  # Load your robot hand image
        self.hand = self.canvas.create_image(300, 50, image=self.hand_image)

        # Buttons for actions
        self.frame = tk.Frame(master, bg="white")
        self.frame.pack()
        tk.Button(self.frame, text="Tenir A", command=lambda: self.action_tenir("a"), bg="gray", fg="white").pack(side="left")
        tk.Button(self.frame, text="Tenir B", command=lambda: self.action_tenir("b"), bg="gray", fg="white").pack(side="left")
        tk.Button(self.frame, text="Tenir C", command=lambda: self.action_tenir("c"), bg="gray", fg="white").pack(side="left")
        tk.Button(self.frame, text="Poser (Table)", command=lambda: self.action_poser("table"), bg="gray", fg="white").pack(side="left")
        tk.Button(self.frame, text="Reset", command=self.reset, bg="gray", fg="white").pack(side="left")

        # Dynamic pose buttons
        self.dynamic_buttons = tk.Frame(master, bg="white")
        self.dynamic_buttons.pack()
        self.update_dynamic_buttons()

    def action_tenir(self, cube):
        if self.state.tenir(cube):
            self.animate_hand(cube, "grab")

    def action_poser(self, target):
        if self.state.tenu:
            held_cube = self.state.tenu
            if self.state.poser(held_cube, target):
                self.animate_hand(held_cube, "release", target)

    def update_dynamic_buttons(self):
        for widget in self.dynamic_buttons.winfo_children():
            widget.destroy()

        for cube in self.state.surtable | self.state.libres:
            for target in self.state.libres:
                if cube != target:
                    button = tk.Button(
                        self.dynamic_buttons,
                        text=f"Pose {cube.upper()} on {target.upper()}",
                        command=lambda c=cube, t=target: self.action_poser(t),
                        bg="blue",
                        fg="white"
                    )
                    button.pack(side="left")

    def reset(self):
        self.state = Etat(
            libres=["a", "b", "c"],
            sur={},
            surtable=["a", "b", "c"],
            braslibre=True,
            tenu=None
        )
        self.canvas.coords(self.cubes["a"], 100, 300, 150, 350)
        self.canvas.coords(self.cubes["b"], 200, 300, 250, 350)
        self.canvas.coords(self.cubes["c"], 300, 300, 350, 350)
        self.canvas.coords(self.hand, 300, 50)
        for cube in self.labels:
            x, y, _, _ = self.canvas.coords(self.cubes[cube])
            self.canvas.coords(self.labels[cube], x + 25, y + 25)
        self.update_dynamic_buttons()

    def animate_hand(self, cube, action, target=None):
        cube_coords = self.canvas.coords(self.cubes[cube])
        hand_coords = self.canvas.coords(self.hand)

        target_x = (cube_coords[0] + cube_coords[2]) / 2
        target_y = cube_coords[1] - 50  # Move above the cube when grabbing

        if action == "grab":
            self.move_hand(hand_coords, target_x, target_y, lambda: self.grab_cube(cube))
        elif action == "release":
            self.move_hand(hand_coords, target_x, target_y, lambda: self.release_cube(cube, target))

    def move_hand(self, start_coords, target_x, target_y, callback):
        hand_x = start_coords[0]
        hand_y = start_coords[1]
        dx = (target_x - hand_x) / 20
        dy = (target_y - hand_y) / 20

        def step(count=0):
            if count < 20:
                self.canvas.move(self.hand, dx, dy)
                self.master.after(50, step, count + 1)
            else:
                callback()

        step()

    def grab_cube(self, cube):
        self.move_hand(self.canvas.coords(self.hand), *self.canvas.coords(self.cubes[cube])[:2], lambda: None)

    def release_cube(self, cube, target):
        if target == "table":
            target_x, _, _, target_y = self.canvas.coords(self.cubes[cube])
            target_y = 300  # Place cube on table level
        else:
            target_coords = self.canvas.coords(self.cubes[target])
            target_x = (target_coords[0] + target_coords[2]) / 2
            target_y = target_coords[1] - 25  # Align bottom of cube to top of target cube

        self.animate_cube_to_position(cube, target_x, target_y)
        self.update_dynamic_buttons()

    def animate_cube_to_position(self, cube, target_x, target_y):
        cube_coords = self.canvas.coords(self.cubes[cube])
        dx = (target_x - (cube_coords[0] + cube_coords[2]) / 2) / 20
        dy = (target_y - (cube_coords[1] + cube_coords[3]) / 2) / 20

        def step(count=0):
            if count < 20:
                self.canvas.move(self.cubes[cube], dx, dy)
                self.canvas.move(self.labels[cube], dx, dy)
                self.master.after(50, step, count + 1)

        step()


if __name__ == "__main__":
    root = tk.Tk()
    app = AnimatedCubeWorld(root)
    root.mainloop()
