from django.db import models
from django.db import connection


class CurrentPlannedOutageManager(models.Manager):
    """
    Helper class that defines logic for dealing out outages
    """

    def insert_outages(self, planned_outages, mod_date):
        """
        Insert outages into database and updates the history table to reflect
        changes.
        :param planned_outages: List of outage objects from Django
        :param mod_date: Date used for validFrom column--modification date
        :return: Returns nothing, does SQL I/O
        """
        CurrentPlannedOutage.objects.bulk_create(planned_outages)
        HistoricPlannedOutage.objects.update_removed(mod_date)
        HistoricPlannedOutage.objects.update_changed(mod_date)
        HistoricPlannedOutage.objects.insert_changed()
        HistoricPlannedOutage.objects.insert_new()

    def delete_current_outages(self):
        """
        Removes all instances of Outages in CurrentOutages table
        :return: Returns nothing, does SQL I/O
        """
        CurrentPlannedOutage.objects.all().delete()


class HistoricPlannedOutageManager(models.Manager):
    """
    Helper class that contains logic fof dealing with the PlannedOutages
    history table
    """

    def update_removed(self, mod_date):
        """
        Invalidates outages that have been removed from the most recent outage file

        :param mod_date: Date used for validFrom column--modification date
        :return: Returns nothing, does SQL I/O
        """
        c = connection.cursor()
        mod_date = mod_date.strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        UPDATE outages_historicplannedoutage
        SET validTo = '{}', currentStatus = 'N'
        WHERE NOT EXISTS(SELECT * FROM outages_currentplannedoutage
                          WHERE outages_historicplannedoutage.currentStatus LIKE 'Y'
                          AND outages_historicplannedoutage.ticket_number = outages_currentplannedoutage.ticket_id
                          AND outages_historicplannedoutage.facility_id = outages_currentplannedoutage.facility_id
                          AND outages_currentplannedoutage.lineNumber = outages_historicplannedoutage.lineNumber);""".format(
            mod_date)
        c.execute(sql)

    def update_changed(self, mod_date):
        """
        Invalidates outages that have been changed in the most recent outage file

        :param mod_date: Date used for validFrom column--modification date
        :return: Returns nothing, does SQL I/O
        """
        c = connection.cursor()
        mod_date = mod_date.strftime("%Y-%m-%d %H:%M:%S")
        sql = """UPDATE outages_historicplannedoutage
        SET validTo = '{}', currentStatus = 'N'
        WHERE EXISTS(SELECT * FROM outages_currentplannedoutage
              WHERE outages_historicplannedoutage.currentStatus LIKE 'Y'
                AND outages_historicplannedoutage.ticket_number = outages_currentplannedoutage.ticket_id
                AND outages_historicplannedoutage.facility_id = outages_currentplannedoutage.facility_id
                AND outages_currentplannedoutage.lineNumber = outages_historicplannedoutage.lineNumber
                AND (outages_currentplannedoutage.startTime != outages_historicplannedoutage.startTime
                  OR outages_currentplannedoutage.endTime != outages_historicplannedoutage.endTime
                  OR outages_currentplannedoutage.openClosed != outages_historicplannedoutage.openClosed));""".format(
            mod_date)
        c.execute(sql)

    def insert_changed(self):
        """
        Inserts new outage entry to replace previously invalidated ticket entry

        :return: Returns nothing, does SQL I/O
        """
        c = connection.cursor()
        sql = """
        INSERT INTO outages_historicplannedoutage
        (ticket_id, ticket_number, lineNumber, zone_id, station_id, facility_id, startTime, endTime, openClosed,
        validFrom, validTo, currentStatus)
        SELECT
        outages_historicticket.id AS ticket_id, outages_historicticket.ticket_number AS ticket_number, lineNumber,
        zone_id, station_id, facility_id, startTime, endTime, openClosed, outages_currentplannedoutage.validFrom,
        outages_currentplannedoutage.validTo, 'Y'
        FROM outages_currentplannedoutage
          LEFT JOIN outages_historicticket
            ON outages_historicticket.ticket_number = outages_currentplannedoutage.ticket_id
        WHERE EXISTS(SELECT * FROM outages_historicplannedoutage
              WHERE outages_historicplannedoutage.currentStatus LIKE 'Y'
              AND outages_historicplannedoutage.ticket_number = outages_currentplannedoutage.ticket_id
              AND outages_historicplannedoutage.facility_id = outages_currentplannedoutage.facility_id
              AND outages_currentplannedoutage.lineNumber = outages_historicplannedoutage.lineNumber
              AND (outages_currentplannedoutage.startTime != outages_historicplannedoutage.startTime
                OR outages_currentplannedoutage.endTime != outages_historicplannedoutage.endTime
                OR outages_currentplannedoutage.openClosed != outages_historicplannedoutage.openClosed));"""
        c.execute(sql)

    def insert_new(self):
        """
        Inserts any newly added entries from the current planned outages file

        :return: Returns nothing, does SQL I/O
        """
        c = connection.cursor()
        sql = """
        INSERT INTO outages_historicplannedoutage
        (ticket_id, ticket_number, lineNumber, zone_id, station_id, facility_id, startTime, endTime, openClosed, validFrom, validTo, currentStatus)
        SELECT
        outages_historicticket.id AS ticket_id, outages_historicticket.ticket_number AS ticket_number, lineNumber,
        zone_id, station_id, facility_id, startTime, endTime, openClosed, outages_currentplannedoutage.validFrom,
        outages_currentplannedoutage.validTo, 'Y'
        FROM outages_currentplannedoutage
          LEFT JOIN outages_historicticket
            ON outages_historicticket.ticket_number = outages_currentplannedoutage.ticket_id
            WHERE NOT EXISTS(SELECT *
                   FROM outages_historicplannedoutage
                   WHERE outages_historicplannedoutage.currentStatus LIKE 'Y'
                         AND outages_currentplannedoutage.ticket_id = outages_historicplannedoutage.ticket_number
                         AND outages_currentplannedoutage.facility_id = outages_historicplannedoutage.facility_id
                         AND outages_currentplannedoutage.lineNumber = outages_historicplannedoutage.lineNumber);"""
        c.execute(sql)


class CurrentTicketManager(models.Manager):
    """
    Helper class to store logic dealing with Ticket instances
    """

    def insert_tickets(self, tickets, mod_date):
        """
        Insert tickets into database.

        :param tickets: List of django ticket instances
        :param mod_date: Modification date. Sets the validFrom column.
        :return: Does database I/O
        """
        CurrentTicket.objects.bulk_create(tickets)

        HistoricTicket.objects.update_removed(mod_date)
        HistoricTicket.objects.update_changed(mod_date)
        HistoricTicket.objects.insert_changed()
        HistoricTicket.objects.insert_new()


class HistoricTicketManager(models.Manager):
    """
    Helper class to maintain history table of tickets
    """

    def update_removed(self, mod_date):
        """
        Invalidated tickets that have been removed from the msot recent outage file

        :param mod_date: Modification date. Sets the validFrom column.
        :return: Returns nothing, does database I/O
        """
        c = connection.cursor()
        mod_date = mod_date.strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        UPDATE outages_historicticket
        SET validTo = '{}', currentStatus = 'N'
        WHERE NOT EXISTS(SELECT * FROM outages_currentticket
                          WHERE outages_historicticket.currentStatus LIKE 'Y'
                          AND outages_historicticket.ticket_number = outages_currentticket.ticket_number);""".format(
            mod_date)
        c.execute(sql)

    def update_changed(self, mod_date):
        """
        Invalidates tickets that have been changed in the most recent outages file

        :param mod_date:
        :return:
        """
        c = connection.cursor()
        mod_date = mod_date.strftime("%Y-%m-%d %H:%M:%S")
        sql = """UPDATE outages_historicticket
          SET validTo = '{}', currentStatus = 'N'
          WHERE EXISTS(SELECT * FROM outages_currentticket
                WHERE outages_historicticket.currentStatus LIKE 'Y'
                  AND outages_historicticket.ticket_number = outages_currentticket.ticket_number
                  AND (outages_historicticket.status != outages_currentticket.status
                    OR outages_historicticket.lastRevised != outages_currentticket.lastRevised
                    OR outages_historicticket.outageType != outages_currentticket.outageType
                    OR outages_historicticket.approvalRisk != outages_currentticket.approvalRisk
                    OR outages_historicticket.availability != outages_currentticket.availability
                    OR outages_historicticket.rtepNumber != outages_currentticket.rtepNumber
                    OR outages_historicticket.previousStatus != outages_currentticket.previousStatus));""".format(
            mod_date)
        c.execute(sql)

    def insert_changed(self):
        """
        Inserts new ticket entry to replace previously invalided entry

        :return: Returns nothing, does SQL I/O
        """
        c = connection.cursor()
        sql = """
        INSERT INTO outages_historicticket
        (ticket_number, status, lastRevised, outageType, approvalRisk, availability, rtepNumber, previousStatus, validFrom,
        validTo, currentStatus)
        SELECT ticket_number, status, lastRevised, outageType, approvalRisk, availability, rtepNumber, previousStatus, validFrom,
        validTo, 'Y'
        FROM outages_currentticket
        WHERE EXISTS(SELECT * FROM outages_historicticket
              WHERE outages_historicticket.currentStatus LIKE 'Y'
              AND outages_historicticket.ticket_number = outages_currentticket.ticket_number
              AND (outages_historicticket.status != outages_currentticket.status
                      OR outages_historicticket.lastRevised != outages_currentticket.lastRevised
                      OR outages_historicticket.outageType != outages_currentticket.outageType
                      OR outages_historicticket.approvalRisk != outages_currentticket.approvalRisk
                      OR outages_historicticket.availability != outages_currentticket.availability
                      OR outages_historicticket.rtepNumber != outages_currentticket.rtepNumber
                      OR outages_historicticket.previousStatus != outages_currentticket.previousStatus));"""
        c.execute(sql)

    def insert_new(self):
        """
        Inserts tickets that have been added to the most recent outage file

        :return: Returns nothing, does SQL I/O
        """
        c = connection.cursor()
        sql = """
        INSERT INTO outages_historicticket
        (ticket_number, status, lastRevised, outageType, approvalRisk, availability, rtepNumber, previousStatus, validFrom,
        validTo, currentStatus)
        SELECT ticket_number, status, lastRevised, outageType, approvalRisk, availability, rtepNumber, previousStatus, validFrom,
        validTo, 'Y'
        FROM outages_currentticket
        WHERE NOT EXISTS(SELECT * FROM outages_historicticket
              WHERE outages_historicticket.currentStatus LIKE 'Y'
                AND outages_historicticket.ticket_number = outages_currentticket.ticket_number);"""
        c.execute(sql)


class CurrentTicket(models.Model):
    """
    Class to define CurrentTicket entity
    """
    ticket_number = models.IntegerField()
    status = models.CharField(max_length=9)
    lastRevised = models.DateTimeField(null=True)
    outageType = models.CharField(max_length=27)
    approvalRisk = models.CharField(max_length=8)
    availability = models.CharField(max_length=9)
    rtepNumber = models.CharField(max_length=9)
    previousStatus = models.CharField(max_length=11)
    validFrom = models.DateTimeField()
    validTo = models.DateTimeField(null=True)
    objects = CurrentTicketManager()


class Zone(models.Model):
    """
    Class to define Zone entity
    """
    zoneName = models.CharField(max_length=8, unique=True)


class Station(models.Model):
    """
    Class to define Station entity
    """
    stationName = models.CharField(max_length=8, unique=True)


class Equipment(models.Model):
    """
    Class to define Equipment entity
    """
    equipmentName = models.CharField(max_length=32, unique=True)
    equipmentType = models.CharField(max_length=4)
    station = models.ForeignKey(Station)
    voltageLevel = models.IntegerField()
    voltageMeasurementUnit = models.CharField(max_length=8)


class CurrentPlannedOutage(models.Model):
    """
    Class to define PlannedOutage entity
    """
    ticket = models.ForeignKey(CurrentTicket)
    ticket_number = models.IntegerField()
    lineNumber = models.IntegerField()
    facility = models.ForeignKey(Equipment)
    zone = models.ForeignKey(Zone)
    station = models.ForeignKey(Station)
    startTime = models.DateTimeField()
    endTime = models.DateTimeField()
    openClosed = models.CharField(max_length=1)
    validFrom = models.DateTimeField()
    validTo = models.DateTimeField(null=True)
    objects = CurrentPlannedOutageManager()


class OutageCauses(models.Model):
    """
    Class to define OutageCauses entity
    """
    ticket_number = models.IntegerField()
    ticket = models.ManyToManyField(CurrentTicket)
    cause = models.CharField(max_length=78, unique=True)


class HistoricTicket(models.Model):
    """
    Class to define CurrentTicket history table
    """
    ticket_number = models.IntegerField()
    status = models.CharField(max_length=9)
    lastRevised = models.DateTimeField(null=True)
    outageType = models.CharField(max_length=27)
    approvalRisk = models.CharField(max_length=8)
    availability = models.CharField(max_length=9)
    rtepNumber = models.CharField(max_length=9)
    previousStatus = models.CharField(max_length=11)
    validFrom = models.DateTimeField()
    validTo = models.DateTimeField(null=True)
    currentStatus = models.CharField(max_length=1)
    objects = HistoricTicketManager()


class HistoricPlannedOutage(models.Model):
    """
    Class to define CurrentOutage history table
    """
    ticket = models.ForeignKey(HistoricTicket)
    ticket_number = models.IntegerField()
    facility = models.ForeignKey(Equipment)
    lineNumber = models.IntegerField()
    zone = models.ForeignKey(Zone)
    station = models.ForeignKey(Station)
    startTime = models.DateTimeField()
    endTime = models.DateTimeField()
    openClosed = models.CharField(max_length=1)
    validFrom = models.DateTimeField()
    validTo = models.DateTimeField(null=True)
    currentStatus = models.CharField(max_length=1)
    objects = HistoricPlannedOutageManager()
