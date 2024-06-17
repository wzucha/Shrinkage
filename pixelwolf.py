# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 19:55:43 2024

@author: wzucha
"""

import cv2
import numpy as np
from pathlib import Path
import PySimpleGUI as sg

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


def calculate_pixels(image,
                      center_x:float,
                      center_y:float,
                      radius:float,
                      upper_threshold:float,
                      lower_threshold:float):

    # Get center
    center = (center_x, center_y)
    
    # Read image // input is already cv2.imread object
    #image = cv2.imread(image_path, cv2.IMREAD_COLOR)

    # Convert image to grayscale
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Create a mask for the circle
    mask = np.zeros_like(grayscale_image)
    cv2.circle(mask, center, radius, (255), thickness=-1)

    # Apply the circle mask to the grayscale image
    grayscale_image_within_circle = cv2.bitwise_and(grayscale_image, grayscale_image, mask=mask)

    # Count the total number of pixels within the circle
    total_pixels_within_circle = np.count_nonzero(mask == 255)

    # Count the number of black pixels within the circle

    threeshold = upper_threshold
    threeshold2 = lower_threshold
    black_pixel_count = np.count_nonzero(np.logical_and(grayscale_image_within_circle > threeshold2, grayscale_image_within_circle < threeshold))

    # Calculate the percentage of black pixels
    percentage_of_black_pixels = (black_pixel_count / total_pixels_within_circle) * 100

    grayscale_array = np.logical_and(grayscale_image_within_circle > threeshold2, grayscale_image_within_circle < threeshold)
    
    black_pixel_mask = (grayscale_array).astype(np.uint8)

    red_image = image.copy()
    red_image[:, :, 0] = np.maximum(red_image[:, :, 0], 255 * black_pixel_mask)

    # Data to plot with imshow()

    raw_data = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    temp = cv2.cvtColor(red_image, cv2.COLOR_BGR2RGB)
    eval_data = cv2.circle(temp, center, radius, (255), thickness=1)
    return percentage_of_black_pixels, raw_data, eval_data

class picture():
    def __init__(self, path):
        self.raw:float
        self.data:float
        self.sample:str
        self.path:str
        self.percent_shrinkage:float

        self.height:float
        self.width:float
        self.radius:float
        self.center_x:float
        self.center_y:float
        self.upper_threshold = 140
        self.lower_threshold = 0


        self.set_image(path)
        self.set_data()


    def set_image(self, path):
        self.image = cv2.imread(path, cv2.IMREAD_COLOR)
        self.sample = Path(path)

        self.height = self.image.shape[0]
        self.width = self.image.shape[1]

        # get data for picture
        self.center_x = int(self.image.shape[0]/2)
        self.center_y = int(self.image.shape[1]/2)
        self.radius = np.minimum(self.height, self.width)/3
        self.radius = int(self.radius)

    def set_data(self):

        data = calculate_pixels(self.image, self.center_x, self.center_y,
                                self.radius, self.upper_threshold,
                                self.lower_threshold)

        self.percent_shrinkage = data[0]
        self.raw_data = data[1]
        self.eval_data = data[2]




############################ G U I #######################################

def draw_figure(canvas, figure):
    """
    This function help
    --------
    Input: the GUI canvas, the fig from matplotlib
    -------
    Returns: the Matplotlib one can embedd in the GUI
    """
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=0)
    return figure_canvas_agg

def text(ax, instance):
    text = f"""Total shrinkage is {instance.percent_shrinkage:.2f}%\n
Settings are:\n
center_x: {instance.center_x}, center_y: {instance.center_y}\n
radius: {instance.radius}\n
upper limit: {instance.upper_threshold}, lower limit: {instance.lower_threshold}\n
filename is {instance.sample.name}
    """
    ax.text(0.1,0.2, text, fontsize=6)
    ax.axis('off')
    return ax

class GUI():

    def __init__(self, path:str):
        # load classes
        self.pic = picture(path)


        col2 = [[sg.T("Change center of circle (x|y)")],
                [self.x_center(), self.y_center()],
                [sg.T("Set radius")],
                [self.radius()],
                [sg.T("Set lower and upper boundary of grayscale")],
                [self.lower(),self.upper()],
                [self.button()]
                ]


        layout = [
            [sg.Canvas(key="CANVAS"), sg.Col(col2)]
            ]
        # axis labels

        plt.rc('font', size=6)
        plt.rcParams['font.sans-serif'] = "Arial"
        self.fig, (self.ax, self.ax1) = plt.subplots(1,2,figsize=(4, 3),
                                                     dpi=300)

        self.ax = text(self.ax, self.pic)
        self.ax1.imshow(self.pic.eval_data)

        self.window = sg.Window("Pixelwolf", layout, finalize=True,
                                location=(0, 0))

        draw_figure(self.window["CANVAS"].TKCanvas, self.fig)


    def x_center(self):
        reso = int(self.pic.width/100)
        return sg.Slider(range=(0, self.pic.width), key="x_center",
                         default_value=self.pic.center_x, resolution=reso,
                         orientation="h", enable_events=True)

    def y_center(self):
        reso = int(self.pic.height/100)
        return sg.Slider(range=(0, self.pic.height), key="y_center",
                         default_value=self.pic.center_y, resolution=reso,
                         orientation="h", enable_events=True)

    def radius(self):
        maxi = np.minimum(self.pic.height, self.pic.width)
        reso = int(np.minimum(self.pic.height, self.pic.width)/100)
        return sg.Slider(range=(1, maxi), key="radius",
                         default_value=self.pic.radius, resolution=reso,
                         orientation="h", enable_events=True)

    def upper(self):
        return sg.Slider(range=(0, 255), key="upper",
                         default_value=100, resolution=1,
                         orientation="h", enable_events=True)

    def lower(self):
        return sg.Slider(range=(0, 255), key="lower",
                         default_value=0, resolution=1,
                         orientation="h", enable_events=True)

    def button(self):
        return sg.Button("Save", key="save")


################ GUI FUNC #########################

    def plot(self, values):

        self.pic.center_x = int(values["x_center"])
        self.pic.center_y = int(values["y_center"])
        self.pic.radius = int(values["radius"])
        self.pic.upper_threshold = values["upper"]
        self.pic.lower_threshold = values["lower"]


        self.pic.set_data()
        self.ax.clear()
        self.ax1.clear()
        self.ax = text(self.ax, self.pic)
        self.ax1.imshow(self.pic.eval_data)

        self.fig.canvas.draw()

    def save(self):
        self.fig.savefig(str(self.pic.sample.parent)+"/"+self.pic.sample.stem+".pdf")

def main():
    path = sg.popup_get_file("Get file (.png/.jpg)")
    g = GUI(path)

    function = {"save":g.save}

    function2 = {"x_center":g.plot,
                 "y_center":g.plot,
                 "radius":g.plot,
                 "upper":g.plot,
                 "lower":g.plot}

    while True:

        event, values = g.window.read()

        if event in (sg.WINDOW_CLOSED, 'Exit'):
            break
        if event in function:
            function[event]()

        if event in function2:
            function2[event](values)

    g.window.close()

if __name__ == "__main__":
    main()
