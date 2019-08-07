 ## BOILERPLATE SETUP

 #from bluesky import RunEngine
 #from bluesky.plans import rel_grid_scan, count
 #from bluesky.plan_stubs import mv
 #from event_model import Filler
 #from ophyd import Device, EpicsSignal, Component
 #from ophyd.signal import EpicsSignalBase
 #from ophyd.areadetector.filestore_mixins import resource_factory
 #from databroker import Broker
 #from bluesky.preprocessors import SupplementalData
 #import bluesky.plan_stubs as bps
 #import bluesky.preprocessors
 #import time
 #import os
 #import uuid
 #from pathlib import Path
 #import numpy


 #def handler(resource_path, **kwargs):
 #    resource_path = resource_path

 #    def get():
 #        return numpy.load(resource_path)

 #    return get


 #class DarkFrameCache(Device):
 #    def __init__(self, *args, **kwargs):
 #        # self.det = det
 #        self.last_collected = None
 #        self.just_started = True
 #        self.update_done = False
 #        self._assets_collected = True
 #        return super().__init__(*args, **kwargs)

 #    def read(self):
 #        return self._read

 #    def read_configuration(self):
 #        return self._read_configuration

 #    @property
 #    def configuration_attrs(self):
 #        return self._configuration_attrs

 #    @property
 #    def read_attrs(self):
 #        return self._read_attrs

 #    def describe(self):
 #        return self._describe

 #    def describe_configuration(self):
 #        return self._describe_configuration

 #    # def describe_configuration(self):
 #    #     return self.det.describe_configuration

 #    def collect_asset_docs(self):
 #        if self._assets_collected:
 #            yield from []
 #        else:
 #            yield from self._asset_docs_cache

 #    def stage(self):
 #        self._assets_collected = False

 #def teleport(camera, dark_frame_cache):
 #    dark_frame_cache._describe = camera.describe()
 #    dark_frame_cache._describe_configuration = camera.describe_configuration()
 #    dark_frame_cache._read = camera.read()
 #    dark_frame_cache._read_configuration = camera.read_configuration()
 #    dark_frame_cache._read_attrs = list(camera.read())
 #    dark_frame_cache._configuration_attrs = list(camera.read_configuration())
 #    dark_frame_cache._asset_docs_cache = list(camera.collect_asset_docs())
 #    dark_frame_cache.last_collected = time.monotonic()


 #dark_frame_cache = DarkFrameCache(name='dark_frame_cache')


 #class InsertReferenceToDarkFrame:
 #    """
 #    A plan preprocessor that ensures one 'dark' Event per run.
 #    """
 #    def __init__(self, dark_frame_cache, stream_name='dark'):
 #        self.dark_frame_cache = dark_frame_cache
 #        self.stream_name = stream_name

 #    def __call__(self, plan):

 #        def insert_reference_to_dark_frame(msg):
 #            if msg.command == 'open_run':
 #                return (
 #                    bluesky.preprocessors.pchain(
 #                        bluesky.preprocessors.single_gen(msg),
 #                        bps.stage(self.dark_frame_cache),
 #                        bps.trigger_and_read([self.dark_frame_cache], name='dark'),
 #                        bps.unstage(self.dark_frame_cache)
 #                    ),
 #                    None,
 #                )
 #            else:
 #                return None, None

 #        return (yield from bluesky.preprocessors.plan_mutator(
 #            plan, insert_reference_to_dark_frame))


 #def dark_plan(detector, dark_frame_cache, max_age, shutter):
 #    if (dark_frame_cache.just_started or  # first run after instantiation
 #        (dark_frame_cache.last_collected is not None and
 #         time.monotonic() - dark_frame_cache.last_collected > max_age)):
 #        init_shutter_state = shutter.get()
 #        yield from bps.mv(shutter, 'Close')
 #        yield from bps.trigger(detector, group='cam')
 #        yield from bps.wait('cam')
 #        yield from bps.mv(shutter, init_shutter_state)


 #        teleport(detector, dark_frame_cache)
 #        dark_frame_cache.just_started = False
 #        dark_frame_cache.update_done = True
 #    else:
 #        dark_frame_cache.update_done = False


 #class TakeDarkFrames:
 #    def __init__(self, detector, dark_frame_cache, max_age, shutter):
 #        self.detector = detector
 #        self.dark_frame_cache = dark_frame_cache
 #        self.max_age = max_age
 #        self.shutter = shutter

 #    def __call__(self, plan):

 #        def insert_take_dark(msg):
 #            if msg.command == 'open_run':
 #                return (
 #                    bluesky.preprocessors.pchain(
 #                        dark_plan(
 #                            self.detector,
 #                            self.dark_frame_cache,
 #                            self.max_age,
 #                            self.shutter),
 #                        bluesky.preprocessors.single_gen(msg),
 #                    ),
 #                    None,
 #                )
 #            else:
 #                return None, None

 #        return (yield from bluesky.preprocessors.plan_mutator(plan, insert_take_dark))


 #take_dark_frames = TakeDarkFrames(pe1c, dark_frame_cache, 10, shutter_fs)
 #insert_reference_to_dark_frame = InsertReferenceToDarkFrame(dark_frame_cache)
 #RE.preprocessors.append(insert_reference_to_dark_frame)
 #RE.preprocessors.append(take_dark_frames)


 #import event_model
 #import suitcase.tiff_series


 #class DarkSubtraction(event_model.DocumentRouter):
 #    def __init__(self, *args, **kwargs):
 #        self.dark_descriptor = None
 #        self.primary_descriptor = None
 #        self.dark_frame = None
 #        super().__init__(*args, **kwargs)

 #    def descriptor(self, doc):
 #        if doc['name'] == 'dark':
 #            self.dark_descriptor = doc['uid']
 #        elif doc['name'] == 'primary':
 #            self.primary_descriptor = doc['uid']
 #        return super().descriptor(doc)

 #    def event_page(self, doc):
 #        event = self.event  # Avoid attribute lookup in hot loop.
 #        filled_events = []

 #        for event_doc in event_model.unpack_event_page(doc):
 #            filled_events.append(event(event_doc))
 #        new_event_page = event_model.pack_event_page(*filled_events)
 #        # Modify original doc in place, as we do with 'event'.
 #        doc['data'] = new_event_page['data']
 #        return doc

 #    def event(self, doc):
 #        FIELD = 'pe1_image'  # TODO Do not hard-code this.
 #        if doc['descriptor'] == self.dark_descriptor:
 #            self.dark_frame = doc['data']['pe1_image']
 #        if doc['descriptor'] == self.primary_descriptor:
 #            doc['data'][FIELD] = self.subtract(doc['data'][FIELD], self.dark_frame)
 #        return doc

 #    def subtract(self, light, dark):
 #        return numpy.clip(light - dark, a_min=0, a_max=None).astype(numpy.uint16)


 #def factory(name, start_doc):

 #    # Fill externally-stored data into Documents.
 #    filler = Filler(db.reg.handler_reg)
 #    filler(name, start_doc)  # modifies doc in place
 #    # Do dark subtraction "in place".
 #    dark_subtraction = DarkSubtraction()
 #    dark_subtraction(name, start_doc)

 #    def subfactory(name, descriptor_doc):
 #        if descriptor_doc['name'] == 'primary':
 #            serializer = suitcase.tiff_series.Serializer(
 #                    'exported/', file_prefix='{start[uid]:.8}-')
 #            serializer('start', start_doc)
 #            serializer('descriptor', descriptor_doc)
 #            return [serializer]
 #        else:
 #            return []

 #    # Uncomment this to export un-subtracted images as well.
 #    # raw_serializer = suitcase.tiff_series.Serializer('exported/',
 #    #         file_prefix='RAW-{start[name]}-{start[uid]:.8}-')
 #    # raw_serializer('start', start_doc)
 #    # return [filler, raw_serializer, dark_subtraction], [subfactory]

 #    return [filler, dark_subtraction], [subfactory]


 #from event_model import RunRouter
 #rr = RunRouter([factory])
 #RE.subscribe(rr)
