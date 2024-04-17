from PIL import ImageFile, Image, ImageDraw, ImageFont, ImageStat
from PyPDF2 import PdfMerger
from natsort import natsorted, ns
from tqdm import tqdm
import argparse
import os
import re
import logging

import config

class Manga:
    """
    __manga_path = None  # String, Private
    __out_path = None  # String, Private
    __chapters = []  # List of Chapters, Private
    __chapter_pdfs = []  # List of Strings pointing to the chapter pdfs, Private
    __chapter_numbers = []  # List of Ints, Private
    __chapter_invalids = []  # List of Ints, Private
    __args = None  # args from argparse, Private
    """

    def __init__(self, manga_path, out_path):
        """Constructor sets up the Object and output directory"""
        self.__manga_path = os.path.abspath(manga_path)
        self.__out_path = os.path.abspath(out_path)
        self.__chapters = []
        self.__chapter_pdfs = []
        self.__chapter_numbers = []
        self.__chapter_invalids = []
        self.__args = None
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

    def addArgs(self, args):
        self.__args = args

    def convert(self):  # String
        """Create the final output pdf"""
        logging.info("Starting conversion")
        out_name = os.path.basename(self.getOut()) + ".pdf"
        # Create a pdf for all the chapters
        for chapter in tqdm(self.__chapters):
            self.__chapter_pdfs.append(chapter.toPDF())
        logging.info("All chapters have been converted.  Combining to one pdf")
        # Sort the pdf list
        self.__chapter_pdfs = natsorted(self.__chapter_pdfs, alg=ns.F)
        # Combine all pdfs to a single pdf
        merger = PdfMerger(strict=False)
        for pdf in self.__chapter_pdfs:
            merger.append(pdf)
        with open(os.path.join(self.getOut(), out_name), "wb") as f:
            merger.write(f)
        logging.info("Combined pdf created")
        # Remove temporary PDF files
        if self.__args.delete:
            logging.info("Removing temporary pdfs")
            [os.remove(os.path.join(self.getOut(), x)) for x in os.listdir(self.getOut()) if x != out_name]
        return os.path.join(self.getOut(), out_name)

    def getOut(self):  # String
        return self.__out_path

    def getMangaPath(self):  # String
        return self.__manga_path


class Chapter:
    """
    __manga = None  # Manga, Private
    __chapter_path = None  # String, Private
    __chapter_name = None  # String, Private
    __chapter_number = None  # int, Private
    __pages = []  # PIL Image, Private
    """

    def __init__(self, manga, path, name):  # void
        self.__manga = manga
        self.__chapter_path = os.path.abspath(path)
        self.__chapter_name = name
        self.__chapter_number = None
        self.__pages = []

    def __drawTitle(self):  # PIL Image
        """Draw a cover title for the Chapter"""
        fnt = ImageFont.truetype(config.FONT, 60)
        # Fix magic number
        image = Image.new(mode="RGB", size=(739, 1080), color="white")
        draw = ImageDraw.Draw(image)
        draw.text((226, 445), "chapter " + str(self.getChapterNumber()), font=fnt, fill=(0, 0, 0))
        return image

    def __drawPageNumber(self, page_num, total_pages):  # PIL Image
        text = str(self.getChapterNumber()) + "  " + str(page_num) + "/" + str(int(total_pages))
        fnt = ImageFont.truetype(config.FONT, 30)
        image = Image.new(mode="RGB", size=(160, 22), color="white")
        draw = ImageDraw.Draw(image)
        draw.text((160, 0), text, font=fnt, fill=(0, 0, 0), anchor="rt")
        return image

    def toPDF(self):  # String
        """Creates a single pdf from all the pages
        Returns a string pointing to where the pdf was saved"""

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
                page_number = self.__drawPageNumber(index, len(chapter_dir))
                Image.Image.paste(current, page_number, (current.size[0] - page_number.size[0], 0))
                page_number.close()
                # current.save(os.path.join(self.getOut(),image))
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
        """Setter method for number with checking.
        Returns true for successful set and false for not"""
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


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="Path to input manga")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    # Optional flags
    parser.add_argument("--delete", action=argparse.BooleanOptionalAction, help="Delete temporary pdf files after "
                                                                                "compilation")
    parser.set_defaults(delete=True)
    args = parser.parse_args()

    # Create Manga object
    manga = Manga(args.input, args.output)
    manga.addArgs(args)
    # Convert to PDF
    print("Starting conversion: " + str(args.input) + " -> " + str(os.path.join(args.output, os.path.basename(args.output))) + ".pdf")
    out = manga.convert()
    print("Your manga is done!  The path is " + str(out))


if __name__ == "__main__":
    main()
