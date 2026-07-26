#!/usr/bin/env python3

import signal
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence
from rgbmatrix import RGBMatrix, RGBMatrixOptions


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

PANEL_WIDTH = 64
PANEL_HEIGHT = 32

ANIMATION_WIDTH = 32
ANIMATION_HEIGHT = 32

GIF_FILE = "blob.gif"

TEXT_VALUES = ["foo", "bar"]
TEXT_CHANGE_SECONDS = 2.0

BRIGHTNESS = 20
GPIO_SLOWDOWN = 4

# For pixel-art GIFs, NEAREST keeps hard pixel edges.
# Change this to Image.Resampling.LANCZOS for smoother artwork.
RESIZE_METHOD = Image.Resampling.NEAREST


def configure_matrix() -> RGBMatrix:
    options = RGBMatrixOptions()

    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1

    options.brightness = BRIGHTNESS
    options.gpio_slowdown = GPIO_SLOWDOWN

    # Equivalent to --led-no-hardware-pulse.
    options.disable_hardware_pulsing = True

    # Use this when the Adafruit HAT mapping was not compiled in
    # as your default mapping.
    options.hardware_mapping = "adafruit-hat"

    return RGBMatrix(options=options)


def load_gif_frames(filename: str):
    """
    Load the GIF before creating the matrix.

    The matrix library may drop root privileges after initialization,
    which can affect later file access.
    """
    gif_path = Path(filename)

    if not gif_path.is_file():
        raise FileNotFoundError(f"GIF not found: {gif_path.resolve()}")

    frames = []
    durations = []

    with Image.open(gif_path) as gif:
        for source_frame in ImageSequence.Iterator(gif):
            frame = source_frame.convert("RGBA")

            # Force every animation frame into the left 32x32 area.
            frame = frame.resize(
                (ANIMATION_WIDTH, ANIMATION_HEIGHT),
                RESIZE_METHOD
            )

            # Place transparency over a black background.
            background = Image.new(
                "RGBA",
                (ANIMATION_WIDTH, ANIMATION_HEIGHT),
                (0, 0, 0, 255)
            )
            background.alpha_composite(frame)

            frames.append(background.convert("RGB"))

            # GIF duration is stored in milliseconds.
            duration_ms = source_frame.info.get(
                "duration",
                gif.info.get("duration", 100)
            )

            # Avoid frames running unreasonably fast when duration is
            # absent or set to zero.
            duration_seconds = max(duration_ms / 1000.0, 0.02)
            durations.append(duration_seconds)

    if not frames:
        raise ValueError("The GIF does not contain any frames.")

    return frames, durations


def load_font():
    """
    Try a small TrueType font first. Fall back to Pillow's built-in font.
    """
    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for filename in possible_fonts:
        if Path(filename).is_file():
            return ImageFont.truetype(filename, 11)

    return ImageFont.load_default()


def draw_centered_text(
    frame: Image.Image,
    text: str,
    font: ImageFont.ImageFont
):
    draw = ImageDraw.Draw(frame)

    # Right half of the physical panel.
    area_left = 32
    area_top = 0
    area_width = 32
    area_height = 32

    # Determine the actual rendered text dimensions.
    bounding_box = draw.textbbox((0, 0), text, font=font)

    text_width = bounding_box[2] - bounding_box[0]
    text_height = bounding_box[3] - bounding_box[1]

    x = area_left + (area_width - text_width) // 2
    y = area_top + (area_height - text_height) // 2

    # Compensate for font bearings so visual centering is correct.
    x -= bounding_box[0]
    y -= bounding_box[1]

    draw.text(
        (x, y),
        text,
        font=font,
        fill=(255, 255, 255)
    )


def main():
    # Load files before matrix initialization.
    gif_frames, gif_durations = load_gif_frames(GIF_FILE)
    font = load_font()

    matrix = configure_matrix()
    offscreen_canvas = matrix.CreateFrameCanvas()

    animation_index = 0
    text_index = 0

    now = time.monotonic()
    next_animation_change = now + gif_durations[animation_index]
    next_text_change = now + TEXT_CHANGE_SECONDS

    running = True

    def stop_program(_signal_number, _stack_frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop_program)
    signal.signal(signal.SIGTERM, stop_program)

    while running:
        now = time.monotonic()

        # Advance the GIF independently of the text.
        if now >= next_animation_change:
            animation_index = (animation_index + 1) % len(gif_frames)
            next_animation_change += gif_durations[animation_index]

            # Recover gracefully if the program was delayed heavily.
            if next_animation_change < now:
                next_animation_change = (
                    now + gif_durations[animation_index]
                )

        # Change foo/bar independently of the GIF.
        if now >= next_text_change:
            text_index = (text_index + 1) % len(TEXT_VALUES)
            next_text_change += TEXT_CHANGE_SECONDS

            if next_text_change < now:
                next_text_change = now + TEXT_CHANGE_SECONDS

        # Construct one complete 64x32 image.
        output_frame = Image.new(
            "RGB",
            (PANEL_WIDTH, PANEL_HEIGHT),
            (0, 0, 0)
        )

        # Animation goes at x=0 through x=31.
        output_frame.paste(
            gif_frames[animation_index],
            (0, 0)
        )

        # Text goes at x=32 through x=63.
        draw_centered_text(
            output_frame,
            TEXT_VALUES[text_index],
            font
        )

        # Draw the entire completed image onto the hidden buffer.
        offscreen_canvas.SetImage(output_frame)

        # Swap it onto the visible panel at vertical sync.
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

        # Small sleep prevents an unnecessary 100%-CPU loop.
        # Frame timing still comes from the GIF's stored durations.
        time.sleep(0.005)

    offscreen_canvas.Clear()
    matrix.SwapOnVSync(offscreen_canvas)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
