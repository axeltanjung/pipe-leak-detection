import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class AnomalyResult:
    reconstruction_errors: np.ndarray
    anomaly_scores: np.ndarray
    anomaly_flags: np.ndarray
    threshold: float


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, latent_dim: int = 32, num_layers: int = 2):
        super().__init__()
        self.encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2,
        )
        self.encoder_fc = nn.Linear(hidden_dim, latent_dim)

        self.decoder_fc = nn.Linear(latent_dim, hidden_dim)
        self.decoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2,
        )
        self.output_layer = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        enc_out, (hidden, cell) = self.encoder(x)
        latent = self.encoder_fc(enc_out[:, -1, :])
        decoded = self.decoder_fc(latent)
        decoded = decoded.unsqueeze(1).repeat(1, x.size(1), 1)
        dec_out, _ = self.decoder(decoded)
        output = self.output_layer(dec_out)
        return output


class LSTMAnomalyDetector:
    def __init__(
        self,
        input_dim: int,
        sequence_length: int = 50,
        hidden_dim: int = 64,
        latent_dim: int = 32,
        num_layers: int = 2,
        threshold_percentile: float = 95.0,
        device: str = None,
    ):
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.threshold_percentile = threshold_percentile
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.model = LSTMAutoencoder(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            latent_dim=latent_dim,
            num_layers=num_layers,
        ).to(self.device)

        self.threshold = None
        self.scaler_mean = None
        self.scaler_std = None

    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        sequences = []
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data[i : i + self.sequence_length])
        return np.array(sequences)

    def _normalize(self, data: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.scaler_mean = np.nanmean(data, axis=0)
            self.scaler_std = np.nanstd(data, axis=0)
            self.scaler_std[self.scaler_std == 0] = 1.0
        return (data - self.scaler_mean) / self.scaler_std

    def train(
        self,
        data: np.ndarray,
        epochs: int = 50,
        batch_size: int = 64,
        learning_rate: float = 1e-3,
        validation_split: float = 0.1,
    ) -> dict:
        data_clean = np.nan_to_num(data, nan=0.0)
        normalized = self._normalize(data_clean, fit=True)
        sequences = self._create_sequences(normalized)

        split_idx = int(len(sequences) * (1 - validation_split))
        train_seq = sequences[:split_idx]
        val_seq = sequences[split_idx:]

        train_tensor = torch.FloatTensor(train_seq).to(self.device)
        val_tensor = torch.FloatTensor(val_seq).to(self.device)

        train_dataset = TensorDataset(train_tensor, train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

        history = {"train_loss": [], "val_loss": []}

        self.model.train()
        for epoch in range(epochs):
            train_losses = []
            for batch_x, batch_y in train_loader:
                optimizer.zero_grad()
                output = self.model(batch_x)
                loss = criterion(output, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                train_losses.append(loss.item())

            self.model.eval()
            with torch.no_grad():
                val_output = self.model(val_tensor)
                val_loss = criterion(val_output, val_tensor).item()

            avg_train_loss = np.mean(train_losses)
            history["train_loss"].append(avg_train_loss)
            history["val_loss"].append(val_loss)
            scheduler.step(val_loss)
            self.model.train()

        self.model.eval()
        with torch.no_grad():
            train_output = self.model(train_tensor)
            reconstruction_errors = torch.mean(
                (train_tensor - train_output) ** 2, dim=(1, 2)
            ).cpu().numpy()

        self.threshold = np.percentile(reconstruction_errors, self.threshold_percentile)
        history["threshold"] = self.threshold

        return history

    def detect(self, data: np.ndarray) -> AnomalyResult:
        data_clean = np.nan_to_num(data, nan=0.0)
        normalized = self._normalize(data_clean, fit=False)
        sequences = self._create_sequences(normalized)

        self.model.eval()
        seq_tensor = torch.FloatTensor(sequences).to(self.device)

        reconstruction_errors = []
        batch_size = 256
        with torch.no_grad():
            for i in range(0, len(seq_tensor), batch_size):
                batch = seq_tensor[i : i + batch_size]
                output = self.model(batch)
                errors = torch.mean((batch - output) ** 2, dim=(1, 2)).cpu().numpy()
                reconstruction_errors.extend(errors)

        reconstruction_errors = np.array(reconstruction_errors)

        full_errors = np.zeros(len(data))
        full_errors[: self.sequence_length - 1] = reconstruction_errors[0]
        full_errors[self.sequence_length - 1 :] = reconstruction_errors[: len(data) - self.sequence_length + 1]

        max_err = np.max(reconstruction_errors) if len(reconstruction_errors) > 0 else 1.0
        anomaly_scores = full_errors / (max_err + 1e-8)
        anomaly_flags = (full_errors > self.threshold).astype(int)

        return AnomalyResult(
            reconstruction_errors=full_errors,
            anomaly_scores=anomaly_scores,
            anomaly_flags=anomaly_flags,
            threshold=self.threshold,
        )

    def save(self, path: str):
        torch.save({
            "model_state": self.model.state_dict(),
            "threshold": self.threshold,
            "scaler_mean": self.scaler_mean,
            "scaler_std": self.scaler_std,
            "config": {
                "input_dim": self.input_dim,
                "sequence_length": self.sequence_length,
                "hidden_dim": self.hidden_dim,
                "latent_dim": self.latent_dim,
            },
        }, path)

    def load(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state"])
        self.threshold = checkpoint["threshold"]
        self.scaler_mean = checkpoint["scaler_mean"]
        self.scaler_std = checkpoint["scaler_std"]
        self.model.eval()
