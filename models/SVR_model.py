import torch
import torch.nn as nn
from torch.utils.data import Dataset
from torch.nn import functional as F
 
class SVRegressorV0(nn.Module):
    def __init__(self, input_dims, num_targets):
        super().__init__()
        self.total_size = sum(input_dims)
        
        # здесь просто линейная модель + RBF фичи
        self.linear = nn.Linear(self.total_size, 128)
        self.rbf_centers = nn.Parameter(torch.randn(10, 128) * 0.1)
        self.output_layer = nn.Linear(10, num_targets)
    
    def forward(self, *x_signals):
        # Объединяем + Линейное преобразование + RBF активации
        combined = torch.cat([x.reshape(x.shape[0], -1) for x in x_signals], dim=1)
        
        features = F.relu(self.linear(combined))
        
        distances = torch.cdist(features, self.rbf_centers)
        rbf_features = torch.exp(-0.1 * distances**2)
        
        return self.output_layer(rbf_features)