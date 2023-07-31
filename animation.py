from board import *
from PIL import Image, ImageDraw
from IPython.display import display, clear_output
import time

Colour = Tuple[int, int, int]


def colourmap(species: int) -> Colour:
    if species == -1:
        return (0, 0, 0)
    elif species == 0:
        return (170, 150, 50)
    elif species == 1:
        return (181, 45, 45)
    elif species == 2:
        return (45, 45, 181)
    else:
        raise NoSuchSpeciesError()


def animate_schelling(
    board_width: int,
    board_height: int,
    img_width: int,
    img_height: int,
    fill_proportion: float,
    delay: float,
    number_of_species: int,
    thresholds: int | Tuple[int, ...],
    proximity_bias: float | Tuple[float, ...],
    border_colour: Optional[Colour] = None,
    display_conspecificity: bool = False,
    record_moves: bool = False,
    outfile_name: Optional[str] = None,
    max_iter: int = -1,
) -> None:

    assert board_width > 0
    assert board_height > 0
    assert img_width >= board_width
    assert img_height >= board_height
    assert 0 <= fill_proportion <= 1
    assert delay >= 0

    board: Board = Board(
        shape=(board_width, board_height),
        n=int((board_width * board_height / number_of_species) * fill_proportion),
        thresholds=thresholds,
        k=number_of_species,
        proximity_bias=proximity_bias,
        record_moves=record_moves,
    )

    assert img_width >= board.shape[X] and img_height >= board.shape[Y]

    def draw_board() -> Image.Image:
        img: Image.Image = Image.new("RGB", board.shape)
        for i in range(board.shape[X]):
            for j in range(board.shape[Y]):
                img.putpixel((i, j), colourmap(board[(i, j)]))
        img = img.resize((img_width, img_height), resample=Image.BOX)

        draw: ImageDraw.ImageDraw = ImageDraw.Draw(img)

        cell_width: float = img_width / board.shape[X]
        cell_height: float = img_height / board.shape[Y]

        if display_conspecificity:
            for i in range(board.shape[X]):
                for j in range(board.shape[Y]):
                    if board[(i, j)] != -1:
                        draw.text(
                            (int(i * cell_width) + 10, int(j * cell_height)),
                            str(round(100 * board.conspecificity((i, j)))) + "% ",
                        )
                        draw.text(
                            (int(i * cell_width) + 10, int((j + 0.5) * cell_height)),
                            ":)" if board.is_satisfied((i, j)) else ":(",
                        )

        if isinstance(border_colour, tuple):
            for i in range(board.shape[X]):
                for y in range(img_height):
                    img.putpixel((int(i * cell_width), y), border_colour)
            for y in range(img_height):
                img.putpixel((img_width - 1, y), border_colour)
            for j in range(board.shape[Y]):
                for x in range(img_width):
                    img.putpixel((x, int(j * cell_height)), border_colour)
            for x in range(img_width):
                img.putpixel((x, img_height - 1), border_colour)

        if isinstance(board.log, list):
            try:
                for (start, end) in board.log[-1]:
                    draw.line(
                        [
                            (
                                cell_width * (start[X] + 0.5),
                                cell_height * (start[Y] + 0.5),
                            ),
                            (cell_width * (end[X] + 0.5), cell_height * (end[Y] + 0.5)),
                        ],
                        fill=colourmap(board[end]),
                        width=1,
                    )
            except IndexError:
                pass

        total_satisfied: int = board.total_satisfied()
        draw.text(
            (10, 0),
            "Satisfied: "
            + (
                "everyone"
                if total_satisfied == board.number_of_agents
                else str(round(100 * total_satisfied / board.number_of_agents)) + "%"
            ),
        )

        return img

    history: List[Image.Image] = list()

    iteration_number: int = 0
    while iteration_number != max_iter:
        try:
            img = draw_board()
            clear_output(wait=True)
            display(img)
            time.sleep(delay)
            board.update()
            history.append(img)
            iteration_number += 1

        except KeyboardInterrupt:
            break

    clear_output(wait=True)
    print("How it started:")
    display(history[0])
    print()
    print("How it's going:")
    display(history[-1])

    if isinstance(outfile_name, str):
        print('Saving file as "' + outfile_name + '"...')
        history[0].save(
            outfile_name,
            append_images=history[1:],
            save_all=True,
            optimize=False,
            duration=1 if delay == 0 else 1000 * delay,
            loop=0,
        )
