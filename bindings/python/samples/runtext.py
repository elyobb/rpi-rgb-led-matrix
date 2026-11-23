
#!/usr/bin/env python
# Display a runtext with double-buffering.
from samplebase import SampleBase
from rgbmatrix import graphics
import time
import random

FORTUNES_FILE = "fortunes.txt"

# Animation settings
SCROLL_SPEED = 0.03
CHASE_SPEED = 0.20
CHASE_SPACING = 2
CHASE_GAP = 1
PAUSE_DURATION = 1.5
RUN_DURATION = 180

# Border brightness
BORDER_BRIGHTNESS = 0.50

gold_r = int(255 * BORDER_BRIGHTNESS)
gold_g = int(215 * BORDER_BRIGHTNESS)
gold_b = 0

gold = graphics.Color(gold_r, gold_g, gold_b)


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
    gold,  # Gold
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
        self.parser.add_argument(
            "-t", "--text",
            help="The text to scroll on the RGB LED panel",
            default="Hello world!"
        )

    def get_fortune(self):
        with open(FORTUNES_FILE) as f:
            lines = f.readlines()
        return random.choice(lines).strip()

    def run(self):
        offscreen_canvas = self.matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont("../../../fonts/8x13.bdf")
        textColor = random.choice(COLORS)

        w = offscreen_canvas.width
        h = offscreen_canvas.height

        pos = w
        my_text = self.get_fortune()

        font_height = 13
        y = (h + font_height) // 2 - 2

        # Build clockwise border path
        border_pixels = []

        # Top edge: left to right
        for x in range(w):
            border_pixels.append((x, 0))

        # Right edge: top to bottom
        for by in range(1, h):
            border_pixels.append((w - 1, by))

        # Bottom edge: right to left
        for x in range(w - 2, -1, -1):
            border_pixels.append((x, h - 1))

        # Left edge: bottom to top
        for by in range(h - 2, 0, -1):
            border_pixels.append((0, by))

        # Animation timers
        startTime = time.monotonic()
        endTime = startTime + RUN_DURATION
        chase_start = startTime
        pause_until = 0

        while time.monotonic() < endTime:
            offscreen_canvas.Clear()
            now = time.monotonic()

            # Draw scrolling text unless paused
            if now >= pause_until:

                text_len = graphics.DrawText(
                    offscreen_canvas,
                    font,
                    pos,
                    y,
                    textColor,
                    my_text
                )

                pos -= 1

                # Pause before restarting text
                if pos + text_len < 0:
                    pos = w
                    pause_until = now + PAUSE_DURATION

            # Calculate current border animation phase
            chase_offset = int(
                (now - chase_start) / CHASE_SPEED
            )

            # Draw alternating gold border
            for i, (bx, by) in enumerate(border_pixels):

                if (i - chase_offset) % CHASE_SPACING < CHASE_GAP:

                    # LED off
                    offscreen_canvas.SetPixel(
                        bx, by, 0, 0, 0
                    )

                else:

                    # LED on
                    offscreen_canvas.SetPixel(
                        bx, by, gold_r, gold_g, gold_b
                    )

            # Display completed frame
            offscreen_canvas = self.matrix.SwapOnVSync(
                offscreen_canvas
            )

            time.sleep(SCROLL_SPEED)

        # Clear the display when finished
        offscreen_canvas.Clear()
        self.matrix.SwapOnVSync(offscreen_canvas)


# Main function
if __name__ == "__main__":
    run_text = RunText()
    if not run_text.process():
        run_text.print_help()
