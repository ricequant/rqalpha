import abc
from itertools import chain
from typing import Iterable, Optional

from rqalpha.const import INSTRUMENT_TYPE
from rqalpha.model.instrument import Instrument

class AbstractInstrumentStore:
    def get_instruments(self, id_or_syms):
        # type: (Optional[Iterable[str]]) -> Iterable[Instrument]
        raise NotImplementedError


class InstrumentStore(AbstractInstrumentStore):
    def __init__(self, instruments, instrument_type):
        # type: (Iterable[Instrument], INSTRUMENT_TYPE) -> None
        self._instrument_type = instrument_type
        self._instruments = {}
        self._sym_id_map = {}

        for ins in instruments:
            if ins.type != instrument_type:
                continue
            self._instruments[ins.order_book_id] = ins
            self._sym_id_map[ins.symbol] = ins.order_book_id

    @property
    def instrument_type(self):
        # type: () -> INSTRUMENT_TYPE
        return self._instrument_type

    @property
    def all_id_and_syms(self):
        # type: () -> Iterable[str]
        return chain(self._instruments.keys(), self._sym_id_map.keys())

    def get_instruments(self, id_or_syms):
        # type: (Optional[Iterable[str]]) -> Iterable[Instrument]
        if id_or_syms is None:
            return self._instruments.values()
        order_book_ids = set()
        for i in id_or_syms:
            if i in self._instruments:
                order_book_ids.add(i)
            elif i in self._sym_id_map:
                order_book_ids.add(self._sym_id_map[i])
        return (self._instruments[i] for i in order_book_ids)
