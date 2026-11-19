"""CPU character-CNN plus two-layer bidirectional GRU line classifier."""

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from .core import LABELS
from .features import NUMERIC_WIDTH, FeatureCache, extract_features, merge_predictions, windows


class LineModel(nn.Module):
    def __init__(self, *, use_cnn=True):
        super().__init__()
        self.config = {
            "architecture": "charcnn-bigru-1",
            "use_cnn": use_cnn,
            "hidden_size": 128,
            "layers": 2,
            "byte_width": 48,
        }
        self.embedding = nn.Embedding(257, 16, padding_idx=0) if use_cnn else None
        self.convolutions = (
            nn.ModuleList([nn.Conv1d(16, 32, k, padding=k // 2) for k in (3, 5)])
            if use_cnn
            else None
        )
        self.gru = nn.GRU(
            NUMERIC_WIDTH + (64 if use_cnn else 0),
            128,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.1,
        )
        self.head = nn.Linear(256, len(LABELS))

    def forward(self, byte_ids, numeric, lengths):
        if self.embedding is not None:
            batch, lines, width = byte_ids.shape
            embedded = self.embedding(byte_ids.reshape(batch * lines, width)).transpose(1, 2)
            character = torch.cat(
                [torch.relu(conv(embedded)).amax(dim=-1) for conv in self.convolutions], dim=-1
            ).reshape(batch, lines, 64)
            inputs = torch.cat([character, numeric], dim=-1)
        else:
            inputs = numeric
        packed = pack_padded_sequence(inputs, lengths.cpu(), batch_first=True, enforce_sorted=False)
        output, _ = self.gru(packed)
        output, _ = pad_packed_sequence(output, batch_first=True, total_length=numeric.shape[1])
        return self.head(output)


def tensor_batch(pages):
    if not pages or any(not page["bytes"] for page in pages):
        raise ValueError("batch must contain nonempty page windows")
    lengths = torch.tensor([len(page["bytes"]) for page in pages], dtype=torch.long)
    width = len(pages[0]["bytes"][0])
    byte_ids = torch.zeros((len(pages), int(lengths.max()), width), dtype=torch.long)
    numeric = torch.zeros((len(pages), int(lengths.max()), NUMERIC_WIDTH), dtype=torch.float32)
    for i, page in enumerate(pages):
        byte_ids[i, : lengths[i]] = torch.tensor(page["bytes"], dtype=torch.long)
        numeric[i, : lengths[i]] = torch.tensor(page["numeric"], dtype=torch.float32)
    return byte_ids, numeric, lengths


class NeuralTagger:
    name = "neural"

    def __init__(self, model, *, cache=None, threads=2):
        if threads < 1:
            raise ValueError("CPU thread count must be positive")
        torch.set_num_threads(threads)
        self.model = model.cpu().eval()
        self.cache = FeatureCache(cache) if cache else None

    def predict(self, lines):
        text = "\n".join(lines)
        features = self.cache.get(text) if self.cache else extract_features(text)
        spans = windows(len(lines))
        predictions = []
        with torch.inference_mode():
            for offset in range(0, len(spans), 8):
                batch_spans = spans[offset : offset + 8]
                pages = [
                    {key: features[key][start:end] for key in ("bytes", "numeric")}
                    for start, end in batch_spans
                ]
                probabilities = self.model(*tensor_batch(pages)).softmax(dim=-1)
                scores, indices = probabilities.max(dim=-1)
                for row, (start, end) in enumerate(batch_spans):
                    predictions.append(
                        (
                            start,
                            [
                                (LABELS[int(indices[row, i])], float(scores[row, i]))
                                for i in range(end - start)
                            ],
                        )
                    )
        return merge_predictions(len(lines), predictions)
