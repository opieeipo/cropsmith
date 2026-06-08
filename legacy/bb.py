import tkinter as tk
import sys

class BoundingBoxMeasurer:
    """
    A full-screen, transparent utility for measuring screen coordinates 
    (top, left, width, height) of a user-defined bounding box using 
    click-and-drag.
    """
    def __init__(self, master):
        # 1. Setup the main window properties
        self.master = master
        master.title("Bounding Box Measurer")

        # Get screen geometry
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()

        # Configure the window for overlay behavior
        master.attributes("-fullscreen", True) # Full screen
        master.attributes("-alpha", 0.3)      # Semi-transparent background
        master.attributes("-topmost", True)   # Always on top
        master.overrideredirect(True)         # Remove window decorations (border, title bar)

        # 2. State variables
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.rect_id = None
        self.dragging = False

        # 3. Canvas setup
        self.canvas = tk.Canvas(master, cursor="cross", bg='gray', 
                                width=self.screen_width, height=self.screen_height, 
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # 4. Info Label (Always visible coordinates display)
        self.info_label = tk.Label(master, 
                                   text="Press ESC to Quit\nClick and Drag to Measure",
                                   bg="#1a1a1a", fg="#00ff99", 
                                   font=("Inter", 14, "bold"),
                                   padx=10, pady=10, relief=tk.RIDGE, borderwidth=2)
        
        # Position the info label in the bottom left corner
        # Using a fixed position because it's a fixed-size information panel
        self.canvas.create_window(20, self.screen_height - 150, 
                                  anchor="nw", window=self.info_label)

        # 5. Bind mouse and keyboard events
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        master.bind("<Escape>", self.quit_app)

    # --- Event Handlers ---

    def on_press(self, event):
        """Starts the bounding box drawing process."""
        self.dragging = True
        # Record the starting global screen coordinates
        self.start_x = event.x
        self.start_y = event.y

        # Clear any existing rectangle
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

        # Draw the initial rectangle (just a point)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, 
                                                    self.start_x, self.start_y,
                                                    outline="#ff4400", width=3,
                                                    dash=(6, 4))
        # Update label
        self._update_info_label(0, 0, self.start_x, self.start_y)

    def on_drag(self, event):
        """Updates the bounding box and coordinates in real-time during drag."""
        if not self.dragging:
            return

        self.current_x = event.x
        self.current_y = event.y

        # Calculate bounding box parameters
        left = min(self.start_x, self.current_x)
        top = min(self.start_y, self.current_y)
        width = abs(self.start_x - self.current_x)
        height = abs(self.start_y - self.current_y)

        # Update the canvas rectangle coordinates
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, 
                           self.current_x, self.current_y)
        
        # Update the information label
        self._update_info_label(width, height, left, top)

    def on_release(self, event):
        """Finalizes the selection and prints the result to the console."""
        if not self.dragging:
            return
            
        self.dragging = False

        # Final coordinates are the current ones
        x2 = event.x
        y2 = event.y

        left = min(self.start_x, x2)
        top = min(self.start_y, y2)
        width = abs(self.start_x - x2)
        height = abs(self.start_y - y2)

        # Print final result to console
        print("-" * 30)
        print(f"Final Bounding Box Selected:")
        print(f"  Left (X): {left}")
        print(f"  Top (Y): {top}")
        print(f"  Width: {width}")
        print(f"  Height: {height}")
        print("-" * 30)
        
        # Reset the drawing for the next selection
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.canvas.delete(self.rect_id)
        self.rect_id = None
        self._update_info_label(0, 0, 0, 0, reset=True)


    # --- Helper Methods ---

    def _update_info_label(self, width, height, left, top, reset=False):
        """Formats and updates the text in the information label."""
        if reset:
            info_text = "Press ESC to Quit\nClick and Drag to Measure"
        else:
            info_text = (
                f"Left (X): {left}\n"
                f"Top (Y): {top}\n"
                f"Width: {width}\n"
                f"Height: {height}"
            )
        self.info_label.config(text=info_text)

    def quit_app(self, event=None):
        """Quits the application."""
        print("Bounding Box Measurer closed.")
        self.master.destroy()
        sys.exit()

if __name__ == '__main__':
    # Initialize the main Tkinter window
    root = tk.Tk()
    
    # Check if the OS is macOS, as it handles full-screen differently
    if sys.platform == "darwin":
        # On macOS, force a specific geometry before going full-screen to ensure proper overlay
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    
    # Start the application logic
    app = BoundingBoxMeasurer(root)
    
    # Run the Tkinter event loop
    root.mainloop()
