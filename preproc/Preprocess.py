import os
import random
from copy import deepcopy

def parse_directory(directory_path):
    all_samples = []

    if not os.path.isdir(directory_path):
        raise ValueError(f"Directory {directory_path} does not exist")

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)     
        if not os.path.isfile(file_path):
            continue   

        try:
            file_samples = parse_data_file(file_path)
            all_samples.extend(file_samples)
        except Exception as e:
            print(f"Error parsing file {filename}: {str(e)}")
            continue
    
    return all_samples

def parse_data_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    try:
        first_line = lines[1].strip()
        A = int(first_line.split('with ')[1].split(' records')[0])
    except:
        # print("test data")
        pass
    samples = []
    current_sample = None
    current_x_key = None
    collecting_x_data = False
    x_data_buffer = []

    for line in lines:
        line = line.strip()
        
        if "*******************new*record*******************" in line:
            if current_sample is not None:
                if current_x_key is not None and x_data_buffer:
                    current_sample[current_x_key] = x_data_buffer
                samples.append(current_sample)
            
            current_sample = {"Yi": []}
            current_x_key = None
            collecting_x_data = False
            x_data_buffer = []
            continue
        
        if line.startswith("nY="):
            nY = int(line.split('=')[1].strip())
            continue
        
        if line.startswith("Y"):
            parts = line.split('=')
            if len(parts) == 2:
                try:
                    y_value = float(parts[1].strip())
                    current_sample["Yi"].append(y_value)
                except ValueError:
                    pass
            continue
        
        if line.startswith("nX="):
            nX = int(line.split('=')[1].strip())
            for i in range(nX):
                current_sample[f"X[{i}]"] = []
            continue
        
        if "array of X[" in line and "with" in line:
            if current_x_key is not None and x_data_buffer:
                current_sample[current_x_key] = x_data_buffer
                x_data_buffer = []
            
            x_index = line.split('array of X[')[1].split(']')[0]
            current_x_key = f"X[{x_index}]"
            collecting_x_data = True
            continue
        
        if collecting_x_data:
            numbers = []
            for part in line.split():
                try:
                    num = float(part)
                    numbers.append(num)
                except ValueError:
                    pass
            x_data_buffer.extend(numbers)
    
    if current_sample is not None:
        if current_x_key is not None and x_data_buffer:
            current_sample[current_x_key] = x_data_buffer
        samples.append(current_sample)
    
    try:
        if len(samples) != A:
            print(f"Warning: Expected {A} samples, but found {len(samples)}")
            
        validate_data(samples)
    finally:
        return samples


def parse_data_file_prod(file_path):
    """
    Парсинг файла БЕЗ целевых переменных
    Возвращает список словарей, где каждый словарь содержит только X[i] ключи
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    samples = []
    current_sample = None
    current_x_key = None
    collecting_x_data = False
    x_data_buffer = []

    for line in lines:
        line = line.strip()
        
        if "*******************new*record*******************" in line:
            if current_sample is not None:
                if current_x_key is not None and x_data_buffer:
                    current_sample[current_x_key] = x_data_buffer
                samples.append(current_sample)
            
            current_sample = {}  # Нет ключа "Yi"
            current_x_key = None
            collecting_x_data = False
            x_data_buffer = []
            continue
        
        # Пропускаем строки с nY и Y, так как их нет в prod режиме
        if line.startswith("nY=") or line.startswith("Y"):
            continue
        
        if line.startswith("nX="):
            nX = int(line.split('=')[1].strip())
            for i in range(nX):
                current_sample[f"X[{i}]"] = []
            continue
        
        if "array of X[" in line and "with" in line:
            if current_x_key is not None and x_data_buffer:
                current_sample[current_x_key] = x_data_buffer
                x_data_buffer = []
            
            x_index = line.split('array of X[')[1].split(']')[0]
            current_x_key = f"X[{x_index}]"
            collecting_x_data = True
            continue
        
        if collecting_x_data:
            numbers = []
            for part in line.split():
                try:
                    num = float(part)
                    numbers.append(num)
                except ValueError:
                    pass
            x_data_buffer.extend(numbers)
    
    if current_sample is not None:
        if current_x_key is not None and x_data_buffer:
            current_sample[current_x_key] = x_data_buffer
        samples.append(current_sample)
    
    validate_data_prod(samples)
    return samples


def splitSamples(parsed_data_list):
    y_data = [sample["Yi"] for sample in parsed_data_list]
    x_data = []

    for i in range(len(parsed_data_list[0])-1):
        x_key = f"X[{i}]"
        x_data_i = [sample.get(x_key, []) for sample in parsed_data_list]
        x_data.append(x_data_i)

    assert all(len(x) == len(y_data) for x in x_data), "Несоответствие размеров данных"
    return x_data, y_data

def extractXSamples(parsed_data_list):
    # Извлечение только X данных (для prod режима без Y)
    # Возвращает x_data в том же формате, что и splitSamples
    x_data = []

    num_x_features = len([key for key in parsed_data_list[0].keys() if key.startswith("X[")])
    
    for i in range(num_x_features):
        x_key = f"X[{i}]"
        x_data_i = [sample.get(x_key, []) for sample in parsed_data_list]
        x_data.append(x_data_i)

    # Проверяем, что все образцы имеют одинаковое количество X данных
    for i, x_data_i in enumerate(x_data):
        assert len(x_data_i) == len(parsed_data_list), f"X[{i}] length mismatch"
    
    return x_data

def split_data(parsed_data, train_ratio=0.8, shuffle=True, random_seed=None):
    """
    Разделяет данные на обучающую и тестовую выборки
    
    :param parsed_data: Исходные данные (массив словарей)
    :param train_ratio: Доля обучающих данных (по умолчанию 0.8)
    :param shuffle: Флаг перемешивания данных перед разделением
    :param random_seed: Фиксирует случайность для воспроизводимости
    :return: train_data, test_data (оба в том же формате, что и parsed_data)
    """
    data_copy = deepcopy(parsed_data)
    
    if random_seed is not None:
        random.seed(random_seed)
    
    if shuffle:
        random.shuffle(data_copy)
    
    split_idx = int(len(data_copy) * train_ratio)
    
    train_data = data_copy[:split_idx]
    test_data = data_copy[split_idx:]
    
    return train_data, test_data

def validate_data(data):
    # Проверка данных на корректность(TEST)
    import numpy as np
    
    for sample in data:
        if 'Yi' in sample:
            for val in sample['Yi']:
                if not np.isfinite(val):
                    raise ValueError(f"Non-finite value found in Yi: {val}")
        
        for key in sample:
            if key.startswith("X["):
                for val in sample[key]:
                    if not np.isfinite(val):
                        raise ValueError(f"Non-finite value found in {key}: {val}")
                    
def validate_data_prod(data):
    # Проверка данных на корректность, без Y
    import numpy as np
    
    for sample in data:
        for key in sample:
            if key.startswith("X["):
                for val in sample[key]:
                    if not np.isfinite(val):
                        raise ValueError(f"Non-finite value found in {key}: {val}")