from unittest import TestCase
from datetime import datetime
from outages.outage_parser.outage_parser import HistoryEntry, DateEntry, Outage, Cause, Ticket, OutageParser, \
    scrape_PJM_outage_file



class TestOutageParser(TestCase):
    def setUp(self):
        unparsed = \
"""+---+------+--------+------------------------------------------------+-----------------+-----------------+-+---------+-----------------+---------+---------+--------+-----------+
 332 594137 AEP-IM   BRKR SORENSON 345 KV  SORENSON B            CB   01-NOV-2015 0800  24-NOV-2015 1600  O  Active   11/01/2015 07:40            Duration           Approved   |
            AEP-IM   BRKR SORENSON 345 KV  SORENSON B2           CB   01-NOV-2015 0800  24-NOV-2015 1600  O (Continuous                )
            AEP-IM   BRKR KEYSTNE  345 KV  KEYSTNE  A            CB   01-NOV-2015 0800  24-NOV-2015 1600  O (New Construction                                  )
            AEP-IM   BRKR KEYSTNE  345 KV  KEYSTNE  C            CB   01-NOV-2015 0800  24-NOV-2015 1600  O                            |
            AEP      LINE SORENSON 345 KV  SORENSON-KEYSTNE           01-NOV-2015 0800  24-NOV-2015 1600  O                            |
                                                                                                            (01-NOV-2015 0800   24-NOV-2015 1600    03/24/2015 17:12)
                                                                                                            (Active       11/01/2015 07:40)
                                                                                                            (Approved     10/29/2015 14:16)
                                                                                                            (Received     03/25/2015 15:55)
+---+------+--------+------------------------------------------------+-----------------+-----------------+-+---------+-----------------+---------+---------+--------+-----------+
 333 616724 AEP      LINE DELAWARE 138 KV  DELAWARE-TANGY TIE         01-NOV-2015 0912  13-NOV-2015 1600  O  Active   11/06/2015 18:50            Duration           Submitted  |
            AEP-OH   BRKR DELAWARE 138 KV  DELAWARE 106          CB   01-NOV-2015 0912  13-NOV-2015 1600  O (Continuous                )
                                                                                                            (CB Maintenance                                    )
                                                                                                            (01-NOV-2015 0912   13-NOV-2015 1600    11/06/2015 18:50)
                                                                                                            (01-NOV-2015 0912   06-NOV-2015 1600    11/04/2015 20:41)
                                                                                                            (01-NOV-2015 0912   04-NOV-2015 1600    11/03/2015 17:20)
                                                                                                            (01-NOV-2015 0912   03-NOV-2015 1600    11/01/2015 09:05)
                                                                                                            (Active       11/01/2015 09:12)
                                                                                                            (Approved     11/01/2015 09:12)
+---+------+--------+------------------------------------------------+-----------------+-----------------+-+---------+-----------------+---------+---------+--------+-----------+

                                                                                                                    LAST_REVISED
PLANNED OUTAGES (OUTAGE REQUEST RECEIVED BY PJM PLANNING PERSONNEL)                         OPEN/CLOSED---+ (. . . . outage type . . . )
ITEM TICKET ZONE/CO  FACILITY_NAME                                     START_DATE TIME   END_DATE  TIME   | (. . . . c a u s e s . . . )
+---+------+--------+------------------------------------------------+-----------------+-----------------+-+---------+-----------------+---------+---------+--------+-----------+
"""
        self.outage_parser = OutageParser(unparsed)

    def test_outage_parser_should_return2_tickets(self):
        self.assertEqual(len(self.outage_parser.tickets), 2)

    def test_first_ticket_should_have_5_outages(self):
        self.assertEqual(len(self.outage_parser.tickets[0].outages), 5)

    def test_second_ticket_should_have_2_outages(self):
        self.assertEqual(len(self.outage_parser.tickets[1].outages), 2)

    def test_second_ticket_should_have_4_date_entries(self):
        self.assertEqual(len(self.outage_parser.tickets[1].date_log), 4)

    def test_second_ticket_should_have_2_history_entries(self):
        self.assertEqual(len(self.outage_parser.tickets[1].history_log), 2)

class TestTicket(TestCase):
    def setUp(self):
        unparsed = \
"""2294 616617 AEP-IM   BRKR HUNTINGT 138 KV  HUNTINGT A            DIS  27-DEC-2015 0800  31-DEC-2015 1600  O  Received 11/02/2015 08:17            Duration           Submitted  |
            AEP-IM   BRKR SORENSON 138 KV  SORENSON L2           CB   27-DEC-2015 0800  31-DEC-2015 1600  O (Continuous                )
            AEP      LINE HUNTINGT 138 KV  HUNTINGT-SORENSON          27-DEC-2015 0800  31-DEC-2015 1600  O (New Construction                                  )
                                                                                                                (27-DEC-2015 0800   31-DEC-2015 1600    10/30/2015 13:40)
                                                                                                                (Received     11/02/2015 08:17)"""
        self.ticket = Ticket(unparsed)

    def test_ticket_number_should_be_616617(self):
        self.assertEqual(self.ticket.number, 616617)

    def test_ticket_current_status_should_be_received(self):
        self.assertEqual(self.ticket.current_status, 'Received')

    def test_ticket_last_revised_should_be_correct_datetime(self):
        self.assertEqual(self.ticket.last_revised, datetime(2015, 11, 2, 8, 17))

    def test_ticket_approval_risk_should_be_blank(self):
        self.assertEqual(self.ticket.approval_risk, '')

    def test_ticket_availability_should_be_blank(self):
        self.assertEqual(self.ticket.availability, '')

    def test_ticket_rtep_should_be_blank(self):
        self.assertEqual(self.ticket.rtep, '')

    def test_ticket_previous_status_should_be_submitted(self):
        self.assertEqual(self.ticket.previous_status, 'Submitted')

    def test_ticket_outage_type_should_be_continuous(self):
        self.assertEqual(self.ticket.outage_type, 'Continuous')


class TestOutageFirstLine(TestCase):
    def setUp(self):
        unparsed = "3158 612855 COMED    BRKR 443 HARV 138 KV  443 HARVE 38L7615 CS       25-APR-2016 0600  27-APR-2016 1900  O  Received 09/29/2015 11:01            Duration           Submitted  |"
        self.outage = Outage(unparsed)

    def test_outage_zone_should_be(self):
        self.assertEqual(self.outage.zone, 'COMED')

    def test_outage_equipment_type_should_be(self):
        self.assertEqual(self.outage.equipment_type, 'BRKR')

    def test_outage_station_should_be(self):
        self.assertEqual(self.outage.station, '443 HARV')

    def test_outage_voltage_should_be(self):
        self.assertEqual(self.outage.voltage, 138)

    def test_outage_voltage_unit_should_be(self):
        self.assertEqual(self.outage.voltage_measurement_unit, 'KV')

    def test_outage_facility_name_should_be(self):
        self.assertEqual(self.outage.facility_name, '443 HARVE 38L7615 CS')

    def test_outage_start_time_should_be(self):
        self.assertEqual(self.outage.start_time, datetime(2016, 4, 25, 6, 0))

    def test_outage_end_time_should_be(self):
        self.assertEqual(self.outage.end_time, datetime(2016, 4, 27, 19, 0))

    def test_outage_open_closed_should_be(self):
        self.assertEqual(self.outage.open_closed, 'O')


class TestOutageWithoutCauseOrLog(TestCase):
    def setUp(self):
        unparsed = "            COMED    BRKR 12 DRESD 138 KV  12 DRESDE 38BT1-2 CB       11-APR-2016 0600  05-MAY-2016 1900  O                            |"
        self.outage = Outage(unparsed)

    def test_outage_zone_should_be(self):
        self.assertEqual(self.outage.zone, 'COMED')

    def test_outage_equipment_type_should_be(self):
        self.assertEqual(self.outage.equipment_type, 'BRKR')

    def test_outage_station_should_be(self):
        self.assertEqual(self.outage.station, '12 DRESD')

    def test_outage_voltage_should_be(self):
        self.assertEqual(self.outage.voltage, 138)

    def test_outage_voltage_unit_should_be(self):
        self.assertEqual(self.outage.voltage_measurement_unit, 'KV')

    def test_outage_facility_name_should_be(self):
        self.assertEqual(self.outage.facility_name, '12 DRESDE 38BT1-2 CB')

    def test_outage_start_time_should_be(self):
        self.assertEqual(self.outage.start_time, datetime(2016, 4, 11, 6, 0))

    def test_outage_end_time_should_be(self):
        self.assertEqual(self.outage.end_time, datetime(2016, 5, 5, 19, 0))

    def test_outage_open_closed_should_be(self):
        self.assertEqual(self.outage.open_closed, 'O')


class TestOutageWithOutageType(TestCase):
    def setUp(self):
        unparsed = "            ME       BRKR TMI      500 KV  TMI      502602        CB  03-OCT-2016 0800  11-NOV-2016 1600  O (Continuous                )"
        self.outage = Outage(unparsed)

    def test_outage_zone_should_be(self):
        self.assertEqual(self.outage.zone, 'ME')

    def test_outage_equipment_type_should_be(self):
        self.assertEqual(self.outage.equipment_type, 'BRKR')

    def test_outage_station_should_be(self):
        self.assertEqual(self.outage.station, 'TMI')

    def test_outage_voltage_should_be(self):
        self.assertEqual(self.outage.voltage, 500)

    def test_outage_voltage_unit_should_be(self):
        self.assertEqual(self.outage.voltage_measurement_unit, 'KV')

    def test_outage_facility_name_should_be(self):
        self.assertEqual(self.outage.facility_name, 'TMI      502602        CB')

    def test_outage_start_time_should_be(self):
        self.assertEqual(self.outage.start_time, datetime(2016, 10, 3, 8, 0))

    def test_outage_end_time_should_be(self):
        self.assertEqual(self.outage.end_time, datetime(2016, 11, 11, 16, 0))

    def test_outage_open_closed_should_be(self):
        self.assertEqual(self.outage.open_closed, 'O')


class TestCauseWithOutage(TestCase):
    def setUp(self):
        unparsed = "            FE       BRKR EVERGFE  138 KV  EVERGFE  WCI_B21      CB   24-OCT-2012 0800  20-DEC-2015 1600  O (Other                                             )"
        self.cause = Cause(unparsed)

    def test_cause_should_be_other(self):
        self.assertEqual(self.cause.cause, 'Other')


class TestCauseWithoutOutage(TestCase):
    def setUp(self):
        unparsed = "                                                                                                            (Emergency                                         )"
        self.cause = Cause(unparsed)

    def test_cause_should_be_emergency(self):
        self.assertEqual(self.cause.cause, 'Emergency')


class TestCauseWithParens(TestCase):
    def setUp(self):
        unparsed = "            AE       BRKR CARDIFF  230 KV  CARDIFF  AW CB        CB   09-DEC-2015 0600  09-DEC-2015 1800  O (Relay Maintenance (Impact to primary clearing)    )"
        self.cause = Cause(unparsed)

    def test_cause_should_be_relay_maintenance(self):
        self.assertEqual(self.cause.cause, 'Relay Maintenance (Impact to primary clearing)')


class TestCause(TestCase):
    def setUp(self):
        unparsed = "                                                                                                            (Inspection/Maintenance                            )"
        self.cause = Cause(unparsed)

    def test_cause_should_be_instpection_maintenance(self):
        self.assertEqual(self.cause.cause, 'Inspection/Maintenance')


class TestDateEntry(TestCase):
    def setUp(self):
        unparsed = "                                                                                                            (22-DEC-2015 0200   22-DEC-2015 1600    10/29/2015 07:50)"
        self.date_entry = DateEntry(unparsed)

    def test_date_entry_start_time_should_be_correct_datetime(self):
        self.assertEqual(self.date_entry.start_time, datetime(2015, 12, 22, 2, 0))

    def test_date_entry_end_time_should_be_correct_datetime(self):
        self.assertEqual(self.date_entry.end_time, datetime(2015, 12, 22, 16, 0))

    def test_date_entry_time_stamp_should_be_correct_datetime(self):
        self.assertEqual(self.date_entry.time_stamp, datetime(2015, 10, 29, 7, 50))


class TestHistoryEntry(TestCase):
    def setUp(self):
        unparsed = "                                                                                                            (Received     05/11/2015 13:57)"
        self.history_entry = HistoryEntry(unparsed)

    def test_history_log_status_should_be_recieved(self):
        self.assertEqual(self.history_entry.status, 'Received')

    def test_history_log_timestamp_should_be_correct_datetime(self):
        self.assertEqual(self.history_entry.time_stamp, datetime(2015, 5, 11, 13, 57))

class TestScrapePJMOutageFile(TestCase):
    def setUp(self):
        self.pjm = scrape_PJM_outage_file('C:\Users\Alexander\PycharmProjects\outage\outages\outage_parser\PJM_outages_2015-11-07_15_42_15.txt')

    def test_runs(self):
        tickets = self.pjm.tickets
        ticket50 = tickets[50]
        causes = ticket50.causes
        outages = ticket50.outages
        date_log = ticket50.date_log
        history_log = ticket50.history_log

    def test_ticket_50_should_have_contuous_outage(self):
        self.assertEqual(self.pjm.tickets[50].outage_type,'Continuous')

    def test_ticket_50_should_have_emergency_cause(self):
        self.assertEqual(self.pjm.tickets[50].causes[0].cause, 'Emergency')
