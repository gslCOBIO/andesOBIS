import logging
from shapely.geometry import LineString

from andesOBIS.models import Event, Occurrence
from shared_models.models import Cruise, Set, Operation
from ecosystem_survey.models import Catch

# from andesOBIS.forms import EventForm

from shared_models.common_views import CommonCreateView
from shared_models.mixins import AndesLeadRequiredMixin

from shared_models.utils import calc_nautical_dist, get_active_cruise


class NoCatchData(Exception):
    pass


class InvalidSpecies(Exception):
    pass


# class EventCreateView(AndesLeadRequiredMixin, CommonCreateView):
#     model = Event
#     form_class = EventForm


def make_obis_events():
    cruise = get_active_cruise()
    parent = make_event_from_cruise(cruise)

    for set in Set.objects.filter(cruise=cruise):
        print(set)
        if len(set.operations.filter(is_fishing=True)) == 0:
            continue
        event = make_event_from_fishing_set(set, parent)

        for catch_idx, catch in enumerate(Catch.objects.filter(set=set)):
            # print(f"\t {catch}")

            if catch.species.is_mixed_catch:
                pass
                # mixed_catch_event = make_event_from_mixed_catch(set, event)
                # make_occurence_from_catch
            else:
                try:
                    occurence = make_occurence_from_catch(catch, catch_idx, event)
                except InvalidSpecies as exc:
                    pass


def make_event_from_cruise(cruise: Cruise) -> Event:
    if cruise is None:
        raise RuntimeError("Cannot get active cruise")
    _event_start_dt = cruise.start_date
    continent = "North America"
    # use cruise bounding box
    decimalLatitude = 0.5 * (cruise.max_lat + cruise.min_lat)
    decimalLongitude = 0.5 * (cruise.max_lng + cruise.min_lng)
    # use half of great-circle distance (converted to metres)
    coordinateUncertaintyInMeters = (
        1852
        * 0.5
        * calc_nautical_dist(
            {"lat": cruise.max_lat, "lng": cruise.max_lng},
            {"lat": cruise.min_lat, "lng": cruise.min_lng},
        )
    )
    coordinateUncertaintyInMeters = round(coordinateUncertaintyInMeters, 3)

    eventType = "Project"  # https://registry.gbif-uat.org/vocabulary/EventType/concepts
    eventRemarks = cruise.notes
    eventID = cruise.mission_number
    e = Event(
        eventID=eventID,
        _event_start_dt=_event_start_dt,
        _event_start_dt_p=3,
        decimalLatitude=decimalLatitude,
        decimalLongitude=decimalLongitude,
        coordinateUncertaintyInMeters=coordinateUncertaintyInMeters,
        continent=continent,
        eventType=eventType,
        eventRemarks=eventRemarks,
    )
    e.save()
    return e


def make_event_from_fishing_set(my_set: Set, parent: Event) -> Event:
    def make_set_wkt(my_set: Set):
        start_coord = (
            my_set.start_longitude,
            my_set.start_latitude,
            my_set.start_depth_m,
        )
        end_coord = (my_set.end_longitude, my_set.end_latitude, my_set.end_depth_m)
        ls = LineString((start_coord, end_coord))
        return ls.wkt

    if my_set is None:
        raise RuntimeError("Cannot get set")

    if len(my_set.operations.filter(is_fishing=True)) == 0:
        logging.getLogger(__name__).warning("%s has no fishing operations", my_set)
        raise ValueError

    _event_start_dt = my_set.start_date
    _event_end_dt = my_set.end_date

    # use set bounding box
    decimalLatitude = 0.5 * (my_set.start_latitude + my_set.end_latitude)
    decimalLongitude = 0.5 * (my_set.start_longitude + my_set.end_longitude)
    # use half of great-circle distance (converted to metres)
    coordinateUncertaintyInMeters = (
        1852
        * 0.5
        * calc_nautical_dist(
            {"lat": my_set.start_latitude, "lng": my_set.start_longitude},
            {"lat": my_set.end_latitude, "lng": my_set.end_longitude},
        )
    )
    coordinateUncertaintyInMeters = round(coordinateUncertaintyInMeters, 3)
    eventType = (
        "SiteVisit"  # https://registry.gbif-uat.org/vocabulary/EventType/concepts
    )
    eventRemarks = my_set.remarks
    eventID = f"{parent.eventID}-Set{my_set.set_number}"
    maximumDepthInMeters = my_set.max_depth_m if my_set.max_depth_m else None
    minimumDepthInMeters = my_set.min_depth_m if my_set.min_depth_m else None
    footprintWKT = make_set_wkt(my_set)
    fieldNumber = my_set.station.name

    e = Event(
        eventID=eventID,
        _parentEvent=parent,
        eventType=eventType,
        _event_start_dt=_event_start_dt,
        _event_end_dt=_event_end_dt,
        decimalLatitude=decimalLatitude,
        decimalLongitude=decimalLongitude,
        coordinateUncertaintyInMeters=coordinateUncertaintyInMeters,
        maximumDepthInMeters=maximumDepthInMeters,
        minimumDepthInMeters=minimumDepthInMeters,
        footprintWKT=footprintWKT,
        eventRemarks=eventRemarks,
        fieldNumber=fieldNumber,
    )
    e.save()
    return e


def make_event_from_mixed_catch(catch: Catch, parent: Event) -> Event:
    """
    Makes a subsampling event (mixed catch)
    This makes a follow-up call to make_occurence_from_mixed_catch() for all child baskets it contains
    """


def make_occurence_from_catch(catch: Catch, catch_idx: int, event: Event) -> Occurrence:
    """

    Create an OBIS occurrence from a top level sampling event (a Set).
    Baskets having a parent baskets (poiting to a mixed catch) are ignored, they need to be populated using make_event_from_mixed_catch.
    Baskets that represent a subsample are ignored, they need a sub-sampling event.

    Args:
        catch (Catch): The Andes catch that supports the occurence
        catch_idx (int): an integrer representing the catch index in this event
        event (Event): a top-level sampling event (i.e., Set). Sub-samples are ignored.

    Raises:
        InvalidSpecies: _description_
        NoCatchData: _description_

    Returns:
        Occurrence: _description_
    """

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

    occurenceID = f"{event.eventID}_{catch_idx:03}"
    verbatimIdentification = catch.species.scientific_name
    scientificName = catch.species.scientific_name
    scientificNameID = f"urn:lsid:marinespecies.org:taxname:{catch.species.aphia_id}"
    basisOfRecord = "HumanObservation"
    occurrenceStatus = "Present"
    occurrenceRemarks = catch.notes
    o = Occurrence(
        occurenceID=occurenceID,
        _event=event,
        verbatimIdentification=verbatimIdentification,
        scientificName=scientificName,
        scientificNameID=scientificNameID,
        basisOfRecord=basisOfRecord,
        occurrenceStatus=occurrenceStatus,
        associatedMedia=None,
        occurrenceRemarks=occurrenceRemarks,
    )
    o.save()
    return o
