import random

import pytest

torch = pytest.importorskip("torch")


def test_real_neural_handoff_preserves_full_evidence():
    from helpcat import ParserEngine, parse_help
    from helpcat.neural import LineModel, NeuralTagger

    model = LineModel()
    with torch.no_grad():
        model.head.weight.zero_()
        model.head.bias.fill_(-20)
        model.head.bias[2] = 20
    text = "Options:\n  --name NAME  " + "é" * 100
    cat = parse_help(text, command_path=("demo",), engine=ParserEngine(tagger=NeuralTagger(model)))
    assert cat["source"]["canonical_text"] == text
    assert cat["flags"][0]["description"]["value"] == "é" * 100
    assert cat["flags"][0]["arity"]["value"] == "required"


def test_checkpoint_restores_optimizer_rng_and_next_step(tmp_path):
    from helpcat.neural import LineModel, tensor_batch
    from helpcat.features import extract_features
    from helpcat.training import save_checkpoint, restore_checkpoint

    torch.set_num_threads(2)
    torch.manual_seed(17)
    random.seed(17)
    model = LineModel()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    inputs = tensor_batch([extract_features("Options:\n  -v  Details")])

    def step(m, opt):
        m.train()
        opt.zero_grad()
        logits = m(*inputs)
        loss = torch.nn.functional.cross_entropy(logits.reshape(-1, 10), torch.tensor([1, 2]))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step()

    step(model, optimizer)
    path = tmp_path / "checkpoint.pt"
    session = {"seed": 17, "step": 1, "elapsed_seconds": 1.0, "code_revision": "test"}
    save_checkpoint(path, model, optimizer, session)
    expected_random = random.random()
    step(model, optimizer)
    recovered = LineModel()
    resumed_optimizer = torch.optim.AdamW(recovered.parameters(), lr=1e-3)
    state = restore_checkpoint(path, recovered, resumed_optimizer, expected_revision="test")
    assert state["step"] == 1
    assert random.random() == expected_random
    step(recovered, resumed_optimizer)
    for expected, actual in zip(model.parameters(), recovered.parameters()):
        assert torch.equal(expected, actual)
    with pytest.raises(ValueError, match="revision"):
        restore_checkpoint(path, recovered, resumed_optimizer, expected_revision="changed")


def test_explicit_neural_engine_loads_checkpoint_and_policy(tmp_path):
    import json
    from helpcat.engines import load_engine
    from helpcat.neural import LineModel
    from helpcat.training import save_checkpoint

    model = LineModel(use_cnn=False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    path = tmp_path / "checkpoint.pt"
    save_checkpoint(
        path,
        model,
        optimizer,
        {"seed": 17, "step": 0, "elapsed_seconds": 0.0, "code_revision": "test"},
    )
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {"engine": "neural", "version": "smoke-1", "threshold": 0.0, "calibrated": False}
        )
    )
    engine = load_engine("neural", model=path, policy=policy)
    assert engine.tagger.name == "neural"
    assert len(engine.tagger.predict(["Options:", "  -v  Details"])) == 2
    assert not engine.calibrated
