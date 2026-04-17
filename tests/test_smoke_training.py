import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("torch")
from datssol.train.imitation import train_imitation


def test_smoke_train(tmp_path) -> None:
    p = tmp_path / "d.npz"
    np.savez(p, x=np.random.randn(8, 5).astype(np.float32), y=np.random.randint(0, 5, size=(8,), dtype=np.int64))
    out = tmp_path / "m.pt"
    metrics = train_imitation(str(p), str(out), epochs=1, batch_size=4)
    assert out.exists()
    assert "loss" in metrics
