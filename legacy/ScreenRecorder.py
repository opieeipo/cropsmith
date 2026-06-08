import mss
import cv2
import numpy as np
import time
import threading
from pynput.keyboard import Controller, Key
import argparse
import tkinter as tk
import os
from PIL import Image
from PyPDF2 import PdfMerger
import pytesseract # New dependency for OCR

# --- Tesseract Configuration (REQUIRED) ---
# You may need to change this path if Tesseract is installed in a different location.
# This line tells the pytesseract library where to find the tesseract.exe executable.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- Configuration (Default Values for Optional Arguments) ---
# These values will be used if not provided via command-line arguments.
# Screen capture parameters (top, left, width, height) are now MANDATORY arguments.

# Output image file settings
OUTPUT_DIR = "c:\\temp\\snapshots" # Default directory to save image files
BASE_FILENAME = "screenshot"      # Base name for the saved image files
FPS = 1.0                         # Frames per second for image capture

# Mapping for special keys from string arguments
KEY_MAP = {
    "space": Key.space,
    "enter": Key.enter,
    "esc": Key.esc,
    "tab": Key.tab,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "shift": Key.shift,
    "ctrl": Key.ctrl,
    "alt": Key.alt,
    # Add more special keys here as needed, in lowercase
}

# --- Global Variables ---
stop_capture_flag = False
keyboard_controller = Controller()
bounding_box_window = None # To hold the Tkinter window instance

# --- Functions ---

def get_key_from_string(key_str_arg):
    """
    Converts a string argument to a pynput.keyboard.Key object or returns the string itself.
    """
    key_str_lower = key_str_arg.lower()
    if key_str_lower in KEY_MAP:
        return KEY_MAP[key_str_lower]
    return key_str_lower # Return as string if not a special key

def simulate_key_inputs(key_to_send, interval_between_strokes, num_strokes, initial_delay_before_simulation):
    """
    Simulates key presses for a specified key, number of times, and interval.
    """
    print(f"Starting key input simulation thread. Will simulate '{key_to_send}' {num_strokes} times with {interval_between_strokes}s interval.")
    
    # Wait for the initial delay before starting key presses
    if initial_delay_before_simulation > 0:
        time.sleep(initial_delay_before_simulation)

    for i in range(num_strokes):
        if stop_capture_flag:
            print("Key input simulation stopped early due to capture termination.")
            break
        
        print(f"Simulating stroke {i+1}/{num_strokes} for '{key_to_send}' at {time.time():.2f}s")
        if isinstance(key_to_send, Key):
            keyboard_controller.press(key_to_send)
            keyboard_controller.release(key_to_send)
        elif isinstance(key_to_send, str):
            keyboard_controller.type(key_to_send)
        else:
            print(f"Warning: Unknown key action type: {type(key_to_send)}")

        if i < num_strokes - 1: # Don't wait after the last stroke
            time.sleep(interval_between_strokes)

    print("Key input simulation thread finished.")

def stop_gui():
    """Stops the Tkinter main loop and destroys the bounding box window."""
    global bounding_box_window
    if bounding_box_window:
        bounding_box_window.quit()
        bounding_box_window.destroy()

def create_bounding_box(monitor_params):
    """
    Creates a transparent, always-on-top window with a red border
    to visualize the capture area.
    """
    global bounding_box_window
    root = tk.Tk()
    root.overrideredirect(True) # Remove window decorations (title bar, close button)
    root.attributes('-topmost', True) # Keep it on top of other windows

    # The -transparentcolor attribute makes the window transparent for a specific color.
    # We will draw a canvas with this color and then draw a border.
    transparent_color = 'gray'
    root.attributes('-transparentcolor', transparent_color)

    # Set window geometry
    root.geometry(f"{monitor_params['width']}x{monitor_params['height']}+{monitor_params['left']}+{monitor_params['top']}")

    # Create a canvas that fills the window
    canvas = tk.Canvas(root, bg=transparent_color, highlightthickness=0)
    canvas.pack(expand=True, fill='both')

    # Draw a red rectangle with a 3-pixel width border, making the inside transparent
    canvas.create_rectangle(
        0, 0,
        monitor_params['width'], monitor_params['height'],
        outline='red', width=3
    )

    bounding_box_window = root
    root.mainloop()

def capture_snapshots(monitor_params, capture_duration, output_dir, base_filename, fps):
    """
    Captures the specified screen region, performs OCR, and saves it to a searchable PDF.
    """
    global stop_capture_flag
    
    sct = mss.mss()
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(f"Capturing snapshots to {output_dir}/ (Press Ctrl+C to stop early)...")
    start_time = time.time()
    frame_count = 0

    try:
        while not stop_capture_flag:
            # Get raw pixels from the screen
            sct_img = sct.grab(monitor_params)
            
            # Convert to a NumPy array
            img = np.array(sct_img)
            
            # Convert from BGRA to RGB for Pillow
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            
            # Convert the NumPy array to a Pillow Image
            pil_image = Image.fromarray(frame)

            # Use pytesseract to create a searchable PDF from the Pillow Image
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(pil_image, extension='pdf')

            # Save the PDF bytes to a file
            filename = os.path.join(output_dir, f"{base_filename}_{frame_count:04d}.pdf")
            with open(filename, "w+b") as f:
                f.write(pdf_bytes)
            
            frame_count += 1
            
            # Check if capture duration has been reached
            if capture_duration is not None and (time.time() - start_time) > capture_duration:
                print(f"Capture duration of {capture_duration} seconds reached.")
                stop_capture_flag = True
                break

            # Control the capture rate
            time.sleep(1.0 / fps)
    
    except KeyboardInterrupt:
        print("\nCapture stopped by user (Ctrl+C).")
    except pytesseract.TesseractNotFoundError:
        print("\nError: Tesseract is not installed or the path is incorrect.")
        print("Please check the `pytesseract.pytesseract.tesseract_cmd` setting in the script.")
    except Exception as e:
        print(f"An error occurred during capture: {e}")
    finally:
        stop_capture_flag = True # Ensure the flag is set to stop other threads
        print(f"Capture finished. {frame_count} snapshots saved to '{output_dir}'.")
        stop_gui()

def merge_pdfs(output_dir, base_filename):
    """
    Merges all individual PDF files into a single master PDF.
    """
    print("Merging individual PDF files into 'final.pdf'...")
    pdf_merger = PdfMerger()
    
    # Get all PDF files and sort them chronologically
    pdf_files = sorted([f for f in os.listdir(output_dir) if f.startswith(f"{base_filename}_") and f.endswith(".pdf")])
    
    if not pdf_files:
        print("No PDF files found to merge.")
        return
        
    for pdf_file in pdf_files:
        filepath = os.path.join(output_dir, pdf_file)
        try:
            pdf_merger.append(filepath)
        except Exception as e:
            print(f"Error appending {pdf_file}: {e}")
            
    final_output_path = os.path.join(output_dir, "final.pdf")
    with open(final_output_path, 'wb') as f:
        pdf_merger.write(f)
    
    print(f"Successfully created master PDF: '{final_output_path}'.")

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Screen capture tool with timed key input, a transparent bounding box, and searchable PDF output.")
    
    # Screen capture parameters are now mandatory
    parser.add_argument("--top", type=int, required=True,
                        help="Top coordinate of the capture area (e.g., 100)")
    parser.add_argument("--left", type=int, required=True,
                        help="Left coordinate of the capture area (e.g., 100)")
    parser.add_argument("--width", type=int, required=True,
                        help="Width of the capture area (e.g., 800)")
    parser.add_argument("--height", type=int, required=True,
                        help="Height of the capture area (e.g., 600)")
    
    # Key input parameters (with defaults)
    parser.add_argument("--key-input", type=str, default="right",
                        help="The key to simulate (e.g., 'right', 'space', 'a', 'Hello World'). Default: 'right'")
    parser.add_argument("--interval", type=float, default=0.5,
                        help="Time interval in seconds between successive key strokes. Default: 0.5")
    parser.add_argument("--stroke-count", type=int, default=1,
                        help="Number of times the key will be simulated. Default: 1")
    
    # New startup delay parameter
    parser.add_argument("--startup-delay", type=float, default=3.0,
                        help="Initial delay in seconds before capture and key inputs begin. Default: 3.0")
    
    # New output parameters
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR,
                        help="Directory to save the snapshot images. Default: 'c:\\temp\\snapshots'")
    parser.add_argument("--base-filename", type=str, default=BASE_FILENAME,
                        help="Base filename for the snapshots. Snapshots will be saved as 'base-filename_0000.pdf'. Default: 'screenshot'")
    parser.add_argument("--fps", type=float, default=FPS,
                        help="Frames per second for image capture. Default: 1.0 (1 capture per second)")

    # New trial mode parameter
    parser.add_argument("--trial-mode", action="store_true",
                        help="Run in trial mode to only display the bounding box without capturing or simulating keys.")

    args = parser.parse_args()

    # Update MONITOR based on arguments
    current_monitor_params = {
        "top": args.top,
        "left": args.left,
        "width": args.width,
        "height": args.height
    }

    print("Ensure you have the following Python libraries installed:")
    print("pip install mss opencv-python numpy pynput tkinter Pillow PyPDF2 pytesseract")
    print("\n--- IMPORTANT: Tesseract OCR Engine Installation ---")
    print("This script requires the Tesseract OCR engine to be installed on your system.")
    print("Download and install it from here: https://tesseract-ocr.github.io/tessdoc/Installation.html")
    print("Make sure the Tesseract installation directory (e.g., C:\\Program Files\\Tesseract-OCR) is added to your system's PATH environmental variable.")
    print("The script is currently configured with the path 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'.")
    print("If your installation path is different, please update the `pytesseract.pytesseract.tesseract_cmd` variable at the top of the script.")

    # Run in trial mode or full mode
    if args.trial_mode:
        print("\n--- Trial Mode ---")
        print("Starting bounding box visualization in trial mode. Press Ctrl+C to close the window.")
        print(f"Current capture area: Top={current_monitor_params['top']}, Left={current_monitor_params['left']}, "
              f"Width={current_monitor_params['width']}, Height={current_monitor_params['height']}")
        
        # Start the bounding box visualization in a separate thread
        bounding_box_thread = threading.Thread(target=create_bounding_box, args=(current_monitor_params,))
        bounding_box_thread.daemon = True
        bounding_box_thread.start()
        
        try:
            # Keep the main thread alive while the GUI window is open
            while threading.active_count() > 1: # Wait for the gui thread to finish
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nTrial mode stopped by user (Ctrl+C).")
        finally:
            stop_gui()
            print("Script execution complete.")

    else: # Default (non-trial) mode
        # Parse the key input string
        parsed_key_input = get_key_from_string(args.key_input)
        
        # Calculate dynamic CAPTURE_DURATION
        total_key_action_duration = 0
        if args.stroke_count > 0:
            total_key_action_duration = (args.stroke_count - 1) * args.interval
        
        # Minimum capture duration is (startup_delay + 3 seconds final buffer)
        dynamic_capture_duration = args.startup_delay + total_key_action_duration + 3
        
        print(f"\n--- Full Capture Mode ---")
        print(f"Calculated capture duration: {dynamic_capture_duration:.2f} seconds (startup delay {args.startup_delay}s + key actions + 3s final buffer).")
        print("1. Run the script with ALL mandatory screen capture arguments and optional key inputs:")
        print("   Example: python your_script_name.py --left 0 --top 0 --width 1920 --height 1080 --key-input 'right' --interval 0.2 --stroke-count 10 --startup-delay 5 --output-dir C:\\MyCaptures --fps 2")
        print(f"   Current capture area: Top={current_monitor_params['top']}, Left={current_monitor_params['left']}, "
              f"Width={current_monitor_params['width']}, Height={current_monitor_params['height']}")
        print(f"   Key Input: '{args.key_input}' (parsed as: {parsed_key_input}), Interval: {args.interval}s, Stroke Count: {args.stroke_count}")
        print(f"   Startup Delay: {args.startup_delay}s")
        print(f"   Output: {args.output_dir}/{args.base_filename}_*.pdf, Capture Rate: {args.fps} FPS")
        print("\nStarting capture in {} seconds...".format(args.startup_delay))
        
        # Start the bounding box visualization in a separate thread
        bounding_box_thread = threading.Thread(target=create_bounding_box, args=(current_monitor_params,))
        bounding_box_thread.daemon = True
        bounding_box_thread.start()
        
        # Wait for the initial delay before starting capture and key presses
        time.sleep(args.startup_delay)
    
        # Start the key input simulation in a separate thread
        key_input_thread = threading.Thread(target=simulate_key_inputs, args=(parsed_key_input, args.interval, args.stroke_count, 0,))
        key_input_thread.start()
    
        # Start the screen capture in the main thread
        capture_snapshots(current_monitor_params, dynamic_capture_duration, args.output_dir, args.base_filename, args.fps)
    
        # Wait for the key input thread to finish if it's still running
        key_input_thread.join()
        
        # Call the new function to merge the PDFs
        merge_pdfs(args.output_dir, args.base_filename)
        
        print("Script execution complete.")
