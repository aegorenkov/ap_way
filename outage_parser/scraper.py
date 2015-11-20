""""
main file of scraper to retrieve outage information in the PJM area
retrieve from: https://edart.pjm.com/reports/linesout.txt

Code is windows specific and not made to port to unix systems
"""

import requests
from os import getcwd
from time import gmtime, strftime

OUTAGE_URL = 'https://edart.pjm.com/reports/linesout.txt'


class OutageFileIO(object):
    """
    Handles Input Output operations between web, disk, and python
    """

    def __init__(self, url):
        self.url = url
        self.text = ''

    def get(self):
        outage_text = requests.get(self.url)
        self.text = outage_text.text

    def save(self, directory):
        now = strftime("%Y-%m-%d_%H_%M_%S", gmtime())
        file_name = 'PJM_outages_' + now + '.txt'
        target = directory + '\\' + file_name
        with open(target, "w") as text_file:
            text_file.write(self.text)
        text_file.close()


def retrieve_PJM_outages(directory, url=OUTAGE_URL):
    """
    Retrieves PJM outage data from the internet.
    Retrieve means load, save on disk, and return from the function.

    :param directory: Directory to write PJM text file to
    :param url: The source of PJM outage data.
    Default is at https://edart.pjm.com/reports/linesout.txt
    :return: A string containing raw PJM outage data
    """
    outage_file = OutageFileIO(url)
    outage_file.get()
    outage_file.save(directory)
    return outage_file.text


if __name__ == "__main__":
    retrieve_PJM_outages(directory=getcwd())
