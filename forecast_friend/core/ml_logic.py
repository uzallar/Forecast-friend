import joblib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'ml_models')

class ForecastFriendModels:
    def __init__(self):
        self.topwear_model = joblib.load(os.path.join(MODELS_DIR, 'topwear_model.joblib'))
        self.topwear_encoder = joblib.load(os.path.join(MODELS_DIR, 'topwear_label_encoder.joblib'))

        self.bottom_model = joblib.load(os.path.join(MODELS_DIR, 'bottom_model.joblib'))
        self.bottom_encoder = joblib.load(os.path.join(MODELS_DIR, 'bottom_label_encoder.joblib'))

        self.footwear_model = joblib.load(os.path.join(MODELS_DIR, 'footwear_model.joblib'))
        self.footwear_encoder = joblib.load(os.path.join(MODELS_DIR, 'footwear_label_encoder.joblib'))

        self.accessories_model = joblib.load(os.path.join(MODELS_DIR, 'accessories_model.joblib'))
        self.accessories_encoder = joblib.load(os.path.join(MODELS_DIR, 'accessories_label_encoder.joblib'))

    def predict_topwear(self, features):
        pred = self.topwear_model.predict([features])
        return self.topwear_encoder.inverse_transform(pred)[0]

    def predict_bottom(self, features):
        pred = self.bottom_model.predict([features])
        return self.bottom_encoder.inverse_transform(pred)[0]

    def predict_footwear(self, features):
        pred = self.footwear_model.predict([features])
        return self.footwear_encoder.inverse_transform(pred)[0]

    def predict_accessories(self, features):
        pred = self.accessories_model.predict([features])
        return self.accessories_encoder.inverse_transform(pred)[0]
