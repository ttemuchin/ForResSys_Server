import torch
from torch.utils.data import Dataset

class DynamicNMRDataset(Dataset):
    def __init__(self, *x_signals, y):
        """
        :param x_signals: Списки сигналов (каждый размером [P, L_i], L_i может отличаться)
        :param y: Целевые переменные [P, N]
        """
        self.x_signals = [torch.FloatTensor(x) for x in x_signals]
        self.y = torch.FloatTensor(y)
        
    def __len__(self):
        return len(self.y)
    
    def __getitem__(self, idx):
        return tuple(x[idx] for x in self.x_signals) + (self.y[idx],)
    
class DynamicNMRDatasetPredict(Dataset):
    def __init__(self, *x_signals):
        """
        :param x_signals: Списки сигналов (каждый размером [P, L_i], L_i может отличаться)
        """
        self.x_signals = [torch.FloatTensor(x) for x in x_signals]
        
    def __len__(self):
        return len(self.x_signals[0])
    
    def __getitem__(self, idx):
        return tuple(x[idx] for x in self.x_signals)