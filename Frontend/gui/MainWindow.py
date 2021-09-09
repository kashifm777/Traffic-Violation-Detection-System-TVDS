import queue
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog

from gui.SelectDevice import *
from gui.ConfigureRecording import *
from pygrabber.PyGrabber import *
from pygrabber.image_process import *


class MainWindow:
    def __init__(self, master):
        self.create_gui(master)
        self.grabber = PyGrabber(self.on_image_received)
        self.queue = queue.Queue()
        self.image = None
        self.original_image = None
        self.select_device()

    def create_gui(self, master):
        self.master = master
        master.title("Traffic Violation Detector")
        self.create_menu(master)

        master.columnconfigure(0, weight=1, uniform="group1")
        master.columnconfigure(1, weight=1, uniform="group1")
        master.rowconfigure(0, weight=1)

        self.video_area = Frame(master, bg='gray')
        self.video_area.grid(row=0, column=0, sticky=W+E+N+S, padx=5, pady=5)

        self.status_area = Frame(master)
        self.status_area.grid(row=1, column=0, sticky=W+E+N+S, padx=5, pady=5)

        self.image_area = Frame(master)
        self.image_area.grid(row=0, column=1, sticky=W+E+N+S, padx=5, pady=5)

        self.image_controls_area = Frame(master)
        self.image_controls_area.grid(row=1, column=1, padx=5, pady=0)

        self.image_controls_area2 = Frame(master)
        self.image_controls_area2.grid(row=2, column=1, padx=5, pady=0)

        # Grabbed image
        fig = Figure(figsize=(5, 4), dpi=100)
        self.plot = fig.add_subplot(111)
        self.plot.axis('off')

        self.canvas = FigureCanvasTkAgg(fig, master=self.image_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=1)

        # Status
        self.lbl_status1 = Label(self.status_area, text="Device Error")
        self.lbl_status1.grid(row=0, column=0, padx=5, pady=5, sticky=W)

        # Image controls
        self.grab_btn = Button(self.image_controls_area, text="Capture", command=self.capture_frame).pack(padx=5, pady=20, side=LEFT)

        self.image_filter_4_btn = Button(self.image_controls_area2, text="Detect", command=(self.capture_frame)).pack(padx=5, pady=2, side=LEFT)

        self.save_btn = Button(self.image_controls_area2, text="Save", command=self.save_image).pack(padx=5, pady=2, side=LEFT)

        self.video_area.bind("<Configure>", self.on_resize)

    def create_menu(self, master):
        menubar = Menu(master)
        self.master.config(menu=menubar)

        camera_menu = Menu(menubar)
        camera_menu.add_command(label="Open", command=self.change_camera)
        camera_menu.add_command(label="Properties", command=self.camera_properties)
        camera_menu.add_command(label="Format", command=self.set_format)
        camera_menu.add_command(label="Preview", command=self.start_preview)
        camera_menu.add_command(label="Stop", command=self.stop)
        menubar.add_cascade(label="Camera", menu=camera_menu)

        image_menu = Menu(menubar)
        image_menu.add_command(label="Capture", command=self.capture_frame)
        image_menu.add_command(label="Save", command=self.save_image)
        menubar.add_cascade(label="Image", menu=image_menu)

    def display_image(self):
        while self.queue.qsize():
            try:
                self.image = self.queue.get(0)
                self.original_image = self.image
                self.plot.imshow(np.flip(self.image, axis=2))
                self.canvas.draw()
            except queue.Empty:
                pass
        self.master.after(100, self.display_image)

    def select_device(self):
        input_dialog = SelectDevice(self.master, self.grabber.get_video_devices())
        self.master.wait_window(input_dialog.top)
        # no device selected
        if input_dialog.device_id is None:
            exit()

        self.grabber.set_device(input_dialog.device_id)
        self.grabber.start_preview(self.video_area.winfo_id())
        self.display_status(self.grabber.get_status())
        self.on_resize(None)
        self.display_image()

    def display_status(self, status):
        self.lbl_status1.config(text=status)

    def change_camera(self):
        self.grabber.stop()
        del self.grabber
        self.grabber = PyGrabber(self.on_image_received)
        self.select_device()

    def camera_properties(self):
        self.grabber.set_device_properties()

    def set_format(self):
        self.grabber.display_format_dialog()

    def on_resize(self, event):
        self.grabber.update_window(self.video_area.winfo_width(), self.video_area.winfo_height())

    def init_device(self):
        self.grabber.start()

    def capture_frame(self):
        self.grabber.capture_frame()

    def on_image_received(self, image):
        self.queue.put(image)

    def start_preview(self):
        self.grabber.start_preview(self.video_area.winfo_id())
        self.display_status(self.grabber.get_status())
        self.on_resize(None)

    def stop(self):
        self.grabber.stop()
        self.display_status(self.grabber.get_status())

    def save_image(self):
        filename = filedialog.asksaveasfilename(
            initialdir="/",
            title="Select file",
            filetypes=[('PNG', ".png".format), ('JPEG', ".jpg".format)])
        if filename is not None:
            save_image(filename, self.image)
        

    