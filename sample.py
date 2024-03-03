import tkinter as tk
from tkinter import ttk
import subprocess
import os
import threading
import configparser

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))
scrcpy_dir = os.path.join(script_dir, 'scrcpy')

# Load config
def load_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(script_dir, 'config.ini'))
    return config

# Load default bitrate from config
config = load_config()
default_bitrate = config.getint('scrcpy', 'bitrate', fallback=20)

casting_devices = {}

def initialize_adb():
    # adb kill-serverを実行
    subprocess.run(["adb", "kill-server"])
    # Notify the GUI that the initialization is complete
    # loading_label.config(text="GUI ready.")
    get_serials_async()

def start_scrcpy():
    global casting_devices

    serial = serial_var.get()
    size = size_entry.get()
    bitrate = bitrate_entry.get() or default_bitrate
    screen_off = screen_off_var.get()
    title = f"Scrcpy for Quest - {serial}"
    # device = device_type_var.get()

    # Construct the command
    command = ["scrcpy", "-s", serial]
    if size:
        command.extend(["--max-size", size])
    if bitrate:
        command.extend(["--video-bit-rate", str(bitrate)+"M"])
    if screen_off:
        command.append("--power-off-on-close")
    if title:
        command.extend(["--window-title", title])
    # if device == "Quest 2":
    #     command.append(["--crop=1450:1450:140:140"])
    # elif device == "Quest 3":
    #     command.append(["--crop 2064:2208:2064:100"]) # Consider later

    # Start the process asynchronously and redirect stderr to stdout
    process = subprocess.Popen(command, cwd=scrcpy_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    casting_devices[serial] = process

    # Start a separate thread to wait for the process to finish and output any errors
    threading.Thread(target=monitor_casting, args=(serial,)).start()

def monitor_casting(serial):
    global casting_devices

    # Wait for the process to finish
    process = casting_devices[serial]
    stdout, _ = process.communicate()  # This will also capture stderr because of the redirection

    # Print the output, which includes stderr
    print(stdout.decode())

    # Remove the process from the dictionary
    del casting_devices[serial]

    print("Casting finished.")

def stop_scrcpy():
    global casting_devices

    selected_device = serial_var.get()
    if selected_device not in casting_devices:
        print("No casting found for the selected device.")
        return

    process = casting_devices[selected_device]
    process.terminate()
    del casting_devices[selected_device]
    print(f"Casting stopped for device: {selected_device}")

def get_serials_async():
    def get_serials():
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        serials = [line.split()[0] for line in lines[1:] if line.endswith("device")]
        serial_var.set(serials[0] if serials else "")
        serial_menu["menu"].delete(0, "end")
        for serial in serials:
            serial_menu["menu"].add_command(label=serial, command=tk._setit(serial_var, serial))
        get_button.config(state="normal")  # Enable the get button

    get_button.config(state="disabled")  # Disable the get button while processing
    threading.Thread(target=get_serials).start()

# Create Tkinter window
root = tk.Tk()
root.title("Scrcpy GUI for Quest")
root.resizable(False, False)  # Disable window resizing
root.geometry("500x200")  # Set window size

# Set font
if 'win' in root.tk.call('tk', 'windowingsystem'):
    font = ("MS Gothic", 12)
else:
    font = ("Noto Sans CJK JP", 12)

# Serial number input and Get button
serial_label = tk.Label(root, text="Device:")
serial_label.grid(row=0, column=0, sticky=tk.W)
serial_var = tk.StringVar()
serial_menu = tk.OptionMenu(root, serial_var, "")
serial_menu.grid(row=0, column=1, sticky=tk.EW)
get_button = tk.Button(root, text="Get", command=get_serials_async)
get_button.grid(row=0, column=2)

# Mirroring window size specification
size_label = tk.Label(root, text="Screen Size (e.g., 1920x1080):")
size_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
size_entry = tk.Entry(root, width=15)
size_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

# Bitrate specification
bitrate_label = tk.Label(root, text="Bitrate (Mbps):")
bitrate_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
bitrate_entry = tk.Entry(root, width=15)
bitrate_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
bitrate_entry.insert(0, str(default_bitrate))  # Insert default bitrate

# Screen off feature when disconnecting
screen_off_var = tk.BooleanVar()
screen_off_var.set(False)
screen_off_checkbox = tk.Checkbutton(root, text="Turn off screen when disconnecting", variable=screen_off_var)
screen_off_checkbox.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5, columnspan=2)

# Start/Stop mirroring buttons
start_button = tk.Button(root, text="Start Scrcpy", command=start_scrcpy)
start_button.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
stop_button = tk.Button(root, text="Stop Scrcpy", command=stop_scrcpy)
stop_button.grid(row=4, column=1, padx=5, pady=5, sticky=tk.E)

# Device Selection
# device_type_var = tk.StringVar(value="Other")
# quest_2_radio = tk.Radiobutton(root, text="Quest 2", variable=device_type_var, value="Quest 2")
# quest_2_radio.grid(row=5, column=0, sticky=tk.W)
# quest_3_radio = tk.Radiobutton(root, text="Quest 3", variable=device_type_var, value="Quest 3")
# quest_3_radio.grid(row=5, column=1, sticky=tk.W)
# quest_pro_radio = tk.Radiobutton(root, text="Quest Pro", variable=device_type_var, value="Quest Pro")
# quest_pro_radio.grid(row=5, column=2, sticky=tk.W)
# other_radio = tk.Radiobutton(root, text="Other", variable=device_type_var, value="Other")
# other_radio.grid(row=5, column=3, sticky=tk.W)

# Adjust the grid configuration
root.grid_columnconfigure (1, weight=1)

# Initialize ADB in a separate thread to avoid freezing the GUI
threading.Thread(target=initialize_adb).start()

# Start GUI loop
root.mainloop()