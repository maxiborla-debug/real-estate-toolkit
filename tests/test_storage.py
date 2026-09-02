from realestate.storage import SeenStore


def test_new_store_has_nothing_seen(tmp_path):
    store = SeenStore.load(tmp_path / "seen.json")
    assert store.is_new("zonaprop:1")


def test_mark_seen_and_reload(tmp_path):
    path = tmp_path / "seen.json"
    store = SeenStore.load(path)
    store.mark_seen("zonaprop:1")
    store.save()

    reloaded = SeenStore.load(path)
    assert not reloaded.is_new("zonaprop:1")
    assert reloaded.is_new("zonaprop:2")
