import time
import requests
import getpass
import tkinter as tk
from tkinter import ttk
import threading

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
SERVER_URL = f'http://{SERVER_HOST}:{SERVER_PORT}'

# GUI
class QueueClientGUI:
    def __init__(self, root):
        self.root = root
        root.title("Cliente RDP")
        root.geometry("540x580")
        root.minsize(500, 450)
        root.configure(bg="#2b2b2b")

        self.username = getpass.getuser()
        self.settings_window = None

        self.status_container = tk.Frame(root, bg="#2b2b2b")
        self.status_container.pack(side="bottom", fill="x")  

        self.status_label = tk.Label(self.status_container,
                                     text=f"Usuário: {self.username}",
                                     font=("Arial", 10, "bold"),
                                     bg="#2b2b2b", fg="#f0f0f0")
        self.status_label.pack(side="left", padx=10)

        self.turn_label = tk.Label(self.status_container,
                                   text="",
                                   font=("Arial", 10, "bold"),
                                   bg="#2b2b2b", fg="#28a745")
        self.turn_label.place(relx=0.5, rely=0.5, anchor="center")

        self.settings_button = tk.Button(self.status_container, text="⚙", font=("Arial", 12, "bold"),
                                         bg="#2b2b2b", fg="#f0f0f0", relief="flat",
                                         command=self.open_settings_window)
        self.settings_button.pack(side="right", padx=10)

        self.main_frame = tk.Frame(root, bg="#2b2b2b")
        self.main_frame.pack(side="top", fill="both", expand=True) 

        title_lbl = tk.Label(self.main_frame, text="Cliente RDP", font=("Arial", 18, "bold"),
                             bg="#2b2b2b", fg="#f0f0f0")
        title_lbl.pack(pady=10)

        btn_frame = tk.Frame(self.main_frame, bg="#2b2b2b")
        btn_frame.pack(pady=5)

        btn_width = 22
        button_font = ("Arial", 12, "bold")

        self.btn_enter = tk.Button(btn_frame, text="Entrar na Fila", width=btn_width,
                                   command=self.threaded_enter_queue, bg="#28a745", fg="white",
                                   font=button_font, relief="flat", activebackground="#218838")
        self.btn_enter.pack(pady=6)

        self.btn_exit = tk.Button(btn_frame, text="Sair da Fila", width=btn_width,
                                  command=self.threaded_exit_queue, bg="#e94e4e", fg="white",
                                  font=button_font, relief="flat", activebackground="#C0392B")
        self.btn_exit.pack(pady=6)

        table_frame = tk.Frame(self.main_frame, bg="#2b2b2b")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 10))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#3c3f41",
                        foreground="#f0f0f0",
                        fieldbackground="#3c3f41",
                        font=("Arial", 12),
                        rowheight=30)
        style.configure("Treeview.Heading",
                        background="#2b2b2b",
                        foreground="#f0f0f0",
                        font=("Arial", 14, "bold"))
        style.map('Treeview', background=[('selected', '#6a6d70')])

        self.tree = ttk.Treeview(table_frame, columns=("pos", "name"), show="headings", height=10)
        self.tree.heading("pos", text="Posição")
        self.tree.heading("name", text="Nome do Usuário")
        self.tree.column("pos", width=80, anchor="center")
        self.tree.column("name", anchor="center", width=400)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.update_loop_running = True
        self.update_queue_periodic_threaded()

    def threaded_enter_queue(self):
        threading.Thread(target=self.enter_queue, daemon=True).start()

    def threaded_exit_queue(self):
        threading.Thread(target=self.exit_queue, daemon=True).start()

    def open_settings_window(self):
        if self.settings_window and tk.Toplevel.winfo_exists(self.settings_window):
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Configurações do Servidor")
        self.settings_window.geometry("350x180")
        self.settings_window.configure(bg="#3c3f41")
        self.settings_window.resizable(False, False)
        self.settings_window.transient(self.root)
        self.settings_window.grab_set()

        tk.Label(self.settings_window, text="Configuração do Servidor", font=("Arial", 12, "bold"),
                 bg="#3c3f41", fg="#f0f0f0").pack(pady=(10, 15))

        input_frame = tk.Frame(self.settings_window, bg="#3c3f41")
        input_frame.pack(pady=5, padx=20, fill="x")

        tk.Label(input_frame, text="IP do Servidor:", bg="#3c3f41", fg="#f0f0f0").grid(row=0, column=0, sticky="w", pady=3)
        tk.Label(input_frame, text="Porta:", bg="#3c3f41", fg="#f0f0f0").grid(row=1, column=0, sticky="w", pady=3)

        self.host_entry = tk.Entry(input_frame)
        self.host_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.host_entry.insert(0, SERVER_HOST)

        self.port_entry = tk.Entry(input_frame)
        self.port_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0))
        self.port_entry.insert(0, str(SERVER_PORT))

        input_frame.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self.settings_window, bg="#3c3f41")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Aplicar", bg="#28a745", fg="white",
                  font=("Arial", 10, "bold"), width=10,
                  command=self.apply_settings).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Cancelar", bg="#e94e4e", fg="white",
                  font=("Arial", 10, "bold"), width=10,
                  command=self.settings_window.destroy).pack(side="right", padx=10)

    def apply_settings(self):
        global SERVER_HOST, SERVER_PORT, SERVER_URL
        host = self.host_entry.get().strip()
        try:
            port = int(self.port_entry.get())
        except ValueError:
            return
        SERVER_HOST = host
        SERVER_PORT = port
        SERVER_URL = f'http://{SERVER_HOST}:{SERVER_PORT}'
        if self.settings_window:
            self.settings_window.destroy()

    def enter_queue(self):
        payload = {'bot_id': self.username}
        try:
            r = requests.post(f'{SERVER_URL}/chegar', json=payload, timeout=1)
            data = r.json()
            pos = data.get('posicao')
            eh = data.get('eh_vez')
            if eh:
                self.turn_label.config(text="✅ É sua vez!")
            else:
                self.turn_label.config(text=f"{pos}º lugar")
        except Exception:
            self.turn_label.config(text="Erro conexão")

    def exit_queue(self):
        payload = {'bot_id': self.username}
        try:
            requests.post(f'{SERVER_URL}/saiu', json=payload, timeout=1)
            self.turn_label.config(text="")
        except Exception:
            self.turn_label.config(text="Erro conexão")

    def update_queue_periodic_threaded(self):
        threading.Thread(target=self.update_queue_periodic, daemon=True).start()

    def update_queue_periodic(self):
        while self.update_loop_running:
            try:
                r = requests.get(f'{SERVER_URL}/fila', timeout=1)
                if r.status_code == 200:
                    lista = r.json()
                    self.tree.delete(*self.tree.get_children())
                    for i, name in enumerate(lista, start=1):
                        self.tree.insert("", "end", values=(i, name))
                    if len(lista) > 0:
                        if lista[0] == self.username:
                            self.turn_label.config(text="✅ É sua vez!")
                        else:
                            pos = lista.index(self.username) + 1 if self.username in lista else "-"
                            self.turn_label.config(text=f"{pos}º lugar")
                    else:
                        self.turn_label.config(text="")
            except Exception:
                self.turn_label.config(text="")
            time.sleep(1)

    def close(self):
        self.update_loop_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = QueueClientGUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.close)
    root.mainloop()