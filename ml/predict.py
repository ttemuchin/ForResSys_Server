import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
import math
import json
import sys, os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from sklearn.metrics import r2_score, mean_absolute_error

from models.Dataset import DynamicNMRDataset, DynamicNMRDatasetPredict
from models.ConvLayers_model import DynamicNMR_ConvRegressor
from models.LinearRegression_model import DynamicNMR_LinearRegression
from models.SVR_model import SVRegressorV0

from preproc.Preprocess import parse_data_file, parse_data_file_prod, splitSamples, extractXSamples

def get_weights_path(user_id: int, base_name: str, model_name: str) -> Path:
    """Путь к весам модели с учётом пользователя"""
    models_dir = Path(os.path.dirname(__file__)) / "saved_models" / str(user_id)
    weights_path = models_dir / f"{base_name}_{model_name}.pth"
    
    if not weights_path.exists():
        raise Exception(f"Weights file not found: {weights_path}")
    
    return weights_path


def create_model(model_name: str, input_dims: list, num_targets: int):
    if model_name.lower() == "svr":
        return SVRegressorV0(input_dims, num_targets)
    elif model_name.lower() == "convolutional":
        return DynamicNMR_ConvRegressor(input_dims, num_targets)
    elif model_name.lower() == "linear regression":
        return DynamicNMR_LinearRegression(input_dims, num_targets)
    else:
        raise Exception(f"Unknown model type: {model_name}")

# 2 РЕЖИМА save_predictions - test И prod
# в тесте ожидаем метрики в файле для предикта, а в прод - нет
def save_predictions_TEST(
    all_preds: np.ndarray,
    all_targets: np.ndarray,
    file_path: str,
    model_name: str,
    base_name: str,
    metrics: Dict[str, float],
    user_id: int,
    temp: bool = True
) -> str:
    """Сохраняет результаты предсказаний с метриками (test)"""
    # ВАЖНО! МЫ НЕ СОХРАНЯЕМ ПРЕДСКАЗАНИЯ БЕЗ ДЕЙСТВИЯ НА КЛИЕНТЕ
    # НО ЗДЕСЬ МЫ МОЖЕМ СИЛЬНО УПРОСТИТЬ ПРОЦЕСС СОХРАНЕНИЯ ПО ТРЕБОВАНИЮ
    # В МЕТОДЕ save_predictions СОХРАНЯТЬ РЕЗУЛЬТАТЫ В ВРЕМЕННЫЙ ФАЙЛ - server\static\predictions\{user_id}\TEMP.txt
    # а потом если пользователь захочет сохранить их нормально, то мы скопируем содержимое из TEMP.txt, создадим другой файл и сущность в БД
    # думаю отличный план
    
    output_dir = Path(os.path.dirname(__file__)).parent / "static" / "predictions" / str(user_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    input_filename = Path(file_path).stem
    if temp:
        output_filename = "TEMP.txt"
    else:
        output_filename = f"{input_filename}_{model_name}_{base_name}_out.txt"
    # output_filename = f"{input_filename}_{model_name}_{base_name}_out.txt"
    output_path = output_dir / output_filename
    # print(f"PROD output_dir: {output_dir}")
    # print(f"PROD output_path: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("PREDICTION RESULTS (with metrics)\n")
        f.write("================================\n")
        f.write(f"Input file: {file_path}\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Training base: {base_name}\n")
        f.write(f"MAE: {metrics.get('mae', 0):.6f}\n")
        f.write(f"R2 Score: {metrics.get('r2', 0):.6f}\n")
        f.write(f"Test Loss: {metrics.get('test_loss', 0):.6f}\n")
        f.write("\nPREDICTIONS:\n")
        
        col_width = 12
        num_targets = all_targets.shape[1] if all_targets.ndim > 1 else 1
        num_preds = all_preds.shape[1] if all_preds.ndim > 1 else 1
        
        headers = ["Sample"]
        headers.extend([f"Target_{i}" for i in range(num_targets)])
        headers.extend([f"Pred_{i}" for i in range(num_preds)])
        
        header_line = "".join([h.ljust(col_width) for h in headers])
        f.write(header_line + "\n")
        
        for i in range(len(all_preds)):
            row = [str(i+1)]
            if all_targets.ndim > 1:
                row.extend([f"{val:.6f}" for val in all_targets[i]])
            else:
                row.append(f"{all_targets[i]:.6f}")
            
            if all_preds.ndim > 1:
                row.extend([f"{val:.6f}" for val in all_preds[i]])
            else:
                row.append(f"{all_preds[i]:.6f}")
            
            formatted_row = [item.ljust(col_width) for item in row]
            f.write("".join(formatted_row) + "\n")
    
    return str(output_path)


def save_predictions_PROD(
    all_preds: np.ndarray,
    file_path: str,
    model_name: str,
    base_name: str,
    user_id: int,
    labelsY: Optional[list] = None,
    temp: bool = True
) -> str:
    """Сохраняет результаты предсказаний без метрик (prod)"""

    # Вариант когда все результаты сохраняются в temp/ до подтверждения пользователем
    # if temp:
    #     output_dir = Path(os.path.dirname(__file__)).parent.parent / "static" / "predictions" / str(user_id) / "temp"
    # else:
    #     output_dir = Path(os.path.dirname(__file__)).parent.parent / "static" / "predictions" / str(user_id)
    # но мы сделаем лучше так:

    # ОДИН РАЗ перент
    output_dir = Path(os.path.dirname(__file__)).parent / "static" / "predictions" / str(user_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    input_filename = Path(file_path).stem
    if temp:
        output_filename = "TEMP.txt"
    else:
        output_filename = f"{input_filename}_{model_name}_{base_name}_out.txt"
    # output_filename = f"{input_filename}_{model_name}_{base_name}_out.txt"
    output_path = output_dir / output_filename
    
    num_targets = all_preds.shape[1] if all_preds.ndim > 1 else 1
    num_samples = len(all_preds)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("ML Predicted Results\n")
        f.write("====================\n")
        f.write(f"Input file: {file_path}\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Training base: {base_name}\n\n")
        
        if labelsY and len(labelsY) == num_targets:
            f.write(" " * 8 + "".join([f"{label:>12}" for label in labelsY]) + "\n")
        else:
            f.write(" " * 8 + "".join([f"Pred_{i:>12}" for i in range(num_targets)]) + "\n")
        
        for i in range(num_samples):
            row = f"Sample {i+1:<3}"
            if all_preds.ndim > 1:
                row += "".join([f"{val:12.6f}" for val in all_preds[i]])
            else:
                row += f"{all_preds[i]:12.6f}"
            f.write(row + "\n")
    
    return str(output_path)


def safe_r2_score(y_true, y_pred):
    try:
        if (np.any(~np.isfinite(y_true)) or 
            np.any(~np.isfinite(y_pred)) or 
            len(y_true) < 2 or 
            np.var(y_true) == 0):
            return 0.0
        r2 = r2_score(y_true, y_pred)
        return r2 if np.isfinite(r2) else 0.0
    except:
        return 0.0


def predict(
    user_id: int,
    file_path: str,
    model_name: str,
    base_name: str,
    base_config: Dict[str, Any],
    mode: str = "test"  # "test" / "prod"
) -> Tuple[str, Optional[Dict[str, float]]]:
    """
    Основная функция предсказания
    
    Args:
        user_id: ID пользователя
        file_path: Путь к файлу с данными для предсказания
        model_name: Название модели
        base_name: Имя обучающей базы
        base_config: Конфигурация базы из БД
        mode: "test" - есть целевые переменные, считаем метрики
              "prod" - нет целевых переменных, только предсказания
    
    Returns:
        Tuple[output_path, metrics] - metrics = None для prod режима
    """
    weights_path = get_weights_path(user_id, base_name, model_name)

    num_features_x = base_config['nX']
    x_lengths = base_config['dimension']
    num_targets_y = base_config['nY']
    # !!!
    labelsY = base_config.get('labelsY', [f"Y{i}" for i in range(num_targets_y)])
    
    if mode == "test":
        parsed_data = parse_data_file(file_path)
        x_test, y_test = splitSamples(parsed_data)
        has_targets = True
        
    else:  # prod режим
        parsed_data = parse_data_file_prod(file_path)
        x_test = extractXSamples(parsed_data)
        y_test = None
        has_targets = False

# избыточная проверка но пусть будет
    if mode == "test" and not has_targets:
        raise Exception("Mode 'test' requires target variables in input file")
    if mode == "prod" and has_targets:
        print("Warning: Input file contains target variables, but running in 'prod' mode. Targets will be ignored.")
    
    # Проверки на соответствие размеров
    if len(x_test) != num_features_x:
        raise Exception(f"Feature count mismatch: config has {num_features_x}, data has {len(x_test)}")
    
    for i, length in enumerate(x_lengths):
        if len(x_test[i][0]) != length:
            raise Exception(f"Feature X[{i}] length mismatch: config has {length}, data has {len(x_test[i][0])}")
    
    # if len(y_test[0]) != num_targets_y:
    #     raise Exception(f"Target count mismatch: config has {num_targets_y}, data has {len(y_test[0])}")
    
    if mode == "test":
        test_dataset = DynamicNMRDataset(*x_test, y=y_test)
    else:
        test_dataset = DynamicNMRDatasetPredict(*x_test)
    
    batch_size = 32
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = create_model(model_name, x_lengths, num_targets_y)
    model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
    model.to(device)
    model.eval()

    criterion = nn.MSELoss()
    test_running_loss = 0.0
    all_preds = []
    all_targets = [] if has_targets else None

    with torch.no_grad():
        for batch in test_dataloader:
            if has_targets:
                *x_batch, y_batch = batch
                y_batch = y_batch.to(device)
            else:
                x_batch = batch
                y_batch = None
            x_batch = [x.to(device) for x in x_batch]
            outputs = model(*x_batch)
            
            if has_targets:
                loss = criterion(outputs, y_batch)
                test_running_loss += loss.item()
                all_targets.append(y_batch.cpu().numpy())
            
            all_preds.append(outputs.cpu().numpy())

    all_preds = np.concatenate(all_preds, axis=0)

    if mode == "test" and has_targets:
        all_targets = np.concatenate(all_targets, axis=0)
        test_loss = test_running_loss / len(test_dataloader)
        
        mae = mean_absolute_error(all_targets, all_preds)
        r2 = safe_r2_score(all_targets, all_preds)
        
        metrics = {
            'mae': float(mae) if math.isfinite(mae) else 0.0,
            'r2': float(r2) if math.isfinite(r2) else 0.0,
            'test_loss': float(test_loss) if math.isfinite(test_loss) else 0.0
        }
        
        output_path = save_predictions_TEST(
            all_preds, all_targets, file_path, model_name, base_name, metrics, user_id, temp=True
        )
        
        return output_path, metrics
    
    else:
        output_path = save_predictions_PROD(
            all_preds, file_path, model_name, base_name, user_id, labelsY, temp=True
        )
        
        return output_path, None
