from django.db import models
from datetime import datetime
from enum import Enum


class OBISTable(models.Model):
    class Meta:
        abstract = True
        app_label = "andesOBIS"

    @classmethod
    def obis_datetime_str(cls, dt: datetime, precision: int) -> str:
        if precision == 1:
            return dt.strftime("%Y")
        elif precision == 2:
            return dt.strftime("%Y-%m")
        elif precision == 3:
            return dt.strftime("%Y-%m-%d")
        elif precision == 4:
            return dt.strftime("%Y-%m-%dT%H%z")
        elif precision == 5:
            return dt.strftime("%Y-%m-%dT%H:%M%z")
        elif precision == 6:
            return dt.strftime("%Y-%m-%dT%H:%M%S%z")
        elif precision == 7:
            return dt.strftime("%Y-%m-%dT%H:%M%S.%f%z")
        else:
            raise ValueError("Precision not implemented")


class Event(OBISTable):

    datetime_precision_choices = [
        (1, "year"),
        (2, "month"),
        (3, "day"),
        (4, "hour"),
        (5, "minute"),
        (6, "second"),
        (7, "millisecond"),
    ]

    ####
    ### obligatoire (excluding private members)
    ####

    eventID = models.CharField(
        primary_key=True,
        max_length=255,
        verbose_name="An identifier for the set of information associated with a dwc:Event (something that occurs at a place and time). May be a global unique identifier or an identifier specific to the data set.",
    )
    _parentEvent = models.ForeignKey(
        "Event",
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        verbose_name="An identifier for the broader dwc:Event that groups this and potentially other dwc:Events",
    )

    @property
    def parentEventID(self) -> str:
        """parent EventID
        An identifier for the broader dwc:Event that groups this and potentially other dwc:Events
        """
        if self._parentEvent:
            return self._parentEvent.eventID
        else:
            return None

    parentEventID.fget.short_description = "An identifier for the broader dwc:Event that groups this and potentially other dwc:Events"

    @property
    def eventDate(self) -> str:
        """Event Date
        http://rs.tdwg.org/dwc/terms/eventDate
        """
        if self._event_start_dt and self._event_end_dt:
            start_dt_str = OBISTable.obis_datetime_str(
                self._event_start_dt, self._event_start_dt_p
            )
            end_dt_str = OBISTable.obis_datetime_str(
                self._event_start_dt, self._event_end_dt_p
            )
            return f"{start_dt_str}/{end_dt_str}"
        else:
            start_dt_str = OBISTable.obis_datetime_str(
                self._event_start_dt, self._event_start_dt_p
            )
            return f"{start_dt_str}"

    eventDate.fget.short_description = "The date-time or interval during which a dwc:Event occurred. For occurrences, this is the date-time when the dwc:Event was recorded. Not suitable for a time in a geological context."

    _event_start_dt = models.DateTimeField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Private datetime variable for the start date",
    )
    _event_start_dt_p = models.IntegerField(
        verbose_name="Private datetime variable for the start date precision",
        choices=datetime_precision_choices,
        default=6,
    )
    _event_end_dt = models.DateTimeField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Private datetime variable for the start date",
    )
    _event_end_dt_p = models.IntegerField(
        verbose_name="Private datetime variable for the start date precision",
        choices=datetime_precision_choices,
        default=6,
    )
    decimalLatitude = models.DecimalField(
        blank=True,
        null=True,
        default=None,
        decimal_places=6,
        max_digits=8,
        verbose_name="The geographic latitude (in decimal degrees, using the spatial reference system given in dwc:geodeticDatum) of the geographic center of a dcterms:Location. Positive values are north of the Equator, negative values are south of it. Legal values lie between -90 and 90, inclusive.",
    )
    decimalLongitude = models.DecimalField(
        blank=True,
        null=True,
        default=None,
        decimal_places=6,
        max_digits=9,
        verbose_name="The geographic longitude (in decimal degrees, using the spatial reference system given in dwc:geodeticDatum) of the geographic center of a dcterms:Location. Positive values are east of the Greenwich Meridian, negative values are west of it. Legal values lie between -180 and 180, inclusive.",
    )

    ####
    # Fortement Recommendé (excluding private members)
    ####

    @property
    def month(self) -> str:
        """The integer month in which the dwc:Event occurred.
        http://rs.tdwg.org/dwc/terms/month
        """
        return self._event_start_dt.strftime("%m")

    month.fget.short_description = "The integer month in which the dwc:Event occurred."

    @property
    def year(self) -> str:
        """The four-digit year in which the dwc:Event occurred, according to the Common Era Calendar.
        http://rs.tdwg.org/dwc/terms/year
        """
        return self._event_start_dt.strftime("%Y")

    year.fget.short_description = "The four-digit year in which the dwc:Event occurred, according to the Common Era Calendar."

    continent = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="The name of the continent in which the dcterms:Location occurs.",
        help_text="http://rs.tdwg.org/dwc/terms/continent",
    )

    coordinatePrecision = models.DecimalField(
        blank=True,
        null=True,
        default=None,
        decimal_places=6,
        max_digits=7,
        verbose_name="A decimal representation of the precision of the coordinates given in the dwc:decimalLatitude and dwc:decimalLongitude.",
        help_text="http://rs.tdwg.org/dwc/terms/coordinatePrecision",
    )

    coordinateUncertaintyInMeters = models.DecimalField(
        blank=True,
        null=True,
        default=None,
        decimal_places=6,
        max_digits=12,
        verbose_name="The horizontal distance (in meters) from the given dwc:decimalLatitude and dwc:decimalLongitude describing the smallest circle containing the whole of the dcterms:Location. Leave the value empty if the uncertainty is unknown, cannot be estimated, or is not applicable (because there are no coordinates). Zero is not a valid value for this term.",
        help_text="http://rs.tdwg.org/dwc/terms/coordinateUncertaintyInMeters",
    )

    eventType = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="The nature of the dwc:Event. https://registry.gbif-uat.org/vocabulary/EventType/concepts",
        help_text="http://rs.tdwg.org/dwc/terms/eventTypet",
    )

    maximumDepthInMeters = models.DecimalField(
        blank=True,
        null=True,
        default=None,
        decimal_places=3,
        max_digits=6,
        verbose_name="The greater depth of a range of depth below the local surface, in meters.",
        help_text="http://rs.tdwg.org/dwc/terms/maximumDepthInMeters",
    )
    minimumDepthInMeters = models.DecimalField(
        blank=True,
        null=True,
        default=None,
        decimal_places=3,
        max_digits=6,
        verbose_name="The lesser depth of a range of depth below the local surface, in meters.",
        help_text="http://rs.tdwg.org/dwc/terms/minimumDepthInMeterss",
    )

    @property
    def language(self) -> str:
        """A language of the resource.
        http://purl.org/dc/terms/language

        """
        return "En"

    language.fget.short_description = "A language of the resource. Recommended best practice is to use an IRI from the Library of Congress ISO 639-2 scheme http://id.loc.gov/vocabulary/iso639-2"

    @property
    def license(self) -> str:
        """A legal document giving official permission to do something with the resource.

        http://purl.org/dc/terms/license
        """
        return "http://creativecommons.org/licenses/by/4.0/legalcode"

    language.fget.short_description = (
        "A legal document giving official permission to do something with the resource."
    )

    @property
    def rightsHolder(self) -> str:
        """A person or organization owning or managing rights over the resource.

        http://purl.org/dc/terms/rightsHolder
        """
        return "His Majesty the King in right of Canada, as represented by the Minister of Fisheries and Oceans"

    language.fget.short_description = (
        "A person or organization owning or managing rights over the resource."
    )

    @property
    def datasetID(self) -> str | None:
        """An identifier for the set of data. May be a global unique identifier or an identifier specific to a collection or institution.

        http://rs.tdwg.org/dwc/terms/datasetID
        """
        return None

    datasetID.fget.short_description = "An identifier for the set of data. May be a global unique identifier or an identifier specific to a collection or institution."

    @property
    def institutionID(self) -> str | None:
        """An identifier for the institution having custody of the object(s) or information referred to in the record.

        http://rs.tdwg.org/dwc/terms/institutionID

        For physical specimens, the recommended best practice is to use a globally unique and resolvable identifier from a collections registry such as the Research Organization Registry (ROR) or the GBIF Registry of Scientific Collections (https://www.gbif.org/grscicoll).

        """
        # FOR IML use https://edmo.seadatanet.org/report/4160
        return None

    institutionID.fget.short_description = "An identifier for the institution having custody of the object(s) or information referred to in the record."

    @property
    def institutionCode(self) -> str | None:
        """The name (or acronym) in use by the institution having custody of the object(s) or information referred to in the record.

        http://rs.tdwg.org/dwc/terms/institutionCode
        """
        # for IML, use "IML"
        return None

    institutionCode.fget.short_description = "The name (or acronym) in use by the institution having custody of the object(s) or information referred to in the record."

    @property
    def datasetName(self) -> str | None:
        """The name identifying the data set from which the record was derived.

        http://rs.tdwg.org/dwc/terms/datasetName
        """
        return None

    datasetName.fget.short_description = (
        "The name identifying the data set from which the record was derived."
    )

    # IML uses station name when the event is a Set
    fieldNumber = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="An identifier given to the dwc:Event in the field. Often serves as a link between field notes and the dwc:Event.",
        help_text="http://rs.tdwg.org/dwc/terms/fieldNumber",
    )

    # TODO
    # locationID

    ####
    # Recommendé (excluding private members)
    ####
    footprintWKT = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=511,
        verbose_name="A Well-Known Text (WKT) representation of the shape (footprint, geometry) that defines the dcterms:Location. A dcterms:Location may have both a point-radius representation (see dwc:decimalLatitude) and a footprint representation, and they may differ from each other.",
        help_text="http://rs.tdwg.org/dwc/terms/footprintWKT",
    )

    # TODO
    # day
    # endDayOfYear
    # eventTime
    # habitat
    # startDayOfYear
    # verbatimEventDate
    # country
    # footprintWKT
    # geodeticDatum
    # locality
    # locationAccordingTo
    # locationRemarks
    # waterBody
    # accessRights
    # bibliographicCitation
    # datasetID
    # datasetName
    # dynamicProperties
    # language
    # license
    # modified
    # references
    # rightsHolder

    ####
    # Facultatif (excluding private members)
    ####
    # TODO

    eventRemarks = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        verbose_name="Comments or notes about the dwc:Event.",
    )
    # footprintSRS


class Occurrence(OBISTable):
    occurenceID = models.CharField(
        primary_key=True,
        max_length=255,
        verbose_name="An identifier for the dwc:Occurrence (as opposed to a particular digital record of the dwc:Occurrence). In the absence of a persistent global unique identifier, construct one from a combination of identifiers in the record that will most closely make the dwc:occurrenceID globally unique.",
    )

    _event = models.ForeignKey(Event, on_delete=models.CASCADE)

    @property
    def eventID(self) -> str:
        """parent EventID
        An identifier for the set of information associated with a dwc:Event (something that occurs at a place and time). May be a global unique identifier or an identifier specific to the data set.

        """
        return self._event.eventID

    eventID.fget.short_description = "An identifier for the set of information associated with a dwc:Event (something that occurs at a place and time). May be a global unique identifier or an identifier specific to the data set."

    verbatimIdentification = models.CharField(
        max_length=255,
        verbose_name="A string representing the taxonomic identification as it appeared in the original record.",
    )
    scientificName = models.CharField(
        max_length=255,
        verbose_name="The full scientific name, with authorship and date information if known. When forming part of a dwc:Identification, this should be the name in lowest level taxonomic rank that can be determined. This term should not contain identification qualifications, which should instead be supplied in the dwc:identificationQualifier term.",
    )
    scientificNameID = models.CharField(
        max_length=255,
        verbose_name="An identifier for the nomenclatural (not taxonomic) details of a scientific name.",
    )
    basisOfRecord = models.CharField(
        max_length=255, verbose_name="The specific nature of the data record."
    )
    occurrenceStatus = models.CharField(
        max_length=255,
        verbose_name="A statement about the presence or absence of a dwc:Taxon at a dcterms:Location",
    )
    associatedMedia = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=255,
        verbose_name="A list (concatenated and separated) of identifiers (publication, global unique identifier, URI) of media associated with the dwc:Occurrence.",
    )
    taxonRemarks = models.CharField(
        max_length=255,
        verbose_name="A statement about the presence or absence of a dwc:Taxon at a dcterms:Location",
    )


class eMoF(OBISTable):
    eventID = models.ForeignKey(Event, on_delete=models.CASCADE)
    occurenceID = models.ForeignKey(Occurrence, on_delete=models.CASCADE)
    measurementType = models.CharField(
        max_length=255,
        verbose_name="The nature of the measurement, fact, characteristic, or assertion",
    )
    measurementValue = models.CharField(
        max_length=255,
        verbose_name="Recommended best practice is to use a controlled vocabulary. This term has an equivalent in the dwciri: namespace that allows only an IRI as a value, whereas this term allows for any string literal value.",
    )
    measurementUnit = models.CharField(
        max_length=255,
        verbose_name="Recommended best practice is to use the International System of Units (SI). This term has an equivalent in the dwciri: namespace that allows only an IRI as a value, whereas this term allows for any string literal value. ",
    )
    measurementTypeID = models.CharField(
        max_length=255,
        verbose_name="An identifier for the measurementType (global unique identifier, URI). The identifier should reference the measurementType in a vocabulary.",
    )
    measurementValueID = models.CharField(
        max_length=255,
        verbose_name="An identifier for facts stored in the column measurementValue (global unique identifier, URI). This identifier can reference a controlled vocabulary (e.g. for sampling instrument names, methodologies, life stages) or reference a methodology paper with a DOI. When the measurementValue refers to a value and not to a fact, the measurementvalueID has no meaning and should remain empty.",
    )
    measurementRemarks = models.CharField(
        max_length=255,
        verbose_name="Comments or notes accompanying the dwc:MeasurementOrFact.",
    )
