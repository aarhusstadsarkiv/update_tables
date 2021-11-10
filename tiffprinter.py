from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pathlib import Path


def stringToTiffPrinter(input: str, dest: Path) -> None:
    """
    * Takes a string to print, and a destination to save it at

    * Creates a tiff at the given destination

    * Requires: libtiff

    * Assumption: the dest value ends in .tiff (or .tif)

    * Assumption: the dest value is a valid path
    """

    # To figure out the dimensions required for our
    # tiff, we'll need to make an unused test img first
    img: Image = Image.new("1", (5, 5))
    d: ImageDraw = ImageDraw.Draw(img)
    # Calculate how much we need to print,
    # so we can create a tiff of a suitable size
    textWidth: int = 0
    textHeight: int = 0

    # We'll also need a font, to calculate size
    # and to actually make the text later!
    try:
        textFont = ImageFont.truetype("consola.ttf", 18)
    # for ubuntu compatibility
    except OSError:
        textFont = ImageFont.truetype("DejaVuSansMono.ttf", 20)

    textVerticalMargin: int = 20
    textHorizontalMargin: int = 16
    textVerticalSpacing: int = 10

    # Also figure out how tall and wide the strings are gonna be
    textWidth, textHeight = d.multiline_textsize(
        input, font=textFont, spacing=textVerticalSpacing
    )

    # Dimensions of image:
    #   Width:  Horizontal margin x 2
    #           + the width of the text
    #   Height: Vertical margin x 2
    #           + the height of the text
    tiffFile: Image = Image.new(
        "1",
        (
            textHorizontalMargin * 2 + textWidth,
            textVerticalMargin * 2 + textHeight,
        ),
        1,
    )
    tiffDraw: ImageDraw = ImageDraw.Draw(tiffFile)

    # and now we can finally draw the image
    tiffDraw.multiline_text(
        (textHorizontalMargin, textVerticalMargin),
        input,
        fill=0,
        font=textFont,
        spacing=textVerticalSpacing,
    )

    # And then save it
    tiffFile.save(dest.as_posix(), format="tiff", compression="group4")
    # tiffFile.save(dest)