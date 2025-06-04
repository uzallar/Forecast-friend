from joblib import load

footwear_model = load('core/ml_models/footwear_model.joblib')
footwear_le = load('core/ml_models/footwear_label_encoder.joblib')

bottom_model = load('core/ml_models/bottom_model.joblib')
bottom_le = load('core/ml_models/bottom_label_encoder.joblib')

top_model = load('core/ml_models/topwear_model.joblib')
top_le = load('core/ml_models/topwear_label_encoder.joblib')

accessories_model = load('core/ml_models/accessories_model.joblib')
accessories_le = load('core/ml_models/accessories_label_encoder.joblib')

def encode_condition(le, condition):
    try:
        return le.transform([condition])[0]
    except Exception:
        default = 'Sunny' if 'Sunny' in le.classes_ else le.classes_[0]
        return le.transform([default])[0]

def calculate_uv_index(ET0, K, T_max, WS_max):
    try:
        uv_index = (ET0 * K) / (T_max * WS_max)
        return round(uv_index, 2)
    except (ZeroDivisionError, TypeError):
        return 1.0

def predict_footwear(temp, feels_like, wind, precip, humidity, condition):
    condition_encoded = encode_condition(footwear_le, condition)
    input_data = [[temp, feels_like, wind, precip, humidity, condition_encoded]]
    pred = footwear_model.predict(input_data)[0]
    categories = {
        0: "Сандалии/босоножки",
        1: "Кроссовки",
        2: "Водонепроницаемая обувь",
        3: "Зимняя обувь/сапоги"
    }
    return categories.get(pred, "Нет данных")

def predict_bottom(temp, feels_like, wind, precip, humidity, condition):
    condition_encoded = encode_condition(bottom_le, condition)
    input_data = [[temp, feels_like, wind, precip, humidity, condition_encoded]]
    pred = bottom_model.predict(input_data)[0]
    categories = {
        0: "Шорты/юбка",
        1: "Легкие брюки/джинсы",
        2: "Утепленные брюки",
        3: "Водостойкие/зимние штаны"
    }
    return categories.get(pred, "Нет данных")

def predict_top(temp, feels_like, wind, precip, humidity, condition):
    condition_encoded = encode_condition(top_le, condition)
    input_data = [[temp, feels_like, wind, precip, humidity, condition_encoded]]
    pred = top_model.predict(input_data)[0]
    categories = {
        0: "Футболка/майка",
        1: "Рубашка/тонкий свитер",
        2: "Свитер/худи",
        3: "Куртка/пальто"
    }
    return categories.get(pred, "Нет данных")

def predict_accessories(temp, feels_like, wind, precip, humidity, condition, uv):
    condition_encoded = encode_condition(accessories_le, condition)
    input_data = [[temp, feels_like, wind, precip, humidity, condition_encoded, uv]]
    pred = accessories_model.predict(input_data)[0]
    categories = {
        0: "Шарф/перчатки",
        1: "Солнцезащитные очки",
        2: "Зонтик",
        3: "Шляпа"
    }
    return categories.get(pred, "Нет данных")
