from itertools import repeat
from model.base import *
from PIL import Image, ImageDraw
from IPython.display import display, clear_output
import time
from typing import Tuple, List, Final


class CantColourSpeciesError(Exception):
    def __init__(self, species: Species):
        self.species = species
        self.message = f"No colour defined for species {self.species}"


Colour = Tuple[int, int, int]


def colourmap(species: Species) -> Colour:
    if species is None:
        return (0, 0, 0)
    elif species == 0:
        return (170, 150, 50)
    elif species == 1:
        return (181, 45, 45)
    elif species == 2:
        return (45, 45, 181)
    else:
        raise CantColourSpeciesError(species)


def draw_board(
    board: Board,
    img_width: int,
    img_height: int,
    border_params: Tuple[int, int, int, int] | None = None,
    tail_length: int = 0,
) -> Image.Image:

    if img_width < board.get_width() or img_height < board.get_height():
        raise ValueError("Image cannot be smaller than the board itself")

    # We first create the image that we are going to print out (allbeit a very small version of it where each cell is only one pixel)
    img: Image.Image = Image.new("RGB", (board.get_width(), board.get_height()))
    for i in range(board.get_width()):
        for j in range(board.get_height()):
            img.putpixel((i, j), colourmap(board[(i, j)]))

    # We then resize the image to its full size (as specified by the arguments `img_width` and `img_height`), using box resampling so it stays pixelated
    img = img.resize((img_width, img_height), resample=Image.BOX)

    # We will now start drawing on our image
    drawing: ImageDraw.ImageDraw = ImageDraw.Draw(img)

    # We need to know how big each cell is so that we know where to draw things
    CELL_WIDTH: Final[float] = img_width / board.get_width()
    CELL_HEIGHT: Final[float] = img_height / board.get_height()

    # Let's maybe draw some lines to demarcate borders between cells (did the user ask for that?)
    if isinstance(border_params, tuple):

        neighbourhood_size: int = border_params[0]
        border_colour: Colour = border_params[1:]

        for x in range(int(board.get_width() / neighbourhood_size)):
            drawing.line(
                [
                    (x * neighbourhood_size * CELL_WIDTH, 0),
                    (x * neighbourhood_size * CELL_WIDTH, img_height),
                ],
                fill=border_colour,
                width=1,
            )
        for y in range(int(board.get_height() / neighbourhood_size)):
            drawing.line(
                [
                    (0, y * neighbourhood_size * CELL_HEIGHT),
                    (img_width, y * neighbourhood_size * CELL_HEIGHT),
                ],
                fill=border_colour,
                width=1,
            )

    if tail_length > 0:
        try:
            for ((x0, y0), (x1, y1)) in board.log[-1]:
                drawing.line(
                    [
                        (CELL_WIDTH * (x0 + 0.5), CELL_HEIGHT * (y0 + 0.5)),
                        (CELL_WIDTH * (x1 + 0.5), CELL_HEIGHT * (y1 + 0.5)),
                    ],
                    fill=colourmap(board[(x1, y1)]),
                    width=1,
                )
        except IndexError:
            pass

    # We finally print a little message on the top-right showing the percentage of satisfied agents
    total_satisfied: int = board.get_total_satisfied()
    drawing.text(
        (10, 0),
        "Satisfied: "
        + (
            "everyone"
            if total_satisfied == board.get_total_population()
            else str(round(100 * total_satisfied / board.get_total_population())) + "%"
        ),
    )

    # Congradulations! We're done :)
    return img


def animate_schelling(
    board: Board,
    img_width: int,
    img_height: int,
    delay: float,
    border_params: Tuple[int, int, int, int] | None = None,
    tail_length=1,
    max_iter: int | None = None,
    outfile_name: str | None = None,
) -> None:

    if delay < 0:
        raise ValueError("Delay cannot be negative")

    # We will record all the images we display so we can make them into a gif after
    history: List[Image.Image] = list()

    # This for-loop probably looks kind of complicated, but all really all we're saying is do to this `max_iter` times unless `max_iter` is None, in which case just do it forever (or at least until it's broken by something like a keyboard interupt)
    for _ in repeat(None) if max_iter is None else range(max_iter):

        try:

            # We begin the cycle by drawing a board (naturally)
            img = draw_board(
                board=board,
                img_width=img_width,
                img_height=img_height,
                border_params=border_params,
                tail_length=tail_length,
            )

            # We then clear the output (but we will let it wait until its ready to display the next image)
            clear_output(wait=True)

            # Then we print the image out
            display(img)

            # Pause for a moment to let the image sink in
            time.sleep(delay)

            # And save the image to our history so we can make our little gif afterwards
            history.append(img)

            # Then update we update the board and start it all again
            if board.get_proportion_satisfied() == 1.0:
                break
            else:
                board.update()
                continue

        except KeyboardInterrupt:
            break

        finally:

            # Now that everything is finished we first print out the beginning and end for comparison
            clear_output(wait=True)
            print("How it started:")
            display(history[0])
            print()
            print("How it's going:")
            display(history[-1])

            # And if some outfile was specified, we make a little gif
            if isinstance(outfile_name, str):
                print(f'Saving file as "{outfile_name}"...')
                history[0].save(
                    outfile_name,
                    append_images=history[1:],
                    save_all=True,
                    optimize=False,
                    duration=1 if delay == 0 else 1000 * delay,
                    loop=0,
                )
