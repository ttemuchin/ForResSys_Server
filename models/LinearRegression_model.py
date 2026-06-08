import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class DynamicNMR_LinearRegression(nn.Module):
    def __init__(self, input_dims: list, num_targets: int):
        """
        :param input_dims: Список длин сигналов (например, [1000, 2000])
        :param num_targets: Количество целевых переменных (N)
        """
        super().__init__()
        self.num_experiments = len(input_dims)
        self.num_targets = num_targets
        self.input_dims = input_dims
        
        # общая сумма размеров всех сигналов
        total_input_size = sum(input_dims)
        
        # Единственный линейный слой — это и есть классическая линейная регрессия
        # Веса размера [num_targets, total_input_size]
        # Смещение (bias) размера [num_targets]
        self.linear = nn.Linear(total_input_size, num_targets)
        
        self._initialize_weights()

    def _initialize_weights(self):
        # Стандартная инициализация для линейной регрессии
        for m in self.modules():
            if isinstance(m, nn.Linear):
                # Инициализация весов по умолчанию из PyTorch (Kaiming Uniform)
                nn.init.kaiming_uniform_(m.weight, a=math.sqrt(5))
                if m.bias is not None:
                    fan_in, _ = nn.init._calculate_fan_in_and_fan_out(m.weight)
                    bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
                    nn.init.uniform_(m.bias, -bound, bound)

    def forward(self, *x_signals):
        """
        :param x_signals: M сигналов размером [B, L_i], где L_i - длина i-го сигнала
        :return: Предсказания размером [B, num_targets]
        """
        if len(x_signals) != self.num_experiments:
            raise ValueError(f"Expected {self.num_experiments} signals, got {len(x_signals)}")
        
        batch_size = x_signals[0].shape[0]
        
        # все сигналы в один вектор
        signal_vectors = []
        for i, signal in enumerate(x_signals):
            if signal.shape[-1] != self.input_dims[i]:
                if signal.shape[-1] > self.input_dims[i]:
                    signal = signal[..., :self.input_dims[i]]
                else:
                    pad_size = self.input_dims[i] - signal.shape[-1]
                    signal = F.pad(signal, (0, pad_size), mode='constant', value=0)

            signal_vectors.append(signal)
        
        combined = torch.cat(signal_vectors, dim=1)

        return self.linear(combined) # [batch_size, num_targets]

    def get_feature_importance(self, *x_signals):
        """
        Возвращает веса линейной модели для каждого входного отсчёта.
        Для линейной регрессии важность признака прямо пропорциональна |веса|
        """
        # weights имеет размер [num_targets, total_input_size]
        # Усредняем по целевым переменным, если их несколько
        importance = torch.abs(self.linear.weight.data).mean(dim=0)  # [total_input_size]
        
        # Разбиваем важность по исходным сигналам
        importance_per_signal = []
        start_idx = 0
        for dim in self.input_dims:
            end_idx = start_idx + dim
            signal_importance = importance[start_idx:end_idx]
            importance_per_signal.append(signal_importance)
            start_idx = end_idx
        
        return importance_per_signal