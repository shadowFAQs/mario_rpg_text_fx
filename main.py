import re
import sys

from string import ascii_lowercase

import pygame


BG_COLOR = '#635045'  # Change this to update background color


class Text(object):
    def __init__(self, fonts: list[dict], colors: list[pygame.Color],
                 text: str, dims: tuple[int]):
        self.colors = colors
        self.cooldown = 50   # How long to wait, after animation is
        self.dims = dims     # complete, before clearing text
        self.flash = True
        self.flash_counter = 0
        self.flash_flip = 3  # Frame delay for "bulb" flash
        self.flash_max = 6   # Frame delay before flash cycle restarts
        self.font_bright = fonts[1]
        self.font_dim = fonts[0]
        self.letter_dims = self.font_dim['a'].get_size()
        self.surf = pygame.Surface(dims)
        self.text = text
        self.x_offsets = [0]
        self.y_offset = 0

        self.create_text_objs()
        self.surf.set_colorkey(self.colors['transparent'])

    def clear_text(self):
        self.flash_counter = 0
        self.text_objs = []
        self.surf.fill(pygame.Color('#ff00ff'))

    def create_text_objs(self):
        """
        Clears self.text_objs, calls self.split_lines(), sets x and y
        offsets (to center each line of text), and creates a dict for
        each letter in self.text. These dicts contain 2 surfaces -- a
        bright one and a dim one. The flash/strobe effect just switches
        between which one is blitted to the screen.

        text_obj properties:
        ------------+----------------+----------------------------------
        counter     | int            | Used with "warmup" to
                    |                | determine if the letter is ready
                    |                | to appear on the screen yet
        line        | int            | The line the letter is on (0-2)
        surf_bright | pygame.Surface | "Bulb on" surface
        surf_dim    | pygame.Surface | "Bulb off" surface
        vy          | float          | Vertical velocity
        warmup      | int            | Number of frames before letter is
                    |                | slated to appear on-screen*
        x           | int            | Letter's x position in pixels
        x_offset    | float          | "Padding" from the left to the
                    |                | start of letter's line
        y           | int            | Letter's "floor" y coordinate;
                    |                | used to set y coordinate
                    |                | on-screen and determine if letter
                    |                | has completed its animation
        y_offset    | float          | "Padding" from the top to the
                    |                | start of letter's line

        *Note: The timing for when a letter is "ready" to pop up is a
        little complicated. This is my best attempt at recreating the
        original game effect-- The letters wipe, roughly, from
        northwest to southeast. Full formula:
            round(
                (length of longest line - len of letter's line) / 2 * 3
                +
                letter's "x" position in its line * 3
                +
                letter's line number * 4
            )
        """

        self.text_objs = []
        lines = self.split_lines()

        # Horizontal centering values for each line
        self.x_offsets = [(self.dims[0] / 2) \
            - (len(l) * self.letter_dims[0]) / 2 for l in lines]

        # Vertical centering value for text block
        self.y_offset = (self.dims[1] / 2) \
            - ((self.letter_dims[1] / 2) * len(lines))

        for l, line in enumerate(lines):
            diff = (max([len(l) for l in lines]) - len(line)) / 2
            for n, letter in enumerate(line):
                self.text_objs.append({
                    'counter': 0,
                    'line': l,
                    'surf_bright': self.font_bright[letter],
                    'surf_dim': self.font_dim[letter],
                    'vy': -7.0,
                    'warmup': round((3 * diff) + (3 * n) + (l * 4)),
                    'x': n * self.letter_dims[0],
                    'x_offset': self.x_offsets[l],
                    'y': 0,
                    'y_offset': l * self.letter_dims[1] + l * 4
                })

    def print_text(self):
        self.surf.fill(pygame.Color('#ff00ff'))
        current_surf = 'surf_dim' if self.flash_counter < self.flash_flip \
            else 'surf_bright'

        for n, obj in enumerate(self.text_objs):
            if obj['counter'] == obj['warmup']:
                obj['vy'] += .4
                obj['vy'] *= .98
                obj['y'] += obj['vy']

                if obj['y'] > 0:
                    obj['y'] = 0
                    obj['vy'] *= -.4

                self.surf.blit(
                    obj[current_surf],
                    dest=(obj['x'] + obj['x_offset'],
                          obj['y'] + obj['y_offset'] + self.y_offset))

    def split_lines(self) -> list[str]:
        """
        Shortens any words longer than [maxlen] to [maxlen] - 3, and
        appends "..." to the end of them:
            "ausgezeichnet" -> "ausge..." (maxlen = 8)

        Groups words into lines such that each line will not have more
        than maxlen characters in it:
            "let's go pikachu!" -> LET'S GO
                                   PIKACHU!

        If more than [maxlines] would be created this way, returns only
        lines 0 through [maxlines - 1], appending "..." at the end:
                                              DON'T
           "don't get too cocky starfox" ->  GET TOO
                                             COCKY...
        """

        maxlen = 8
        maxlines = 3

        words = [w if len(w) <= maxlen else w[:maxlen - 3] + '...' for w in self.text.split(' ')]
        lines = []

        for word in words:
            try:
                if len(word) + len("".join(lines[-1])) \
                    + len(lines[-1]) > maxlen:
                    if len(lines) < maxlines:
                        lines.append([])
                    else:
                        if len(' '.join(lines[-1])) > maxlen - 3:
                            line = ' '.join(lines[-1])[:maxlen - 3] + '...'
                            lines[-1] = line.split(' ')
                        else:
                            lines[-1][-1].append('...')
                        break
            except IndexError:
                lines.append([])

            lines[-1].append(word)

        return [' '.join(l) for l in lines]

    def update(self):
        for obj in self.text_objs:
            if obj['counter'] < obj['warmup']:
                obj['counter'] += 1

        if self.flash:
            self.flash_counter += 1
            if self.flash_counter == self.flash_max:
                self.flash_counter = 0
            self.print_text()

        if not [o for o in self.text_objs if o['y']]:
            if self.cooldown:
                self.cooldown -= 1
            else:
                self.flash = False
                self.clear_text()


def load_font(colors) -> list[dict]:
    """Load "font" from image file.

    Creates dictionaries with keys equal to each
    supported letter and values being instances
    of pygame.Surface.

    Returns "dim" and "bright" versions of this
    font.
    """

    font_bright = {}
    font_dim = {}
    letter_dims = (16, 16)
    sheet = pygame.image.load('pixel_alphabet.png')
    upscaled = pygame.transform.scale(sheet, tuple([n * 2 for n in sheet.get_size()]))

    # Dim font for flash effect
    for n, letter in enumerate(ascii_lowercase + '.!\' '):
        letter_surface = pygame.Surface(letter_dims)
        letter_surface.blit(upscaled, dest=((-1 * n * letter_dims[0]), 0))
        font_dim[letter] = letter_surface

    # Bright font for flash effect
    pxarray = pygame.PixelArray(upscaled)
    pxarray.replace(color=colors['dim'], repcolor=colors['bright'], distance=.5)
    bright = pxarray.make_surface()
    for n, letter in enumerate(ascii_lowercase + '.!\' '):
        letter_surface = pygame.Surface(letter_dims)
        letter_surface.blit(bright, dest=((-1 * n * letter_dims[0]), 0))
        font_bright[letter] = letter_surface

    return [font_dim, font_bright]


def validate_input(string: str) -> bool:
    """Test input for supported characters.

    Only alpha characters, ., !, single quote,
    and space are allowed.
    """

    search = search=re.compile(r'[^a-z\.!\' ]').search
    return not bool(search(string))


def main(text: str):
    pygame.init()
    global BG_COLOR
    BG_COLOR = pygame.Color(BG_COLOR)

    dims = (300, 200)
    pygame.display.set_caption('Mario RPG text effect')
    window_surface = pygame.display.set_mode(dims)
    window_surface.fill(BG_COLOR)
    clock = pygame.time.Clock()
    is_running = True

    colors = {
        'bright': pygame.Color('#f8eae5'),     # "Bulb on" yellow
        'dim': pygame.Color('#dfbb35'),        # "Bulb off" yellow
        'transparent': pygame.Color('#ff00ff') # "Ignore me" purple
    }
    fonts = load_font(colors)
    text_surf = None

    while is_running:
        clock.tick(60)  # Set FPS

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.MOUSEBUTTONDOWN: # Click to create
                if text_surf:                          # text FX
                    if not text_surf.text_objs:
                        text_surf = Text(fonts, colors, text, dims)
                else:
                    text_surf = Text(fonts, colors, text, dims)

        window_surface.fill(BG_COLOR)

        if text_surf:
            text_surf.update()
            window_surface.blit(text_surf.surf, dest=(0, 0))

        pygame.display.update()


if __name__ == '__main__':
    try:
        text = sys.argv[1].lower() # Lowercase everything, since the font
    except IndexError:             # only has a single case.
        text = 'level up!'

    if validate_input(text):
        main(text)
    else:
        print('\nFor the input string, only alpha characters, ' \
              '".", "!", "\'" (single quote) and " " (space) are allowed.')
