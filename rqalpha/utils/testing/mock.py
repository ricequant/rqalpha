def mock_instrument(order_book_id="000001", _type="CS", exchange="XSHE", **kwargs):
    from rqalpha.model.instrument import Instrument

    ins_dict = {
        "order_book_id": order_book_id,
        "type": _type,
        "exchange": exchange,
    }
    ins_dict.update(kwargs)

    return Instrument(ins_dict)
