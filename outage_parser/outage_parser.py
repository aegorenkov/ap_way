"""
Set of classes to convert outage text file into python classes to be used
when rendering data
"""

from datetime import datetime

FIXED_FORMAT = '+---+------+--------+------------------------------------------------+-----------------+-------------' \
               '----+-+---------+-----------------+---------+---------+--------+-----------+'


class ParsingException(Exception):
    """
    Exception class to narrow the scope of errors while using EAFP idiom
    """
    pass


class FwfSlicer(object):
    """
    Fixed width format slicer to convert know fixed format into columns
    """

    def __init__(self, fixed_format):
        """
        Initialize fixed format slicer
        :param fixed_format: The fixed format schema as a series for +- with + as delimeter
        :return: Store indicies and slices internally
        """
        self.fixed_format = fixed_format
        self.indicies = [idx for idx, token in enumerate(FIXED_FORMAT) if token == '+']
        self.column_slices = [slice(start, end) for start, end in zip(self.indicies, self.indicies[1:])]


class OutageParser(object):
    """
    Main class for parsing lineoutages.txt file
    """

    def __init__(self, text):
        self.text = text.replace('\n\n', '\n')
        self._tickets = []

    @property
    def tickets(self):
        """
        Create list of tickets that corresponds to each ticket section in the textfile
        :return: List of tickets
        """
        if self._tickets:
            return self._tickets
        else:
            # Parse out tickets by splitting on the fixed format -- will break if format changes
            tickets = self.text.split(FIXED_FORMAT + '\n')
            tickets = tickets[1:-2]  # Exclude extra line that are not tickets
            tickets = [Ticket(text) for text in tickets]

            for ticket in tickets:
                for line in ticket.text.splitlines():
                    line = line.strip('\n')

                    # Use the Easier to Ask for Forgiveness idiom
                    # If we recognize an entity, we parse it, if not, we do nothing
                    try:
                        ticket.outages.append(Outage(line))
                    except ParsingException:
                        pass

                    try:
                        ticket.causes.append(Cause(line))
                    except ParsingException:
                        pass

                    try:
                        ticket.date_log.append(DateEntry(line))
                    except ParsingException:
                        pass

                    try:
                        ticket.history_log.append(HistoryEntry(line))
                    except ParsingException:
                        pass

            return tickets


class Ticket(object):
    """
    The ticket entity in the textfile
    """

    def __init__(self, text):
        """
        Parse text related to a ticket into a ticket object

        :param text: Raw text that corresponds to a single ticket
        :return: Parsed Ticked object
        """
        self._fwf = FwfSlicer(FIXED_FORMAT)
        self.text = text

        # Parsing definition
        self.number = int(self._get_col(1).strip())
        self.current_status = self._get_col(7).strip()
        self.last_revised = datetime.strptime(self._get_col(8).strip(), '%m/%d/%Y %H:%M')
        self.approval_risk = self._get_col(9).strip()
        self.rtep = self._get_col(11).strip()
        self.previous_status = self._get_col(12).strip()

        # Related entities
        self.outages = []
        self.causes = []
        self.date_log = []
        self.history_log = []

    def _get_col(self, idx):
        """
        Helper function to retrieve columns from text snippet
        :param idx:
        :return:
        """
        return self.text[self._fwf.column_slices[idx]]

    @property
    def availability(self):
        """
        Parsing definition for availability attribute
        """
        availability_value = self._get_col(10).strip()
        if availability_value == 'Duration':
            return ''
        else:
            return availability_value

    @property
    def outage_type(self):
        """
        Parsing definition for outage type attribute
        """

        second_line = self.text.splitlines()[1]
        if not second_line[108] == '(':
            raise ParsingException
        if not second_line[135:136] == ')':
            raise ParsingException
        return second_line[109:135].strip()


class Cause(object):
    """
    The Cause entity in the textfile
    """

    def __init__(self, line):
        """
        Parse text related to a cause into a cause object

        :param line: Raw text that corresponds to a single cause
        :return: Parsed Cause object
        """
        # Throw an exception if we don't see the parenthesis that mark a cause
        if not line[108] == '(':
            raise ParsingException
        if not line[159:160] == ')':
            raise ParsingException

        # Parsing definitions
        self.cause = line[109:159].strip()


class Outage(object):
    """
    The outage entity in the textfile
    """

    def __init__(self, line):
        """
        Parse text related to an outage into an outage object

        :param line: Raw text that corresponds to a single outage
        :return: Parsed Outage object
        """
        # Throw an exception if we are not in the outage section of the ticket
        if not line[:107].strip():
            raise ParsingException

        self._fwf = FwfSlicer(FIXED_FORMAT)
        self.line = line

        # Parsing definitions
        self.zone = self._get_col(2).strip()
        self.equipment_type = self._get_col(3)[1:5]
        self.station = self._get_col(3)[6:14].strip()
        self.facility_name = self._get_col(3)[21:].strip()
        self.start_time = datetime.strptime(self._get_col(4).strip(), '%d-%b-%Y %H%M')
        self.end_time = datetime.strptime(self._get_col(5).strip(), '%d-%b-%Y %H%M')
        self.open_closed = self._get_col(6).strip()

    def _get_col(self, idx):
        """
        Helper function to retrieve columns from text snippet
        :param idx:
        :return:
        """
        return self.line[self._fwf.column_slices[idx]]

    @property
    def voltage(self):
        full_facility_name = self.line[self._fwf.column_slices[3]]
        voltage_col = full_facility_name[15:21]
        return int(''.join([c for c in voltage_col if c.isdigit()]))

    @property
    def voltage_measurement_unit(self):
        full_facility_name = self.line[self._fwf.column_slices[3]]
        voltage_col = full_facility_name[15:21]
        return ''.join([c for c in voltage_col if c.isalpha()])


class DateEntry(object):
    """
    The date entry entity in the textfile located in the bottom right of a ticket
    """

    def __init__(self, line):
        """
        Parse text related to a date entry into a DateEntry object

        :param line: Raw text line that corresponds to a single date entry
        :return: Parsed DateEntry object
        """
        # Throw an exception if we don't see the parenthesis that mark a date entry
        if not line[108] == '(':
            raise ParsingException
        if not line[164:165] == ')':
            raise ParsingException

        # Parsing definitions
        self.start_time = datetime.strptime(line[109:125], '%d-%b-%Y %H%M')
        self.end_time = datetime.strptime(line[128:144], '%d-%b-%Y %H%M')
        self.time_stamp = datetime.strptime(line[148:164], '%m/%d/%Y %H:%M')


class HistoryEntry(object):
    """
    The date entry entity in the textfile located in the bottom right of a ticket
    """

    def __init__(self, line):
        """
        Parse text related to a history entry in the history log into a HistoryEntry

        :param line: Raw text line that corresponds to a single history entry
        :return: Parsed HistoryEntry object
        """
        # Throw an exception if we don't see the parenthesis that mark a history entry
        if not line[108] == '(':
            raise ParsingException
        if not line[138:139] == ')':
            raise ParsingException

        self.status = line[109:122].strip()
        self.time_stamp = datetime.strptime(line[122:138], '%m/%d/%Y %H:%M')


def scrape_PJM_outage_file(source):
    """
    Scrapes outage file into an organized hierarchy of objects
    :param source: Filepath of file to parse
    :return: OutageParser object that contains all related entities
    """
    with open(source, 'rU') as pjm_outage_file:
        pjm_data = pjm_outage_file.read()

    return OutageParser(pjm_data)
