from django.db import connection
from datetime import datetime

def _to_date_string(date):
    return datetime.strftime(date, "%Y-%m-%d %H:%M")

def get_current_outages():
    c = connection.cursor()
    sql ="""
        SELECT
          outages_currentticket.ticket_number,
          zoneName,
          equipmentName,
          equipmentType,
          voltageLevel,
          voltageMeasurementUnit,
          startTime,
          endTime,
          openClosed,
          status,
          lastRevised,
          approvalRisk,
          availability,
          rtepNumber,
          previousStatus
        FROM outages_currentplannedoutage
          LEFT JOIN outages_currentticket
            ON outages_currentplannedoutage.ticket_id = outages_currentticket.id
          LEFT JOIN outages_zone
            ON outages_currentplannedoutage.zone_id = outages_zone.id
          LEFT JOIN outages_equipment
            ON outages_currentplannedoutage.facility_id = outages_equipment.id
    """
    res = c.execute(sql)
    return res.fetchall()

def get_historic_outages(date1):
    date1 = _to_date_string(date1)
    c = connection.cursor()
    sql = """
            SELECT
              outages_historicticket.ticket_number,
              zoneName,
              equipmentName,
              equipmentType,
              voltageLevel,
              voltageMeasurementUnit,
              startTime,
              endTime,
              openClosed,
              status,
              lastRevised,
              approvalRisk,
              availability,
              rtepNumber,
              previousStatus
            FROM outages_historicplannedoutage
              LEFT JOIN outages_historicticket
                ON outages_historicplannedoutage.ticket_id = outages_historicticket.id
              LEFT JOIN outages_zone
                ON outages_historicplannedoutage.zone_id = outages_zone.id
              LEFT JOIN outages_equipment
                ON outages_historicplannedoutage.facility_id = outages_equipment.id
            WHERE outages_historicplannedoutage.validFrom < '{date1}'
                  AND (
                    outages_historicplannedoutage.validTo > '{date1}' OR
                    outages_historicplannedoutage.validTo ISNULL
                  )
      """.format(**{'date1': date1})
    res = c.execute(sql)
    return res.fetchall()

def get_diff_added_outages(date1, date2):
    date1 = _to_date_string(date1)
    date2 = _to_date_string(date2)

    c = connection.cursor()
    sql = """
        SELECT
          ticket_number,
          zoneName,
          equipmentName,
          equipmentType,
          voltageLevel,
          voltageMeasurementUnit,
          startTime,
          endTime,
          openClosed,
          status,
          lastRevised,
          approvalRisk,
          availability,
          rtepNumber,
          previousStatus
        FROM (SELECT *
              FROM outages_historicplannedoutage
                LEFT JOIN outages_historicticket
                        ON outages_historicplannedoutage.ticket_id = outages_historicticket.id
                      LEFT JOIN outages_zone
                        ON outages_historicplannedoutage.zone_id = outages_zone.id
                      LEFT JOIN outages_equipment
                        ON outages_historicplannedoutage.facility_id = outages_equipment.id
              WHERE outages_historicplannedoutage.validFrom < '{date1}'
                    AND ('({date1}' < outages_historicplannedoutage.validTo
                         OR outages_historicplannedoutage.validTo ISNULL)
             ) AS current
        WHERE NOT EXISTS(SELECT *
                         FROM outages_historicplannedoutage AS history
                         WHERE history.validFrom < '{date2}'
                               AND ('{date2}' < history.validTo
                                    OR history.validTo ISNULL)
                               AND current.ticket_id = history.ticket_id
                               AND current.facility_id = history.facility_id
                               AND current.lineNumber = history.lineNumber);
        """.format(**{'date1': date1, 'date2': date2})
    res = c.execute(sql)
    return res.fetchall()

def get_diff_removed_outages(date1, date2):
    date1 = _to_date_string(date1)
    date2 = _to_date_string(date2)

    c = connection.cursor()
    sql ="""
        SELECT
          ticket_number,
          zoneName,
          equipmentName,
          equipmentType,
          voltageLevel,
          voltageMeasurementUnit,
          startTime,
          endTime,
          openClosed,
          status,
          lastRevised,
          approvalRisk,
          availability,
          rtepNumber,
          previousStatus
        FROM (SELECT *
              FROM outages_historicplannedoutage
                LEFT JOIN outages_historicticket
                  ON outages_historicplannedoutage.ticket_id = outages_historicticket.id
                LEFT JOIN outages_zone
                  ON outages_historicplannedoutage.zone_id = outages_zone.id
                LEFT JOIN outages_equipment
                  ON outages_historicplannedoutage.facility_id = outages_equipment.id
              WHERE outages_historicplannedoutage.validFrom < '{date2}'
                    AND ('{date2}' < outages_historicplannedoutage.validTo
                         OR outages_historicplannedoutage.validTo ISNULL)
             ) AS current
        WHERE NOT EXISTS(SELECT *
                         FROM outages_historicplannedoutage AS history
                         WHERE history.validFrom < '{date1}'
                               AND ('{date1}' < history.validTo OR history.validTo ISNULL)
                               AND current.ticket_id = history.ticket_id
                               AND current.facility_id = history.facility_id
                               AND current.lineNumber = history.lineNumber)
    """.format(**{'date1': date1, 'date2': date2})
    res = c.execute(sql)
    return res.fetchall()

def get_diff_changed_to_outages(date1, date2):
    date1 = _to_date_string(date1)
    date2 = _to_date_string(date2)

    c = connection.cursor()
    sql ="""
        SELECT
          ticket_number,
          zoneName,
          equipmentName,
          equipmentType,
          voltageLevel,
          voltageMeasurementUnit,
          startTime,
          endTime,
          openClosed,
          status,
          lastRevised,
          approvalRisk,
          availability,
          rtepNumber,
          previousStatus
        FROM (
               SELECT *
               FROM outages_historicplannedoutage
                 LEFT JOIN outages_historicticket
                   ON outages_historicplannedoutage.ticket_id = outages_historicticket.id
                 LEFT JOIN outages_zone
                   ON outages_historicplannedoutage.zone_id = outages_zone.id
                 LEFT JOIN outages_equipment
                   ON outages_historicplannedoutage.facility_id = outages_equipment.id
               WHERE outages_historicplannedoutage.validFrom < '{date1}'
                     AND ('{date1}' < outages_historicplannedoutage.validTo
                          OR outages_historicplannedoutage.validTo ISNULL))
          AS current
        WHERE EXISTS(
            SELECT *
            FROM (
                   SELECT *
                   FROM outages_historicplannedoutage
                   WHERE outages_historicplannedoutage.validFrom < '{date2}'
                         AND ('{date2}' < outages_historicplannedoutage.validTo
                              OR outages_historicplannedoutage.validTo ISNULL))
              AS history
            WHERE current.ticket_id = history.ticket_id
                  AND current.facility_id = history.facility_id
                  AND current.lineNumber = history.lineNumber
                  AND (current.startTime != history.startTime
                       OR current.endTime != history.endTime
                       OR current.openClosed != history.openClosed))
    """.format(**{'date1': date1, 'date2': date2})
    res = c.execute(sql)
    return res.fetchall()

def get_diff_changed_from_outages(date1, date2):
    date1 = _to_date_string(date1)
    date2 = _to_date_string(date2)

    c = connection.cursor()
    sql ="""
        SELECT
          ticket_number,
          zoneName,
          equipmentName,
          equipmentType,
          voltageLevel,
          voltageMeasurementUnit,
          startTime,
          endTime,
          openClosed,
          status,
          lastRevised,
          approvalRisk,
          availability,
          rtepNumber,
          previousStatus
        FROM (
               SELECT *
               FROM outages_historicplannedoutage
                 LEFT JOIN outages_historicticket
                   ON outages_historicplannedoutage.ticket_id = outages_historicticket.id
                 LEFT JOIN outages_zone
                   ON outages_historicplannedoutage.zone_id = outages_zone.id
                 LEFT JOIN outages_equipment
                   ON outages_historicplannedoutage.facility_id = outages_equipment.id
               WHERE outages_historicplannedoutage.validFrom < '{date2}'
                     AND ('{date2}' < outages_historicplannedoutage.validTo
                          OR outages_historicplannedoutage.validTo ISNULL))
          AS current
        WHERE EXISTS(
            SELECT *
            FROM (
                   SELECT *
                   FROM outages_historicplannedoutage
                   WHERE outages_historicplannedoutage.validFrom < '{date1}'
                         AND ('{date1}' < outages_historicplannedoutage.validTo
                              OR outages_historicplannedoutage.validTo ISNULL))
              AS history
            WHERE current.ticket_id = history.ticket_id
                  AND current.facility_id = history.facility_id
                  AND current.lineNumber = history.lineNumber
                  AND (current.startTime != history.startTime
                       OR current.endTime != history.endTime
                       OR current.openClosed != history.openClosed))
    """.format(**{'date1': date1, 'date2': date2})
    res = c.execute(sql)
    return res.fetchall()
