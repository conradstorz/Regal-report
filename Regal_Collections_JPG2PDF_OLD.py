from os import sys
import os
import PIL.Image  # PIL is python 2.7 only (installed Pillow_as_PIL instead)
from pytesseract import *
from loguru import logger


@logger.catch
def reduce_size(tpl, factor):
    """ reduce the values of integers inside of the tuple by factor
    """
    out = []
    source = list(tpl)
    for x in source:
        out.append(int(x / factor))
    return tuple(out)


@logger.catch
def img2pdf(fname):
    """ This code originally lifted from:
        https://stackoverflow.com/questions/12626654/image-library-convert-from-jpeg-to
        user:3423643
        user:681277
    """
    output_reduction_factor = 2
    filename = fname
    name = filename.split(".")[0]
    # TODO trap possible file error IOError
    im = PIL.Image.open(filename)
    text = image_to_string(im)
    logger.debug(text)
    logger.debug(str(im.format) + " " + str(im.mode) + " " + str(im.size))
    bw = im.convert("L")  # strip color information from image
    output_size = reduce_size(im.size, output_reduction_factor)
    logger.debug(output_size)
    out = bw.transpose(PIL.Image.ROTATE_270)
    out = out.resize(
        tuple(reversed(output_size))
    )  # resize takes arguments in opposite order
    if not os.path.exists("im2pdf_output"):
        os.makedirs("im2pdf_output")
    newfilename = "".join(["im2pdf_output/", name, ".pdf"])
    PIL.Image.Image.save(out, newfilename, "PDF", resolution=100.0)
    logger.info("processed successfully: {}".format(newfilename))


@logger.catch
def gather_all_JPEG_filenames_and_process():
    """ This code lifted from:
        https://stackoverflow.com/questions/12626654/image-library-convert-from-jpeg-to
        user:3423643
        user:681277
    """
    files = [f for f in os.listdir("./") if f.endswith(".jpg")]
    for fname in files:
        img2pdf(fname)
    return


@logger.catch
def ask_user_for_filename():
    """ display the jpeg in a window and ask user to input the proper filename to save as.
        user will need to read the text inside the image to determine the correct filename.
        each image has a handwritten name for the particular theater this image represents.
    """
    return


@logger.catch
def Main():
    logger.add(
        sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO"
    )
    logger.add("file.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")
    logger.add("file_{time}.log")
    logger.info("Program Start.")
    gather_all_JPEG_filenames_and_process()
    return


if __name__ == "__main__":
    Main()
