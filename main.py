from PIL import Image, ImageDraw, ImageFont, ImageChops
from PyPDF2 import PdfMerger
from natsort import natsorted, ns
from tqdm import tqdm
import ocrmypdf
import argparse
import os
import re
import logging

import config


class Manga:
    def __init__(self, manga_path, out_path):
        """Constructor sets up the Object and output directory"""
        self.__manga_path = os.path.abspath(manga_path)  # String, Private
        self.__out_path = os.path.abspath(out_path)  # String, Private
        self.__chapters = []  # List of Chapters, Private
        self.__chapter_pdfs = []  # List of Strings pointing to the chapter pdfs, Private
        self.__chapter_numbers = []  # List of Ints, Private
        self.__chapter_invalids = []  # List of Ints, Private
        if config.TITLE:
            self.__title = config.TITLE + ".pdf"  # String, Private
        else:
            self.__title = os.path.basename(self.getOut()) + ".pdf"
        self.__initChapters()

    def __initChapters(self):
        # Create a Chapter object for all folders in manga_path
        paths = [f.path for f in os.scandir(self.__manga_path) if f.is_dir()]
        self.__chapters = [Chapter(self, path, os.path.basename(path)) for path in paths]
        # Make the out directory if it does not exist already
        if not (os.path.exists(self.__out_path)):
            logging.info("Output path does not exist, making directory")
            os.mkdir(self.__out_path)

        # Set chapter numbers and set up output directory
        index = 0
        for chapter in self.__chapters:
            success = chapter.setChapterNumber(re.sub(config.REGEX_PATTERN, r"\1", chapter.getChapterName()))
            if not success:
                logging.warning("Attempt to add invalid chapter: " + str(chapter.getChapterName()))
                self.__chapter_invalids.append(index)
            elif chapter.getChapterNumber() in self.__chapter_numbers:
                for existing in self.__chapters:
                    if chapter.getChapterNumber() == existing.getChapterNumber():
                        logging.warning("Attempt to add duplicate chapter: " + str(chapter.getChapterName())
                                        + "  Existing chapter: " + str(existing.getChapterName()))
                        break
                else:
                    logging.warning("You should not see this message sent by Manga's constructor")
                self.__chapter_invalids.append(index)
            else:
                self.__chapter_numbers.append(chapter.getChapterNumber())
            index += 1
        # Remove the chapters of all bad indices
        while self.__chapter_invalids:
            self.__chapters.pop(self.__chapter_invalids[0])
            self.__chapter_invalids = [x - 1 for x in self.__chapter_invalids[1:]]

    def __ocr(self, f_name, languages):
        # Apply OCR
        ocrmypdf.ocr(f_name, f_name, language=languages, title=self.__title, output_type="pdf")

    def convert(self):  # String
        """Create the final output pdf"""
        logging.info("Starting conversion")
        # Create a pdf for all the chapters
        for chapter in tqdm(self.__chapters):
            self.__chapter_pdfs.append(chapter.toPDF())
        logging.info("All chapters have been converted.  Combining to one pdf")
        # Sort the pdf list
        self.__chapter_pdfs = natsorted(self.__chapter_pdfs, alg=ns.F)
        # Combine all pdfs to a single pdf
        merger = PdfMerger(strict=False)
        for pdf in self.__chapter_pdfs:
            merger.append(pdf, "Chapter " + os.path.basename(pdf))

        # Add metadata
        if config.AUTHOR:
            merger.add_metadata({u"/Title": self.__title, u"Author": config.AUTHOR})
        else:
            merger.add_metadata({u"/Title": self.__title})

        # Write output
        with open(os.path.join(self.getOut(), self.__title), "wb") as f:
            merger.write(f)
        logging.info("Combined pdf created")
        # Remove temporary PDF files
        if config.DELETE:
            logging.info("Removing temporary pdfs")
            [os.remove(os.path.join(self.getOut(), x)) for x in os.listdir(self.getOut()) if x != self.__title]
        # Add OCR
        if config.OCR:
            logging.info("Applying OCR")
            print("Applying OCR")
            self.__ocr(os.path.join(self.getOut(), self.__title), config.OCR_LANGUAGES)

        return os.path.join(self.getOut(), self.__title)

    def getOut(self):  # String
        return self.__out_path

    def getMangaPath(self):  # String
        return self.__manga_path

    def getMangaTitle(self):
        return self.__title


class Chapter:
    def __init__(self, manga, path, name):  # void
        self.__manga = manga  # Manga, Private
        self.__chapter_path = os.path.abspath(path)  # String, Private
        self.__chapter_name = name  # String, Private
        self.__chapter_number = None  # int, Private
        self.__pages = []  # PIL Image, Private

    def __drawTitle(self):  # PIL Image
        """
        Draw a cover title for the Chapter
        :return: PIL image of the constructed title page
        """
        fnt = ImageFont.truetype(config.TITLE_FONT, config.TITLE_SIZE)
        # Fix magic number
        image = Image.new(mode="RGB", size=(config.TITLE_WIDTH, config.TITLE_HEIGHT), color=config.TITLE_BG_COLOR)
        draw = ImageDraw.Draw(image)
        text = "Next:\nChapter " + str(self.getChapterNumber() + "\n" + str(self.getChapterName()))
        draw.text((image.size[0] / 2, image.size[1] / 2), text,
                  font=fnt, fill=config.TITLE_TEXT_COLOR, anchor="mm")
        return image

    def __drawPageNumber(self, dest, curr_page, total_pages):  # void
        """
        Draws page numbers on the input image.
        :param dest: Destination image to paste the page numbers on
        :param curr_page: Current page number of chapter
        :param total_pages: Total pages in chapter
        :return: void
        """
        text = str(self.getChapterNumber()) + "  " + str(curr_page) + "/" + str(int(total_pages))
        fnt = ImageFont.truetype(config.PAGE_FONT, config.PAGE_SIZE)
        _, _, fnt_width, fnt_height = fnt.getbbox(text)
        overlay = Image.new(mode="RGBA", size=(fnt_width + (2 * config.PAGE_PADDING),
                                               fnt_height + (2 * config.PAGE_PADDING)), color=config.PAGE_NUM_FILL)
        draw = ImageDraw.Draw(overlay)
        draw.text((config.PAGE_PADDING, overlay.size[1] / 2),
                  text, font=fnt, fill=config.PAGE_NUM_COLOR, anchor="lm")

        # Paste the page number on top
        match config.PAGE_LOCATION:
            case 0:
                dest.paste(overlay, (0, 0), overlay)
                # ^ (img to paste, coordinates, mask)
            case 1:
                dest.paste(overlay, (dest.size[0] - overlay.size[0], 0), overlay)
            case 2:
                dest.paste(overlay, (0, dest.size[1] - overlay.size[1]), overlay)
            case 3:
                dest.paste(overlay, (dest.size[0] - overlay.size[0], dest.size[1] - overlay.size[1]), overlay)
            case _:
                logging.error("Invalid page location")
                raise ValueError("Chapter.__drawPageNumber throws invalid page location")
        overlay.close()

    @staticmethod
    def __removeMargins(image):
        # https://stackoverflow.com/questions/10615901/trim-whitespace-using-pil
        # Create a new image the same size as the input.  Fill color is the top left pixel of the input
        bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
        # Create a new Image diff containing the absolute value difference of each pixel between the two images
        # The reason we need to do this is because the getbbox() method only looks at pure black pixels on the edges
        diff = ImageChops.difference(image, bg)
        # Get bounding box of the diff Image and crop according to the bounds of this box
        bbox = diff.getbbox()
        if bbox:
            return image.crop(bbox)
        else:
            return image

    def toPDF(self):  # String
        """
        Creates a single pdf from all the pages.
        Returns a string pointing to where the pdf was saved.
        :return: String that is the path to the output pdf
        """

        # Draw title
        self.__pages.append(self.__drawTitle())
        chapter_dir = [x for x in os.listdir(self.getChapterPath()) if x != ".nomedia"]
        os.chdir(self.getChapterPath())
        index = 1
        for image in natsorted(chapter_dir):  # image has type String
            try:
                current = Image.open(image)
            except:
                logging.warning("Unable to open image: " + str(os.path.join(self.getChapterPath(), image)))
            else:
                current = current.convert("RGB")
                if config.TRIM:
                    current = self.__removeMargins(current)
                self.__drawPageNumber(current, index, len(chapter_dir))
                self.__pages.append(current)
            index += 1

        # Save the combined images to a single PDF
        # https://stackoverflow.com/questions/27327513/create-pdf-from-a-list-of-images
        self.__pages[0].save(os.path.join(self.getOut(), str(self.getChapterNumber())),
                             "PDF",
                             resolution=100,
                             save_all=True,
                             append_images=self.__pages[1:])
        return os.path.join(self.getOut(), str(self.getChapterNumber()))

    # Getter and setter methods
    def setChapterNumber(self, number):  # bool
        """
        Setter method for chapter number with checking.
        :param number: Number to set the chapter number to
        :return: True for successful set and false for unsuccessful set
        """
        try:
            int(number)
        except ValueError:
            return False
        else:
            self.__chapter_number = number
            return True

    def getChapterName(self):  # String
        return self.__chapter_name

    def getChapterNumber(self):  # int
        return self.__chapter_number

    def getChapterPath(self):  # String
        return self.__chapter_path

    def getOut(self):  # String
        return self.__manga.getOut()


def checkFonts():
    """Throws a ValueError if the font given is invalid.
    It is common for invalid fonts to be given in the config.py file, so make sure they are valid before continuing."""
    try:
        fnt = ImageFont.truetype(config.TITLE_FONT, config.TITLE_SIZE)
        fnt = ImageFont.truetype(config.PAGE_FONT, config.PAGE_SIZE)
    except OSError:
        raise ValueError("Invalid font given in config.py.  Try changing TITLE_FONT and PAGE_FONT in config.py.")


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="Path to input manga")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    # Optional flags
    parser.add_argument("--title", required=False,
                        help="Title metadata for output pdf.  If not specified then the basename of the output path "
                             "will be used.")
    parser.add_argument("--author", required=False,
                        help="Author metadata for output pdf.  Default is none")
    parser.add_argument("--delete", required=False, action=argparse.BooleanOptionalAction,
                        help="Delete temporary pdf files after compilation.  Default is delete")
    parser.add_argument("--ocr", required=False, action=argparse.BooleanOptionalAction,
                        help="Add OCR on the output pdf.  Default is no ocr")
    parser.add_argument("--trim", required=False, action=argparse.BooleanOptionalAction,
                        help="Remove margins or whitespace.  Useful for 4-Koma.  Default is trim")

    args = parser.parse_args()
    if args.title is not None:
        config.TITLE = args.title
    if args.author is not None:
        config.AUTHOR = args.author
    if args.delete is not None:
        config.DELETE = args.delete
    if args.ocr is not None:
        config.OCR = args.ocr
    if args.trim is not None:
        config.TRIM = args.trim

    checkFonts()
    # Create Manga object
    manga = Manga(args.input, args.output)
    # Convert to PDF
    print("Starting conversion: " + str(args.input) + " -> " + str(
        os.path.join(args.output, manga.getMangaTitle())))
    out = manga.convert()
    print("Your manga is done!  The path is " + str(out))


if __name__ == "__main__":
    main()
