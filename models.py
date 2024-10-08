from django.db import models
from datetime import datetime
import logging
import pytz

from shapely import LineString
from ecosystem_survey.models import Catch
from shared_models.models import Cruise, Set
from shared_models.utils import calc_nautical_dist

# Exceptions
class NoCatchData(Exception):
    pass
class InvalidSpecies(Exception):
    pass
class NoParentCruiseError(Exception):
    pass

class OBISTable(models.Model):


    class Meta:
        abstract = True
        app_label = "andesOBIS"

    @classmethod
    def obis_datetime_str(cls, dt: datetime, precision: int, tz=None) -> str:
        if tz:
            dt_in_user_timezone=dt.astimezone(pytz.timezone(tz))
        else:
            dt_in_user_timezone = dt
        if precision == 1:
            return dt_in_user_timezone.strftime("%Y")
        elif precision == 2:
            return dt_in_user_timezone.strftime("%Y-%m")
        elif precision == 3:
            return dt_in_user_timezone.strftime("%Y-%m-%d")
        elif precision == 4:
            return dt_in_user_timezone.strftime("%Y-%m-%dT%H%z")
        elif precision == 5:
            return dt_in_user_timezone.strftime("%Y-%m-%dT%H:%M%z")
        elif precision == 6:
            return dt_in_user_timezone.strftime("%Y-%m-%dT%H:%M:%S%z")
        elif precision == 7:
            return dt_in_user_timezone.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            raise ValueError("Precision not implemented")

    @classmethod
    def obis_time_str(cls, dt: datetime, precision: int, tz=None) -> str:
        if tz:
            dt_in_user_timezone=dt.astimezone(pytz.timezone(tz))
        else:
            dt_in_user_timezone = dt
        if precision == 4:
            return dt_in_user_timezone.strftime("%H%z")
        elif precision == 5:
            return dt_in_user_timezone.strftime("%H:%M%z")
        elif precision == 6:
            return dt_in_user_timezone.strftime("%H:%M:%S%z")
        elif precision == 7:
            return dt_in_user_timezone.strftime("%H:%M:%S.%f%z")
        else:
            raise ValueError("Precision not implemented")


class Event(OBISTable):
    andes_object = None
    datetime_precision_choices = [
        (1, "year"),
        (2, "month"),
        (3, "day"),
        (4, "hour"),
        (5, "minute"),
        (6, "second"),
        (7, "millisecond"),
    ]
    
    eventID = models.CharField(
        primary_key=True,
        max_length=255,
        verbose_name="An identifier for the set of information associated with a dwc:Event (something that occurs at a place and time). May be a global unique identifier or an identifier specific to the data set.",
        help_text="http://rs.tdwg.org/dwc/terms/eventID",
    )
    # Private actual parent event object 
    _parentEvent = models.ForeignKey(
        "Event",
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        verbose_name="An identifier for the broader dwc:Event that groups this and potentially other dwc:Events",
        help_text="http://rs.tdwg.org/dwc/terms/eventID",
    )

    @property
    def parentEventID(self) -> str|None:
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

        The date-time or interval during which a dwc:Event occurred. For occurrences, this is the date-time when the dwc:Event was recorded. Not suitable for a time in a geological context.

        """
        if self._event_start_dt and self._event_end_dt:
            start_dt_str = OBISTable.obis_datetime_str(
                self._event_start_dt, self._event_start_dt_p, tz=self.timezone
            )
            end_dt_str = OBISTable.obis_datetime_str(
                self._event_end_dt, self._event_end_dt_p, tz=self.timezone
            )
            return f"{start_dt_str}/{end_dt_str}"
        else:
            start_dt_str = OBISTable.obis_datetime_str(
                self._event_start_dt, self._event_start_dt_p, tz=self.timezone
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
        help_text="http://rs.tdwg.org/dwc/terms/decimalLatitude"
    )
    decimalLongitude = models.DecimalField(
        blank=True,
        null=True,
        default=None,
        decimal_places=6,
        max_digits=9,
        verbose_name="The geographic longitude (in decimal degrees, using the spatial reference system given in dwc:geodeticDatum) of the geographic center of a dcterms:Location. Positive values are east of the Greenwich Meridian, negative values are west of it. Legal values lie between -180 and 180, inclusive.",
        help_text="http://rs.tdwg.org/dwc/terms/decimalLongitude"
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
    @property
    def geodeticDatum(self) -> str|None:
        """The ellipsoid, geodetic datum, or spatial reference system (SRS) upon which the geographic coordinates given in dwc:decimalLatitude and dwc:decimalLongitude are based.

        Recommended best practice is to use the EPSG code of the SRS, if known. Otherwise use a controlled vocabulary for the name or code of the geodetic datum, if known. Otherwise use a controlled vocabulary for the name or code of the ellipsoid, if known. If none of these is known, use the value unknown. This term has an equivalent in the dwciri: namespace that allows only an IRI as a value, whereas this term allows for any string literal value.
        http://rs.tdwg.org/dwc/terms/geodeticDatum
        """
        if self.decimalLongitude or self.decimalLatitude:
            return "epsg:4326"
        else:
            return None
    geodeticDatum.fget.short_description = "The ellipsoid, geodetic datum, or spatial reference system (SRS) upon which the geographic coordinates given in dwc:decimalLatitude and dwc:decimalLongitude are based."


    @property
    def eventTime(self) -> str|None:
        """The time or interval during which a dwc:Event occurred.
        http://rs.tdwg.org/dwc/terms/eventTime
        """
        if self._event_start_dt and self._event_end_dt:
            start_dt_str = OBISTable.obis_time_str(
                self._event_start_dt, self._event_start_dt_p, tz=self.timezone
            )
            end_dt_str = OBISTable.obis_time_str(
                self._event_end_dt, self._event_end_dt_p, tz=self.timezone
            )
            return f"{start_dt_str}/{end_dt_str}"
        elif self._event_start_dt:
            start_dt_str = OBISTable.obis_time_str(
                self._event_start_dt, self._event_start_dt_p, tz=self.timezone
            )
            return f"{start_dt_str}"
        else:
            return None
    eventTime.fget.short_description = "The time or interval during which a dwc:Event occurred."

    # @property
    # def month(self) -> str|None:
    #     """The integer month in which the dwc:Event occurred.
    #     http://rs.tdwg.org/dwc/terms/month
    #     """
    #     if self._event_start_dt:
    #         return self._event_start_dt.strftime("%m")
    #     # elif self._event_end_dt:
    #     #     return self._event_end_dt.strftime("%m")
    #     else:
    #         return None
    # month.fget.short_description = "The integer month in which the dwc:Event occurred."

    @property
    def year(self) -> str:
        """The four-digit year in which the dwc:Event occurred, according to the Common Era Calendar.
        http://rs.tdwg.org/dwc/terms/year
        """
        if self._event_start_dt:
            return self._event_start_dt.strftime("%Y")
        # elif self._event_end_dt:
        #     return self._event_end_dt.strftime("%Y")
        else:
            return None
    year.fget.short_description = "The four-digit year in which the dwc:Event occurred, according to the Common Era Calendar."

    continent = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="The name of the continent in which the dcterms:Location occurs.",
        help_text="http://rs.tdwg.org/dwc/terms/continent",
    )

    # @property
    # def continent(self) -> str:
    #     """The name of the continent in which the dcterms:Location occurs.
    #     http://rs.tdwg.org/dwc/terms/continent
    #     Recommended best practice is to use a controlled vocabulary such as the Getty Thesaurus of Geographic Names. Recommended best practice is to leave this field blank if the dcterms:Location spans multiple entities at this administrative level or if the dcterms:Location might be in one or another of multiple possible entities at this level. Multiplicity and uncertainty of the geographic entity can be captured either in the term dwc:higherGeography or in the term dwc:locality, or both.
    #     """
    #     return "North America"
    # continent.fget.short_description = "The name of the continent in which the dcterms:Location occurs."

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

    language = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=63,
        verbose_name="A language of the resource. Recommended best practice is to use an IRI from the Library of Congress ISO 639-2 scheme http://id.loc.gov/vocabulary/iso639-2",
        help_text="http://purl.org/dc/terms/language",
    )
    # @property
    # def language(self) -> str:
    #     """A language of the resource.
    #     http://purl.org/dc/terms/language
    #     """
    #     return "En"
    # language.fget.short_description = "A language of the resource. Recommended best practice is to use an IRI from the Library of Congress ISO 639-2 scheme http://id.loc.gov/vocabulary/iso639-2"

    license = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=255,
        verbose_name="A legal document giving official permission to do something with the resource.",
        help_text="http://purl.org/dc/terms/license",
    )

    # @property
    # def license(self) -> str:
    #     """A legal document giving official permission to do something with the resource.
    #     http://purl.org/dc/terms/license
    #     """
    #     return "http://creativecommons.org/licenses/by/4.0/legalcode"
    # language.fget.short_description = (
    #     "A legal document giving official permission to do something with the resource."
    # )

    license = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="A person or organization owning or managing rights over the resource.",
        help_text="http://purl.org/dc/terms/rightsHolder",
    )

    # @property
    # def rightsHolder(self) -> str:
    #     """A person or organization owning or managing rights over the resource.
    #     http://purl.org/dc/terms/rightsHolder
    #     """
    #     return "His Majesty the King in right of Canada, as represented by the Minister of Fisheries and Oceans"
    # language.fget.short_description = (
    #     "A person or organization owning or managing rights over the resource."
    # )

    datasetID = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="An identifier for the set of data. May be a global unique identifier or an identifier specific to a collection or institution.",
        help_text="http://rs.tdwg.org/dwc/terms/datasetID",
    )

    # @property
    # def datasetID(self) -> str | None:
    #     """An identifier for the set of data. May be a global unique identifier or an identifier specific to a collection or institution.
    #     http://rs.tdwg.org/dwc/terms/datasetID
    #     """
    #     return None
    # datasetID.fget.short_description = "An identifier for the set of data. May be a global unique identifier or an identifier specific to a collection or institution."

    institutionID = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="An identifier for the institution having custody of the object(s) or information referred to in the record.",
        help_text="http://rs.tdwg.org/dwc/terms/institutionID",
    )

    # @property
    # def institutionID(self) -> str | None:
    #     """An identifier for the institution having custody of the object(s) or information referred to in the record.
    #     http://rs.tdwg.org/dwc/terms/institutionID
    #     For physical specimens, the recommended best practice is to use a globally unique and resolvable identifier from a collections registry such as the Research Organization Registry (ROR) or the GBIF Registry of Scientific Collections (https://www.gbif.org/grscicoll).
    #     """
    #     # FOR IML use https://edmo.seadatanet.org/report/4160
    #     return None
    # institutionID.fget.short_description = "An identifier for the institution having custody of the object(s) or information referred to in the record."

    institutionCode = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="The name (or acronym) in use by the institution having custody of the object(s) or information referred to in the record.",
        help_text="http://rs.tdwg.org/dwc/terms/institutionCode",
    )
    # @property
    # def institutionCode(self) -> str | None:
    #     """The name (or acronym) in use by the institution having custody of the object(s) or information referred to in the record.
    #     http://rs.tdwg.org/dwc/terms/institutionCode
    #     """
    #     # for IML, use "IML"
    #     return None
    # institutionCode.fget.short_description = "The name (or acronym) in use by the institution having custody of the object(s) or information referred to in the record."

    datasetName = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="The name identifying the data set from which the record was derived.",
        help_text="http://rs.tdwg.org/dwc/terms/datasetName",
    )

    # @property
    # def datasetName(self) -> str | None:
    #     """The name identifying the data set from which the record was derived.
    #     http://rs.tdwg.org/dwc/terms/datasetName
    #     """
    #     return None
    # datasetName.fget.short_description = (
    #     "The name identifying the data set from which the record was derived."
    # )

    # IML uses station name when the event is a Set and mission number when mission
    fieldNumber = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=127,
        verbose_name="An identifier given to the dwc:Event in the field. Often serves as a link between field notes and the dwc:Event.",
        help_text="http://rs.tdwg.org/dwc/terms/fieldNumber",
    )

    footprintWKT = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=511,
        verbose_name="A Well-Known Text (WKT) representation of the shape (footprint, geometry) that defines the dcterms:Location. A dcterms:Location may have both a point-radius representation (see dwc:decimalLatitude) and a footprint representation, and they may differ from each other.",
        help_text="http://rs.tdwg.org/dwc/terms/footprintWKT",
    )

    @property
    def footprintSRS(self) -> str|None:
        """The ellipsoid, geodetic datum, or spatial reference system (SRS) upon which the geometry given in dwc:footprintWKT is based.

        Recommended best practice is to use the EPSG code of the SRS, if known. Otherwise use a controlled vocabulary for the name or code of the geodetic datum, if known. Otherwise use a controlled vocabulary for the name or code of the ellipsoid, if known. If none of these is known, use the value unknown. It is also permitted to provide the SRS in Well-Known-Text, especially if no EPSG code provides the necessary values for the attributes of the SRS. Do not use this term to describe the SRS of the dwc:decimalLatitude and dwc:decimalLongitude, nor of any verbatim coordinates - use the dwc:geodeticDatum and dwc:verbatimSRS instead. This term has an equivalent in the dwciri: namespace that allows only an IRI as a value, whereas this term allows for any string literal value.
        http://rs.tdwg.org/dwc/terms/footprintSRS
        """
        if self.footprintWKT:
            return "epsg:4326"
        else:
            return None
    footprintSRS.fget.short_description = "The ellipsoid, geodetic datum, or spatial reference system (SRS) upon which the geometry given in dwc:footprintWKT is based."

    countryCode = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=7,
        verbose_name="The standard code for the country in which the dcterms:Location occurs. Recommended best practice is to use an ISO 3166-1-alpha-2 country code. Recommended best practice is to leave this field blank if the dcterms:Location spans multiple entities at this administrative level or if the dcterms:Location might be in one or another of multiple possible entities at this level. Multiplicity and uncertainty of the geographic entity can be captured either in the term dwc:higherGeography or in the term dwc:locality, or both.",
        help_text="http://rs.tdwg.org/dwc/terms/countryCode",
    )

    # @property
    # def countryCode(self) -> str:
    #     """The standard code for the country in which the dcterms:Location occurs.
    #     http://rs.tdwg.org/dwc/terms/countryCode
    #     Recommended best practice is to use an ISO 3166-1-alpha-2 country code. Recommended best practice is to leave this field blank if the dcterms:Location spans multiple entities at this administrative level or if the dcterms:Location might be in one or another of multiple possible entities at this level. Multiplicity and uncertainty of the geographic entity can be captured either in the term dwc:higherGeography or in the term dwc:locality, or both.
    #     """
    #     return "CA"
    # countryCode.fget.short_description = (
    #     "The standard code for the country in which the dcterms:Location occurs."
    # )

    country = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=63,
        verbose_name="The name of the country or major administrative unit in which the dcterms:Location occurs. Recommended best practice is to use a controlled vocabulary such as the Getty Thesaurus of Geographic Names. Recommended best practice is to leave this field blank if the dcterms:Location spans multiple entities at this administrative level or if the dcterms:Location might be in one or another of multiple possible entities at this level. Multiplicity and uncertainty of the geographic entity can be captured either in the term dwc:higherGeography or in the term dwc:locality, or both.",
        help_text="http://rs.tdwg.org/dwc/terms/country",
    )

    # @property
    # def country(self) -> str:
    #     """The name of the country or major administrative unit in which the dcterms:Location occurs.
    #     http://rs.tdwg.org/dwc/terms/country
    #     Recommended best practice is to use a controlled vocabulary such as the Getty Thesaurus of Geographic Names. Recommended best practice is to leave this field blank if the dcterms:Location spans multiple entities at this administrative level or if the dcterms:Location might be in one or another of multiple possible entities at this level. Multiplicity and uncertainty of the geographic entity can be captured either in the term dwc:higherGeography or in the term dwc:locality, or both.
    #     """
    #     return "Canada"
    # country.fget.short_description = "The name of the country or major administrative unit in which the dcterms:Location occurs."
    
    eventRemarks = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        verbose_name="Comments or notes about the dwc:Event.",
    )

    @property
    def timezone(self) -> str:
        if isinstance(self.andes_object, Cruise):
            return self.andes_object.display_tz
        else:
            try:
                return self._parentEvent.timezone
            except RecursionError:
                logging.getLogger(__name__).error("All child Events needs to stem from a Cruise")
                raise NoParentCruiseError


    def _init_from_cruise(self, cruise: Cruise):
        if not isinstance(cruise, Cruise):
            raise RuntimeError("_init_from_cruise needs a valid cruise")
        logging.getLogger(__name__).debug("Making Event from Cruise object")
        self.andes_object = cruise

        self.eventID = cruise.mission_number
        self._event_start_dt = cruise.start_date
        self._event_start_dt_p=3
        self._event_end_dt = cruise.end_date
        self._event_end_dt_p=3

        # use cruise bounding box
        self.decimalLatitude = 0.5 * (cruise.max_lat + cruise.min_lat)
        self.decimalLongitude = 0.5 * (cruise.max_lng + cruise.min_lng)
        # use half of great-circle distance (converted to metres)
        _coordinateUncertaintyInMeters = (
            1852
            * 0.5
            * calc_nautical_dist(
                {"lat": cruise.max_lat, "lng": cruise.max_lng},
                {"lat": cruise.min_lat, "lng": cruise.min_lng},
            )
        )
        self.coordinateUncertaintyInMeters = round(_coordinateUncertaintyInMeters, 3)
        self.fieldNumber = cruise.mission_number
        self.eventRemarks = cruise.notes

        # Hard-coded values
        self.eventType = "Project"  # https://registry.gbif-uat.org/vocabulary/EventType/concepts
        self.continent = "North America"
        self.language = "En"
        self.coordinatePrecision = None
        self.license = "http://creativecommons.org/licenses/by/4.0/legalcode"
        self.rightsHolder = "His Majesty the King in right of Canada, as represented by the Minister of Fisheries and Oceans"
        self.institutionID = "https://edmo.seadatanet.org/report/4160"
        self.institutionCode = "IML"
        self.datasetName = None
        self.countryCode = "CA"
        self.country = "Canada"

    def _init_from_fishing_set(self, my_set: Set):
        if not isinstance(my_set, Set):
            raise RuntimeError("_init_from_fishing_set needs a valid Set")
        logging.getLogger(__name__).debug("Making Event from Set object")

        if len(my_set.operations.filter(is_fishing=True)) == 0:
            logging.getLogger(__name__).warning("%s has no fishing operations", my_set)
            raise ValueError

        self.andes_object = my_set

        def make_set_wkt(my_set: Set):
            start_coord = (
                my_set.start_longitude,
                my_set.start_latitude,
                my_set.start_depth_m,
            )
            end_coord = (my_set.end_longitude, my_set.end_latitude, my_set.end_depth_m)
            ls = LineString((start_coord, end_coord))
            return ls.wkt

        self._event_start_dt = my_set.start_date
        self._event_end_dt = my_set.end_date

        # use set bounding box
        self.decimalLatitude = 0.5 * (my_set.start_latitude + my_set.end_latitude)
        self.decimalLongitude = 0.5 * (my_set.start_longitude + my_set.end_longitude)
        # use half of great-circle distance (converted to metres)
        _coordinateUncertaintyInMeters = (
            1852
            * 0.5
            * calc_nautical_dist(
                {"lat": my_set.start_latitude, "lng": my_set.start_longitude},
                {"lat": my_set.end_latitude, "lng": my_set.end_longitude},
            )
        )
        self.coordinateUncertaintyInMeters = round(_coordinateUncertaintyInMeters, 3)
        self.eventRemarks = my_set.remarks
        self.eventID = f"{self._parentEvent.eventID}-Set{my_set.set_number}"
        self.maximumDepthInMeters = my_set.max_depth_m if my_set.max_depth_m else None
        self.minimumDepthInMeters = my_set.min_depth_m if my_set.min_depth_m else None
        self.footprintWKT = make_set_wkt(my_set)
        self.fieldNumber = my_set.station.name

        # hard-coded values
        self.eventType = (
            "SiteVisit"  # https://registry.gbif-uat.org/vocabulary/EventType/concepts
        )

    def _init_from_mixed_catch(self, catch: Catch):
        """
        Makes a subsampling event (mixed catch)
        """
        if not isinstance(catch, Catch):
            raise RuntimeError("_init_from_mixed_catch needs a Catch")

        if not catch.species.is_mixed_catch:
            logging.getLogger(__name__).warning("%s needs to be a mixed catch", catch.id)
            raise InvalidSpecies

        self.andes_object = catch
        raise NotImplementedError


class Occurrence(OBISTable):
    andes_object = None

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

    @property
    def basisOfRecord(self) ->str:
        """	The specific nature of the data record.

        http://rs.tdwg.org/dwc/terms/basisOfRecord

    	Recommended best practice is to use a controlled vocabulary such as the set of local names of the identifiers for classes in Darwin Core.
   
        """
        return "HumanObservation"
    basisOfRecord.fget.short_description = "The specific nature of the data record."
    # basisOfRecord = models.CharField(
    #     max_length=63, verbose_name="The specific nature of the data record."
    # )

    @property
    def occurrenceStatus(self) ->str:
        """A statement about the presence or absence of a dwc:Taxon at a dcterms:Location.

        http://rs.tdwg.org/dwc/terms/occurrenceStatus

        For dwc:Occurrences, the default vocabulary is recommended to consist of present and absent, but can be extended by implementers with good justification. This term has an equivalent in the dwciri: namespace that allows only an IRI as a value, whereas this term allows for any string literal value.

        """
        return "present"
    occurrenceStatus.fget.short_description = "A statement about the presence or absence of a dwc:Taxon at a dcterms:Location."
    # occurrenceStatus = models.CharField(
    #     max_length=63,
    #     verbose_name="A statement about the presence or absence of a dwc:Taxon at a dcterms:Location",
    # )

    occurrenceRemarks = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None,
        verbose_name="Comments or notes about the dwc:Occurrence.",
        help_text="http://rs.tdwg.org/dwc/terms/occurrenceRemarks"
    )


    associatedMedia = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=255,
        verbose_name="A list (concatenated and separated) of identifiers (publication, global unique identifier, URI) of media associated with the dwc:Occurrence.",
    )

    @property
    def taxonRemarks(self) -> str|None:
        """Comments or notes about the taxon or name.

        http://rs.tdwg.org/dwc/terms/taxonRemarks

        """
        return None
    taxonRemarks.fget.short_description = "Comments or notes about the taxon or name."
    # taxonRemarks = models.CharField(
    #     max_length=255,
    #     verbose_name="Comments or notes about the taxon or name.",
    # )

    @property
    def identificationRemarks(self) ->str|None:
        """Comments or notes about the dwc:Identification.
    	http://rs.tdwg.org/dwc/terms/identificationRemarks

        """
        return None
    identificationRemarks.fget.short_description = "Comments or notes about the dwc:Identification."

# TODO
# scientificNameAuthorship
# kingdom
# phylum
# class
# order
# family
# genus
# specificEpithet
# taxonRank

    def _init_from_catch(self, catch: Catch):
        """
        Create an OBIS occurrence from a top level sampling event (a Set).
        Baskets having a parent baskets (poiting to a mixed catch) are ignored, they need to be populated using make_event_from_mixed_catch.
        Baskets that represent a subsample are ignored, they need a sub-sampling event.

        Args:
            catch (Catch): The Andes catch that supports the occurence
            catch_idx (int): an integrer representing the catch index in this event

        Raises:
            InvalidSpecies: If the catch species is mixed or does not have an aphiaID
            NoCatchData: If the catch is hollow (no actual data was inputed)

        """
        if not isinstance(catch, Catch):
            raise RuntimeError("_init_from_catch needs a Catch")

        if catch.species.is_mixed_catch:
            logging.getLogger(__name__).warning("%s is a mixed catch, skipped", catch.id)
            raise InvalidSpecies

        if catch.species.aphia_id is None:
            logging.getLogger(__name__).warning(
                "%s does not have an AphiaID, skipped", catch.id
            )
            raise InvalidSpecies

        if catch.has_parent_baskets:
            logging.getLogger(__name__).warning(
                "catch has parent baskets, perhaps a mixed catch?"
            )

        # meaningless catch:
        # has no baskets
        # AND has no weight
        # AND has no unmeasured specimen count
        # AND has no specimens
        # AND has no relative abundance category
        # AND has no catch images
        # has no children baskets (this case is treated separately)

        if (
            (not catch.has_child_baskets)
            and (catch.extrapolated_specimen_count is None)
            and (catch.relative_abundance_category is None)
            and (catch.total_basket_weight == 0)
            and (catch.unmeasured_specimen_count == 0)
            and (len(catch.specimens) == 0)
            and (len(catch.catch_images) == 0)
            and catch.baskets.filter(children__isnull=False)
        ):

            logging.getLogger(__name__).warning(
                "%s does not contain meaningfull data to export, delete it and try again.",
                catch,
            )
            raise NoCatchData("catch does not contain meaningfull data to export")

        logging.getLogger(__name__).debug("Making Occurrence from Catch object")

        self.andes_object = catch
        self.occurenceID = f"{self._event.eventID}_{self.andes_object.id}"
        self.verbatimIdentification = catch.species.scientific_name
        self.scientificName = catch.species.scientific_name
        self.scientificNameID = f"urn:lsid:marinespecies.org:taxname:{catch.species.aphia_id}"

        # hard-coded
        # self.basisOfRecord = "HumanObservation"
        # self.occurrenceStatus = "present"
        self.associatedMedia = None,
    


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
