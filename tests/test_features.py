from helpcat.features import FeatureCache, FEATURE_CONFIG, windows, merge_predictions


def test_feature_cache_keeps_full_text_and_keys_configuration(tmp_path):
    cache = FeatureCache(tmp_path)
    text = "  --name NAME  " + "é" * 100
    a = cache.get(text)
    assert len(a["bytes"][0]) == 48
    assert a["bytes"][0] == [b + 1 for b in text.encode()[:48]]
    assert a["source_sha256"]
    assert cache.get(text) == a
    b = cache.get(text, dict(FEATURE_CONFIG, byte_width=24))
    assert len(b["bytes"][0]) == 24
    assert a["key"] != b["key"]
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_window_merge_prefers_most_context():
    assert windows(0) == []
    spans = windows(600)
    assert spans == [(0, 256), (224, 480), (448, 600)]
    results = [(start, [(str(start), 1.0)] * (end - start)) for start, end in spans]
    merged = merge_predictions(600, results)
    assert merged[224][0] == "0"
    assert merged[240][0] == "224"
    assert len(merged) == 600


def test_corrupt_cache_payload_is_rebuilt(tmp_path):
    import json

    cache = FeatureCache(tmp_path)
    expected = cache.get("Options:\n  -v  Details")
    path = next(tmp_path.glob("*.json"))
    corrupt = json.loads(path.read_text())
    corrupt["bytes"][0][0] = 256
    path.write_text(json.dumps(corrupt))
    assert cache.get("Options:\n  -v  Details") == expected
