import threading
import time
from flask import Flask, request, jsonify
import tkinter as tk
from tkinter import ttk
import socket
import requests

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
TIMEOUT = 60 

app = Flask(__name__)
fila = {}
fila_lock = threading.Lock()
flask_thread = None
flask_running = False

@app.route('/chegar', methods=['POST'])
def api_chegar():
    data = request.get_json(force=True)
    bot_id = data.get('bot_id')
    ip_usuario = request.remote_addr
    now = time.time()
    with fila_lock:
        mortos = [b for b, t in fila.items() if now - t > TIMEOUT]
        for m in mortos:
            del fila[m]
        if bot_id not in fila:
            fila[bot_id] = now
            gui.add_log(bot_id, ip_usuario, "Entrou")  
        ordem = sorted(fila.items(), key=lambda x: x[1])
        pos = [b for b, _ in ordem].index(bot_id) + 1
    return jsonify({'posicao': pos, 'eh_vez': pos == 1})

@app.route('/saiu', methods=['POST'])
def api_saiu():
    data = request.get_json(force=True)
    bot_id = data.get('bot_id')
    ip_usuario = request.remote_addr
    with fila_lock:
        if bot_id in fila:
            del fila[bot_id]
            gui.add_log(bot_id, ip_usuario, "Saiu")
    return jsonify({'ok': True})

@app.route('/fila', methods=['GET'])
def api_fila():
    with fila_lock:
        ordem = sorted(fila.items(), key=lambda x: x[1])
        lista = [b for b, _ in ordem]
    return jsonify(lista)

def run_flask():
    global flask_running
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    flask_running = True
    app.run(host=SERVER_HOST, port=SERVER_PORT, threaded=True)
    flask_running = False

def start_server():
    global flask_thread, flask_running
    if flask_running:
        return
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

def stop_server():
    global flask_running
    if flask_running:
        flask_running = False
        with fila_lock:
            fila.clear()

# GUI
class ServerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Servidor RDP's")
        root.geometry("540x550")
        root.minsize(480, 400)
        root.configure(bg="#2b2b2b")

        self.logs = []

        title_lbl = tk.Label(root, text="Servidor RDP's", font=("Arial", 18, "bold"),
                             bg="#2b2b2b", fg="#f0f0f0")
        title_lbl.pack(pady=10)

        btn_frame = tk.Frame(root, bg="#2b2b2b")
        btn_frame.pack(pady=5)

        btn_width = 22
        button_font = ("Arial", 12, "bold")

        self.btn_start = tk.Button(btn_frame, text="Iniciar Servidor", width=btn_width,
                                   command=self.start_server_gui, bg="#4a90e2", fg="white",
                                   font=button_font, relief="flat", activebackground="#357ABD")
        self.btn_start.pack(pady=6)

        self.btn_stop = tk.Button(btn_frame, text="Parar Servidor", width=btn_width,
                                  command=self.stop_server_gui, bg="#e94e4e", fg="white",
                                  font=button_font, relief="flat", activebackground="#C0392B")
        self.btn_stop.pack(pady=6)

        self.btn_clear = tk.Button(btn_frame, text="Limpar Fila", width=btn_width,
                                   command=self.clear_fila, bg="#f5a623", fg="white",
                                   font=button_font, relief="flat", activebackground="#D68910")
        self.btn_clear.pack(pady=6)

        table_frame = tk.Frame(root, bg="#2b2b2b")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

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
        self.tree.grid(row=0, column=0, sticky="nsew")

        status_container = tk.Frame(table_frame, bg="#2b2b2b")
        status_container.grid(row=1, column=0, sticky="ew", pady=5, padx=10)
        status_container.grid_columnconfigure(0, weight=1)
        status_container.grid_columnconfigure(1, weight=0)
        status_container.grid_columnconfigure(2, weight=0)

        left_frame = tk.Frame(status_container, bg="#2b2b2b")
        left_frame.grid(row=0, column=0, sticky="w")

        self.status_canvas = tk.Canvas(left_frame, width=14, height=14,
                                       bg="#2b2b2b", highlightthickness=0)
        self.status_canvas.pack(side="left", padx=(0, 5))
        self.status_label = tk.Label(left_frame, text="Parado",
                                     font=("Arial", 10, "bold"),
                                     bg="#2b2b2b", fg="#f0f0f0")
        self.status_label.pack(side="left")

        self.settings_button = tk.Button(status_container, text="⚙", font=("Arial", 12, "bold"),
                                         bg="#2b2b2b", fg="#f0f0f0", relief="flat",
                                         command=self.toggle_info_panel)
        self.settings_button.grid(row=0, column=1, sticky="e", padx=(5, 0))

        self.log_button = tk.Button(status_container, text="📄", font=("Arial", 12, "bold"),
                                    bg="#2b2b2b", fg="#f0f0f0", relief="flat",
                                    command=self.toggle_log_panel)
        self.log_button.grid(row=0, column=2, sticky="e", padx=(5, 0))

        self.info_panel = None
        self.log_panel = None

        self.update_loop_running = True
        self.update_queue_periodic()

    # janela de configuracoes
    def toggle_info_panel(self):
        if self.info_panel and self.info_panel.winfo_exists():
            self.info_panel.destroy()
            self.info_panel = None
        else:
            self.create_info_panel()

    def create_info_panel(self):
        self.info_panel = tk.Toplevel(self.root)
        self.info_panel.title("Informações do Servidor")
        self.info_panel.configure(bg="#3c3f41")
        self.info_panel.geometry("340x170")
        self.info_panel.resizable(False, False)
        self.info_panel.attributes("-topmost", True)

        tk.Label(self.info_panel, text="Informações do Servidor",
                 font=("Arial", 13, "bold"), bg="#3c3f41", fg="#f0f0f0").pack(pady=(10, 10))

        local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            pass

        public_ip = "N/A"
        try:
            public_ip = requests.get("https://api.ipify.org").text
        except:
            pass

        info_font = ("Arial", 12, "bold")
        value_font = ("Arial", 12)

        container = tk.Frame(self.info_panel, bg="#3c3f41")
        container.pack(anchor="w", padx=15)

        row1 = tk.Frame(container, bg="#3c3f41")
        row1.pack(anchor="w", pady=2)
        tk.Label(row1, text="IP Local:", font=info_font, bg="#3c3f41", fg="#f0f0f0").pack(side="left")
        tk.Label(row1, text=local_ip, font=value_font, bg="#3c3f41", fg="#f0f0f0").pack(side="left", padx=(5, 0))

        row2 = tk.Frame(container, bg="#3c3f41")
        row2.pack(anchor="w", pady=2)
        tk.Label(row2, text="IP Público:", font=info_font, bg="#3c3f41", fg="#f0f0f0").pack(side="left")
        tk.Label(row2, text=public_ip, font=value_font, bg="#3c3f41", fg="#f0f0f0").pack(side="left", padx=(5, 0))

        row3 = tk.Frame(container, bg="#3c3f41")
        row3.pack(anchor="w", pady=2)
        tk.Label(row3, text="Porta:", font=info_font, bg="#3c3f41", fg="#f0f0f0").pack(side="left")
        tk.Label(row3, text=str(SERVER_PORT), font=value_font, bg="#3c3f41", fg="#f0f0f0").pack(side="left", padx=(5, 0))

    # janela de log
    def toggle_log_panel(self):
        if self.log_panel and self.log_panel.winfo_exists():
            self.log_panel.destroy()
            self.log_panel = None
        else:
            self.create_log_panel()

    def create_log_panel(self):
        if self.log_panel and self.log_panel.winfo_exists():
            return

        self.log_panel = tk.Toplevel(self.root)
        self.log_panel.title("Log de Entradas e Saídas")
        self.log_panel.configure(bg="#3c3f41")
        self.log_panel.geometry("700x450")  
        self.log_panel.resizable(True, True)  
        self.log_panel.attributes("-topmost", True)

        tk.Label(self.log_panel, text="Log de Entradas e Saídas",
                font=("Arial", 13, "bold"), bg="#3c3f41", fg="#f0f0f0").pack(pady=(10, 5))

        main_frame = tk.Frame(self.log_panel)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        style = ttk.Style()
        style.configure("Log.Treeview", background="#3c3f41", foreground="#f0f0f0",
                        fieldbackground="#3c3f41", font=("Arial", 11), rowheight=25)
        style.configure("Log.Treeview.Heading", font=("Arial", 12, "bold"), background="#2b2b2b", foreground="#f0f0f0")

        self.log_tree = ttk.Treeview(main_frame, columns=("usuario", "ip", "atividade", "datahora"),
                                    show="headings", style="Log.Treeview")
        self.log_tree.heading("usuario", text="Usuário")
        self.log_tree.heading("ip", text="IP")
        self.log_tree.heading("atividade", text="Atividade")
        self.log_tree.heading("datahora", text="Data/Hora")
        self.log_tree.column("usuario", anchor="center", width=150)
        self.log_tree.column("ip", anchor="center", width=150)
        self.log_tree.column("atividade", anchor="center", width=120)
        self.log_tree.column("datahora", anchor="center", width=180)  
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.log_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_tree.configure(yscrollcommand=scrollbar.set)

        button_frame = tk.Frame(self.log_panel, bg="#3c3f41")
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(button_frame, text="Limpar Log", bg="#e94e4e", fg="white",
                font=("Arial", 12, "bold"), relief="flat", command=self.clear_logs).pack(side=tk.RIGHT)

        self.refresh_log_tree()

    def add_log(self, usuario, ip, atividade):
        timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
        self.logs.append((usuario, ip, atividade, timestamp))
        if self.log_panel and self.log_panel.winfo_exists():
            self.refresh_log_tree()

    def refresh_log_tree(self):
        self.log_tree.delete(*self.log_tree.get_children())
        for log in self.logs:
            self.log_tree.insert("", "end", values=log)

    def clear_logs(self):
        self.logs.clear()
        if self.log_panel and self.log_panel.winfo_exists():
            self.refresh_log_tree()

    def update_status(self):
        color = "green" if flask_running else "red"
        text = "Rodando" if flask_running else "Parado"
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(1, 1, 13, 13, fill=color)
        self.status_label.config(text=text)

    def start_server_gui(self):
        start_server()
        self.update_status()

    def stop_server_gui(self):
        stop_server()
        self.update_status()

    def clear_fila(self):
        with fila_lock:
            fila.clear()
        self.update_tree()

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        with fila_lock:
            ordem = sorted(fila.items(), key=lambda x: x[1])
            for i, (name, _) in enumerate(ordem, 1):
                self.tree.insert("", "end", values=(i, name))

    def update_queue_periodic(self):
        self.update_tree()
        self.update_status()
        if self.update_loop_running:
            self.root.after(1000, self.update_queue_periodic)

    def close(self):
        self.update_loop_running = False
        stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ServerGUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.close)
    root.mainloop()
