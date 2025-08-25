# file: hardware_simulator.py
import socket
import time
import random
import threading
import math

# Konfigurasi
HOST = '127.0.0.1'
PORT_SYS1 = 65431
PORT_SYS2 = 65432

# Variabel global
simulation_state = {
    "profile": "normal",  # 'normal', 'spike', 'drift', 'periodic'
    "counter": 0,
    "running": True
}

def generate_data(system_name):
    """Membuat data berdasarkan profil simulasi yang aktif."""
    state = simulation_state
    
    # Nilai dasar
    temp = 25 + math.sin(state['counter'] / 20) + random.uniform(-0.5, 0.5)
    humidity = 50 + math.sin(state['counter'] / 30) * 5 + random.uniform(-1, 1)
    moisture = 55 - math.sin(state['counter'] / 40) * 10 + random.uniform(-2, 2)
    ph = 7.0 + math.sin(state['counter'] / 50) * 0.2 + random.uniform(-0.1, 0.1)
    cps = 250 + math.sin(state['counter'] / 15) * 50 + random.uniform(-10, 10)
    
    # Terapkan skenario
    if state["profile"] == "spike" and state["counter"] % 30 == 0 and state["counter"] > 0:
        print(f"\n[{system_name}] *** INJECTING SPIKE! ***")
        cps += random.randint(250, 300)  
        temp += random.uniform(5, 10)    
    
    elif state["profile"] == "drift":
        temp += state["counter"] * 0.05
        
    elif state["profile"] == "periodic":
        moisture += math.sin(state["counter"]) * 15

    state["counter"] += 1

    # Format string data
    return (
        f"{temp:.2f},{humidity:.2f},{moisture:.2f},{ph:.2f},{random.uniform(500, 1000):.0f},"
        f"{random.uniform(100, 200):.0f},{random.uniform(50, 100):.0f},{random.uniform(50, 150):.0f},"
        f"Co-60,{random.uniform(1170, 1330):.2f},{int(cps)},{random.uniform(1.0, 2.5):.2f}\n"
    )

def handle_client(conn, addr, system_name):
    """Melayani satu client sampai putus."""
    print(f"[{system_name}] Client terhubung dari {addr}")
    with conn:
        conn.settimeout(0.1)  
        while simulation_state["running"]:
            try:
                # kirim data simulasi
                data_str = generate_data(system_name)
                conn.sendall(data_str.encode('utf-8'))
                time.sleep(2)

                # cek pesan masuk
                try:
                    incoming = conn.recv(1024).decode('utf-8').strip()
                    if incoming == "STOP":
                        print(f"[{system_name}] Client meminta STOP.")
                        conn.sendall(b"STOP\n")
                        break
                except socket.timeout:
                    pass

            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                print(f"[{system_name}] Koneksi client terputus.")
                break
            except Exception as e:
                print(f"[{system_name}] ERROR: {e}")
                break
    print(f"[{system_name}] Client selesai.")

def system_simulator(host, port, system_name):
    """Server untuk satu sistem (Lisimeter)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print(f"[{system_name}] Simulator siap di {host}:{port}. Menunggu koneksi...")

        while simulation_state["running"]:
            try:
                conn, addr = s.accept()
                threading.Thread(target=handle_client, args=(conn, addr, system_name), daemon=True).start()
            except Exception as e:
                print(f"[{system_name}] ERROR listener: {e}")
                time.sleep(1)

def user_input_thread():
    """Menu interaktif untuk memilih profil simulasi."""
    time.sleep(2)
    while simulation_state["running"]:
        print("\n--- Pilih Skenario Simulasi ---")
        print("  1: Operasi Normal")
        print("  2: Lonjakan Tiba-tiba (Spike)")
        print("  3: Pergeseran Sensor (Drift)")
        print("  4: Gangguan Periodik (Noise)")
        print("  q: Keluar")
        choice = input("Masukkan pilihan: ")
        
        if choice == '1': 
            simulation_state["profile"] = "normal"
        elif choice == '2': 
            simulation_state["profile"] = "spike"; simulation_state["counter"] = 0
        elif choice == '3': 
            simulation_state["profile"] = "drift"; simulation_state["counter"] = 0
        elif choice == '4': 
            simulation_state["profile"] = "periodic"; simulation_state["counter"] = 0
        elif choice.lower() == 'q':
            print("Menutup simulator...")
            simulation_state["running"] = False
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    print("===== Hardware Simulator untuk LISIDA v2.2 (Fixed) =====")
    
    # Jalankan 2 sistem
    threading.Thread(target=system_simulator, args=(HOST, PORT_SYS1, "Lisimeter 1"), daemon=True).start()
    threading.Thread(target=system_simulator, args=(HOST, PORT_SYS2, "Lisimeter 2"), daemon=True).start()
    
    # Jalankan menu input
    threading.Thread(target=user_input_thread, daemon=True).start()
    
    try:
        while simulation_state["running"]:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Menutup simulator (Ctrl+C).")
        simulation_state["running"] = False
