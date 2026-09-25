import hashlib

import httpx
import pytest

from omnisus.sources.medicamentos import fetch_stock_page


def test_page_number_identity_and_immutable_evidence():
    raw = b'{"parametros":[{"codigo_catmat":"BR0001","quantidade_estoque":3}]}'

    def serve(request):
        assert request.url.params["offset"] == "2"
        assert request.url.params["limit"] == "10"
        assert request.url.params["codigo_cnes"] == "0000001"
        return httpx.Response(200, content=raw)

    with httpx.Client(transport=httpx.MockTransport(serve)) as client:
        result = fetch_stock_page(
            filters={"codigo_cnes": "0000001"}, page=2, limit=10, client=client
        )
        assert not client.is_closed
    assert result.raw == raw
    assert result.sha256 == hashlib.sha256(raw).hexdigest()
    result.records[0]["codigo_catmat"] = "changed"
    assert result.records[0]["codigo_catmat"] == "BR0001"
    assert result.complete is False
    assert result.provenance()["publication_supported"] is False


@pytest.mark.parametrize("raw", [b'{"parametros":[]}', b'{"parametros":[{}]}'])
def test_empty_or_short_page_does_not_prove_completeness(raw):
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=raw))
    ) as client:
        assert fetch_stock_page(filters={"codigo_uf": "14"}, client=client).complete is False


@pytest.mark.parametrize(
    "raw", [b"{}", b"[]", b'{"parametros":[1]}', b"<html>error</html>", b'{"parametros":[{},{}]}']
)
def test_bad_envelope_and_oversized_page_fail(raw):
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, content=raw))
        ) as client,
        pytest.raises(ValueError),
    ):
        fetch_stock_page(filters={"codigo_uf": "14"}, limit=1, client=client)


def test_response_byte_limit():
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"parametros": []}))
        ) as client,
        pytest.raises(ValueError, match="max_bytes"),
    ):
        fetch_stock_page(filters={"codigo_uf": "14"}, max_bytes=1, client=client)


@pytest.mark.parametrize("status", [302, 401, 429, 500])
def test_http_failures_are_not_empty_data(status):
    with (
        httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(status))) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        fetch_stock_page(filters={"codigo_uf": "14"}, client=client)


def test_interrupted_stream_does_not_return_partial_observation():
    class Interrupted(httpx.SyncByteStream):
        def __iter__(self):
            yield b'{"parametros":['
            raise httpx.ReadError("connection lost")

    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=Interrupted()))
        ) as client,
        pytest.raises(httpx.ReadError, match="connection lost"),
    ):
        fetch_stock_page(filters={"codigo_uf": "14"}, client=client)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"filters": {}},
        {"filters": {"dispensacao": 1}},
        {"filters": {"codigo_uf": ""}},
        {"page": -1},
        {"page": True},
        {"limit": 0},
        {"limit": 1001},
        {"max_bytes": 0},
    ],
)
def test_invalid_plan_never_requests_network(kwargs):
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda r: pytest.fail("unexpected request"))
        ) as client,
        pytest.raises(ValueError),
    ):
        fetch_stock_page(**({"filters": {"codigo_uf": "14"}} | kwargs), client=client)
