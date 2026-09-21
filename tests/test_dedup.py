import tempfile
from pathlib import Path
from engine.dedup import HashStore, compute_hash


def test_compute_hash():
    h1 = compute_hash("Hello World")
    h2 = compute_hash("Hello World  \n")
    assert h1 == h2  # normalized whitespace
    assert len(h1) == 64


def test_hash_store_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "hashes.json"
        store = HashStore(file_path=store_path)

        # First check should be changed
        is_changed, h1, prev = store.is_changed("test_doc", "Initial content")
        assert is_changed is True
        assert prev is None

        # Update
        store.update("test_doc", "Initial content", "https://example.com")

        # Second check should be unchanged
        is_changed2, h2, prev2 = store.is_changed("test_doc", "Initial content")
        assert is_changed2 is False
        assert h2 == h1
        assert prev2 == h1

        # Check modified content
        is_changed3, h3, prev3 = store.is_changed("test_doc", "Updated content")
        assert is_changed3 is True
        assert h3 != h1
