#!/usr/bin/env python
# Display a runtext with double-buffering.
from samplebase import SampleBase
from rgbmatrix import graphics
import time
import random

FORTUNES_FILE = "fortunes.txt"

COLORS = [
    # Core bright colors
    graphics.Color(255, 0, 0),  # Red
    graphics.Color(0, 255, 0),  # Green
    graphics.Color(0, 0, 255),  # Blue
    graphics.Color(255, 255, 0),  # Yellow
    graphics.Color(0, 255, 255),  # Cyan
    graphics.Color(255, 0, 255),  # Magenta
    graphics.Color(255, 255, 255),  # White

    # Warm tones (very readable)
    graphics.Color(255, 165, 0),  # Orange
    graphics.Color(255, 140, 0),  # Dark orange
    graphics.Color(255, 215, 0),  # Gold
    graphics.Color(255, 192, 203),  # Pink
    graphics.Color(255, 105, 180),  # Hot pink
    graphics.Color(255, 69, 0),  # Orange red

    # Cool tones
    graphics.Color(0, 191, 255),  # Deep sky blue
    graphics.Color(30, 144, 255),  # Dodger blue
    graphics.Color(0, 206, 209),  # Dark turquoise
    graphics.Color(64, 224, 208),  # Turquoise
    graphics.Color(173, 216, 230),  # Light blue

    # Greens (avoid muddy low values)
    graphics.Color(50, 205, 50),  # Lime green
    graphics.Color(0, 250, 154),  # Medium spring green
    graphics.Color(144, 238, 144),  # Light green

    # Purples / violets
    graphics.Color(138, 43, 226),  # Blue violet
    graphics.Color(148, 0, 211),  # Dark violet
    graphics.Color(186, 85, 211),  # Medium orchid
    graphics.Color(221, 160, 221),  # Plum

    # Soft whites (less eye-searing)
    graphics.Color(200, 200, 200),  # Soft white
    graphics.Color(180, 180, 180),  # Dim white
]


class RunText(SampleBase):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to scroll on the RGB LED panel", default="Hello world!")

    def get_fortune(self):
        with open(FORTUNES_FILE) as f:
            lines = f.readlines()
        return random.choice(lines).strip()

    def run(self):
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("../../../fonts/8x13.bdf")
        textColor = random.choice(COLORS)

        pos = offscreen_canvas.width
        my_text = self.get_fortune()

        startTime = time.time()
        endTime = startTime + 120

        while time.time() < endTime:
            offscreen_canvas.Clear()
            font_height = 13  # for 8x13.bdf
            y = (offscreen_canvas.height + font_height) // 2 - 2
            text_len = graphics.DrawText(offscreen_canvas, font, pos, y, textColor, my_text)
            pos -= 1
            if (pos + text_len < 0):
                pos = offscreen_canvas.width

            time.sleep(0.035)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
        offscreen_canvas.Clear()



# Main function
if __name__ == "__main__":
    run_text = RunText()
    if not run_text.process():
        run_text.print_help()
