import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, END, Scale, HORIZONTAL, Entry, Button, OptionMenu, StringVar, Label
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk, ImageEnhance, ImageOps, ImageFilter

class ImageProcessorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Calculate window size to be 80% of the screen size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)

        # Set the window size and center it on the screen
        self.geometry(f"{window_width}x{window_height}+{screen_width // 10}+{screen_height // 10}")
        self.title("Image Processor")

        # Variables
        self.curr_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.current_image_index = tk.IntVar()
        self.warning_message = tk.StringVar()
        self.current_image_path = tk.StringVar()
        self.filename = tk.StringVar()
        self.output_format = StringVar(value="PNG")  # Default output format
        self.selected_filter = StringVar(value="NONE")  # Default filter

        # Calculate space for canvas based on the window size and other widgets
        left_frame_width = 300
        right_frame_width = 200
        canvas_width = window_width - left_frame_width - right_frame_width - 40
        canvas_height = window_height - 200  # Leave space for buttons and progress bar
        self.max_size = (canvas_width, canvas_height)  # Max width and height for images

        self.zoom_level = tk.DoubleVar(value=1.0)
        self.rotation_angle = 0  # Store rotation angle

        # Enhancement variables
        self.brightness_level = tk.DoubleVar(value=1.0)
        self.contrast_level = tk.DoubleVar(value=1.0)
        self.saturation_level = tk.DoubleVar(value=1.0)
        self.sharpness_level = tk.DoubleVar(value=1.0)

        # Supported image formats
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')

        # Output formats available in PIL
        self.available_formats = ["PNG", "JPEG", "GIF", "BMP", "TIFF", "PPM", "ICO", "PDF"]

        # Filter options
        self.filter_options = [
            "NONE", "EMBOSS", "EDGE_ENHANCE", "FIND_EDGES", "SEPIA",
            "PASTEL", "SHARPEN", "BLUR", "WATERCOLOR", "OIL_PAINTING"
        ]

        # GUI Layout
        self.create_widgets()

        # Placeholder for images
        self.images = []
        self.curr_image = None
        self.original_image = None

    def create_widgets(self):
        # Create the main layout frames
        left_frame = tk.Frame(self, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        center_frame = tk.Frame(self)
        center_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        right_frame = tk.Frame(self, width=200)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # Left Frame Widgets
        tk.Button(left_frame, text="Select Image Directory", command=self.select_directory).pack(pady=5)

        tk.Label(left_frame, text="Current Image Path:").pack()
        tk.Label(left_frame, textvariable=self.current_image_path, fg="blue", wraplength=200).pack(pady=5)

        listbox_frame = tk.Frame(left_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.image_listbox = Listbox(listbox_frame, yscrollcommand=scrollbar.set)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_listbox.bind("<<ListboxSelect>>", self.on_image_select)

        scrollbar.config(command=self.image_listbox.yview)

        # Center Frame Widgets
        self.canvas = tk.Canvas(center_frame, width=self.max_size[0], height=self.max_size[1])
        self.canvas.pack(side=tk.TOP, expand=True)
        self.canvas.bind("<Button-1>", lambda event: self.next_image())  # Advance image on canvas click

        button_frame = tk.Frame(center_frame)
        button_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.prev_button = tk.Button(button_frame, text="Previous Image", command=self.previous_image)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(button_frame, text="Next Image", command=self.next_image)
        self.next_button.pack(side=tk.LEFT, padx=10)

        self.progress = Progressbar(button_frame, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(side=tk.LEFT, padx=10, expand=True)

        self.delete_button = tk.Button(button_frame, text="Delete Image", command=self.delete_image)
        self.delete_button.pack(side=tk.RIGHT, padx=10)

        # Right Frame Widgets
        zoom_frame = tk.Frame(right_frame)
        zoom_frame.pack(fill=tk.X, pady=10)

        self.zoom_slider = Scale(zoom_frame, from_=0.0, to=3.0, resolution=0.01, orient=HORIZONTAL, variable=self.zoom_level,
                            label="Zoom", command=self.apply_zoom, length=200)
        self.zoom_slider.pack(fill=tk.X)

        self.zoom_entry = Entry(zoom_frame)
        self.zoom_entry.pack(fill=tk.X)
        self.zoom_entry.bind("<Return>", self.on_zoom_entry)

        self.zoom_warning = tk.Label(zoom_frame, textvariable=self.warning_message, fg="red", wraplength=200)
        self.zoom_warning.pack(fill=tk.X, pady=5)

        rotate_frame = tk.Frame(right_frame)
        rotate_frame.pack(fill=tk.X, pady=10)

        rotate_right_button = Button(rotate_frame, text="Rotate Right", command=lambda: self.rotate_image(-90))
        rotate_right_button.pack(fill=tk.X, pady=5)

        rotate_left_button = Button(rotate_frame, text="Rotate Left", command=lambda: self.rotate_image(90))
        rotate_left_button.pack(fill=tk.X, pady=5)

        # Brightness, Contrast, Saturation, and Sharpness Controls
        enhancement_frame = tk.Frame(right_frame)
        enhancement_frame.pack(fill=tk.X, pady=10)

        tk.Label(enhancement_frame, text="Brightness").pack(fill=tk.X)
        self.brightness_slider = Scale(enhancement_frame, from_=0.0, to=3.0, resolution=0.01, orient=HORIZONTAL, variable=self.brightness_level,
                                       command=self.apply_enhancements, length=200)
        self.brightness_slider.pack(fill=tk.X)

        tk.Label(enhancement_frame, text="Contrast").pack(fill=tk.X)
        self.contrast_slider = Scale(enhancement_frame, from_=0.0, to=3.0, resolution=0.01, orient=HORIZONTAL, variable=self.contrast_level,
                                     command=self.apply_enhancements, length=200)
        self.contrast_slider.pack(fill=tk.X)

        tk.Label(enhancement_frame, text="Saturation").pack(fill=tk.X)
        self.saturation_slider = Scale(enhancement_frame, from_=0.0, to=3.0, resolution=0.01, orient=HORIZONTAL, variable=self.saturation_level,
                                       command=self.apply_enhancements, length=200)
        self.saturation_slider.pack(fill=tk.X)

        tk.Label(enhancement_frame, text="Sharpness").pack(fill=tk.X)
        self.sharpness_slider = Scale(enhancement_frame, from_=0.0, to=3.0, resolution=0.01, orient=HORIZONTAL, variable=self.sharpness_level,
                                      command=self.apply_enhancements, length=200)
        self.sharpness_slider.pack(fill=tk.X)

        # Filter Selection Section
        filter_frame = tk.Frame(right_frame)
        filter_frame.pack(fill=tk.X, pady=10)

        tk.Label(filter_frame, text="Select Filter").pack(fill=tk.X)
        self.filter_dropdown = OptionMenu(filter_frame, self.selected_filter, *self.filter_options, command=self.apply_filter)
        self.filter_dropdown.pack(fill=tk.X, pady=5)

        self.filter_label = Label(filter_frame, text="Current Filter: NONE", fg="blue")
        self.filter_label.pack(fill=tk.X, pady=5)

        # Save Image Section
        save_frame = tk.Frame(right_frame)
        save_frame.pack(fill=tk.X, pady=10)

        tk.Button(save_frame, text="Select Output Directory", command=self.select_output_directory).pack(fill=tk.X, pady=5)
        tk.Label(save_frame, textvariable=self.output_dir, fg="blue", wraplength=200).pack(pady=5)

        tk.Label(save_frame, text="Filename").pack(fill=tk.X)
        self.filename_entry = Entry(save_frame, textvariable=self.filename)
        self.filename_entry.pack(fill=tk.X, pady=5)

        tk.Label(save_frame, text="Output Format").pack(fill=tk.X)
        self.format_dropdown = OptionMenu(save_frame, self.output_format, *self.available_formats)
        self.format_dropdown.pack(fill=tk.X, pady=5)

        tk.Button(save_frame, text="Save Image", command=self.save_image).pack(fill=tk.X, pady=10)

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.curr_dir.set(directory)
            self.load_images()

    def select_output_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def load_images(self):
        # Get all image files in the selected directory
        all_files = [f for f in os.listdir(self.curr_dir.get()) if f.lower().endswith(self.supported_formats)]
        if not all_files:
            messagebox.showerror("Error", "No images found in the directory.")
            return

        # Sort the image files naturally
        self.images = sorted(all_files, key=self.natural_sort_key)
        self.image_listbox.delete(0, END)  # Clear any previous listbox entries

        # Add images to the listbox
        for image in self.images:
            self.image_listbox.insert(END, image)

        self.current_image_index.set(0)
        self.load_image(0)

    def natural_sort_key(self, s):
        # Function to extract numerical parts for natural sorting
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    def load_image(self, index):
        # Load the image corresponding to the given index
        if index < 0 or index >= len(self.images):
            messagebox.showinfo("End of Range", "No more images in this direction.")
            return

        self.current_image_index.set(index)
        filename = os.path.join(self.curr_dir.get(), self.images[index])

        if not os.path.isfile(filename):
            self.warning_message.set(f"Image {filename} does not exist.")
            return

        self.warning_message.set("")  # Clear any previous warnings
        self.current_image_path.set(filename)

        # Open image using PIL
        image = Image.open(filename)
        self.original_image = image.copy()

        # Reset rotation, enhancements, and filter
        self.rotation_angle = 0
        self.brightness_level.set(1.0)
        self.contrast_level.set(1.0)
        self.saturation_level.set(1.0)
        self.sharpness_level.set(1.0)
        self.selected_filter.set("NONE")
        self.filter_label.config(text="Current Filter: NONE")

        # Resize image if larger than the max size
        image = self.resize_image(image)

        # Set the initial zoom level to reflect any resizing
        initial_zoom = min(self.max_size[0] / self.original_image.width, self.max_size[1] / self.original_image.height)
        self.zoom_level.set(initial_zoom)
        self.update_zoom_entry(initial_zoom)

        self.display_image(image)

        # Update the progress bar
        self.update_progress_bar()

        # Update the listbox selection and ensure it is visible
        self.image_listbox.selection_clear(0, END)
        self.image_listbox.selection_set(index)
        self.image_listbox.activate(index)
        self.image_listbox.see(index)

    def resize_image(self, image):
        """Resize image to fit within the max size constraints."""
        image.thumbnail(self.max_size, Image.LANCZOS)
        return image

    def display_image(self, image):
        """Display the given image on the canvas."""
        self.canvas.delete("all")  # Clear previous image
        image_width, image_height = image.size
        self.curr_image = ImageTk.PhotoImage(image)
        self.canvas.create_image((self.max_size[0] - image_width) // 2, (self.max_size[1] - image_height) // 2, anchor=tk.NW, image=self.curr_image)

    def apply_zoom(self, value):
        """Apply zoom to the currently displayed image."""
        zoom_factor = float(value)
        self.update_zoom_entry(zoom_factor)
        self.update_image_zoom(zoom_factor)

    def update_zoom_entry(self, zoom_factor):
        """Update the zoom entry with the current zoom level."""
        self.zoom_entry.delete(0, END)
        self.zoom_entry.insert(0, f"{zoom_factor:.2f}")

    def update_image_zoom(self, zoom_factor):
        """Update the displayed image according to the zoom factor."""
        if self.original_image:
            width = int(self.original_image.width * zoom_factor)
            height = int(self.original_image.height * zoom_factor)

            if width > self.max_size[0] or height > self.max_size[1]:
                width, height = self.max_size
                self.warning_message.set("Max zoom level reached.")
                self.zoom_level.set(min(self.max_size[0] / self.original_image.width,
                                        self.max_size[1] / self.original_image.height))
            else:
                self.warning_message.set("")

            image = self.original_image.resize((width, height), Image.LANCZOS)
            image = image.rotate(self.rotation_angle, expand=True)
            self.display_image(self.apply_enhancements_to_image(image))

    def apply_enhancements(self, *args):
        """Apply brightness, contrast, saturation, and sharpness adjustments."""
        if self.original_image:
            image = self.original_image.copy()
            image = self.resize_image(image)
            image = image.rotate(self.rotation_angle, expand=True)
            self.display_image(self.apply_enhancements_to_image(image))

    def apply_enhancements_to_image(self, image):
        """Apply brightness, contrast, saturation, sharpness, and filter to an image."""
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(self.brightness_level.get())

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self.contrast_level.get())

        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(self.saturation_level.get())

        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(self.sharpness_level.get())

        return self.apply_filter_to_image(image)

    def apply_filter(self, *args):
        """Apply selected filter to the image and update the display."""
        self.filter_label.config(text=f"Current Filter: {self.selected_filter.get()}")
        self.display_image(self.apply_enhancements_to_image(self.original_image))

    def apply_filter_to_image(self, image):
        """Apply the selected filter to the image."""
        filter_type = self.selected_filter.get()

        if filter_type == "EMBOSS":
            image = image.filter(ImageFilter.EMBOSS)
        elif filter_type == "EDGE_ENHANCE":
            image = image.filter(ImageFilter.EDGE_ENHANCE)
        elif filter_type == "FIND_EDGES":
            image = image.filter(ImageFilter.FIND_EDGES)
        elif filter_type == "SEPIA":
            sepia_image = ImageOps.colorize(image.convert("L"), "#704214", "#C0A080")
            image = sepia_image
        elif filter_type == "PASTEL":
            pastel_image = image.filter(ImageFilter.SMOOTH_MORE)
            image = pastel_image
        elif filter_type == "SHARPEN":
            image = image.filter(ImageFilter.SHARPEN)
        elif filter_type == "BLUR":
            image = image.filter(ImageFilter.BLUR)
        elif filter_type == "WATERCOLOR":
            image = image.filter(ImageFilter.SMOOTH)
        elif filter_type == "OIL_PAINTING":
            image = image.filter(ImageFilter.SMOOTH_MORE)

        return image

    def rotate_image(self, angle):
        """Rotate the image by the given angle."""
        self.rotation_angle = (self.rotation_angle + angle) % 360
        self.apply_enhancements()

    def on_zoom_entry(self, event):
        """Handle manual zoom entry changes."""
        try:
            zoom_factor = float(self.zoom_entry.get())
            if zoom_factor < 0.01:
                zoom_factor = 0.01
            elif zoom_factor > 3.0:
                zoom_factor = 3.0
            self.zoom_level.set(zoom_factor)
            self.zoom_slider.set(zoom_factor)  # Sync the slider with the entry
            self.update_image_zoom(zoom_factor)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for zoom level.")

    def on_image_select(self, event):
        # Load the image when a file is selected from the listbox
        selected_index = self.image_listbox.curselection()
        if selected_index:
            self.load_image(selected_index[0])

    def next_image(self):
        # Increment the current image index and load the next image
        next_image_index = self.current_image_index.get() + 1
        self.load_image(next_image_index)

    def previous_image(self):
        # Decrement the current image index and load the previous image
        prev_image_index = self.current_image_index.get() - 1
        self.load_image(prev_image_index)

    def delete_image(self):
        # Delete the current image and move to the next one
        index = self.current_image_index.get()
        filename = os.path.join(self.curr_dir.get(), self.images[index])
        if os.path.isfile(filename):
            os.remove(filename)
            self.warning_message.set(f"Image {filename} deleted.")
            self.images.pop(index)
            self.image_listbox.delete(index)
            self.load_image(index)

    def update_progress_bar(self):
        """Update the progress bar based on the current image position."""
        total_images = len(self.images)
        current_progress = self.current_image_index.get() + 1
        self.progress['value'] = (current_progress / total_images) * 100

    def save_image(self):
        """Save the current image with modifications."""
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output directory.")
            return

        filename = self.filename.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please enter a filename.")
            return

        output_format = self.output_format.get().strip().lower()

        filepath = os.path.join(self.output_dir.get(), f"{filename}.{output_format.lower()}")

        try:
            image = self.apply_enhancements_to_image(self.original_image)
            image = image.rotate(self.rotation_angle, expand=True)
            image.save(filepath, format=output_format.upper())
            messagebox.showinfo("Success", f"Image saved as {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")


if __name__ == "__main__":
    app = ImageProcessorApp()
    app.mainloop()
