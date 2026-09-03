import joblib
import os
import json

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'priority_model.pkl')
SYMPTOMS_PATH = os.path.join(os.path.dirname(__file__), 'symptoms.json')

class TriageEngine:
    def __init__(self):
        self.model_data = None
        self.symptoms_map = {}
        self._load_resources()

    def _load_resources(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model_data = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Error loading ML model: {e}")
        
        if os.path.exists(SYMPTOMS_PATH):
            try:
                with open(SYMPTOMS_PATH, 'r') as f:
                    self.symptoms_map = json.load(f)
            except Exception as e:
                print(f"Error loading symptoms.json: {e}")

    def evaluate_triage(self, age, category, selected_symptoms, duration_days=1):
        """
        Evaluates patient input and returns:
        - priority (1-5)
        - urgency_level (RED, ORANGE, YELLOW, GREEN)
        - recommended_department
        - rationale
        - safety_disclaimer
        """
        age = int(age) if age else 30
        duration_days = int(duration_days) if duration_days else 1
        symptom_list = [s.strip() for s in selected_symptoms.split(',') if s.strip()] if isinstance(selected_symptoms, str) else selected_symptoms
        symptom_count = max(1, len(symptom_list))

        # Default fallback prediction using rule logic
        category_priority_map = {
            "Covid": 5, "Heart": 5, "Brain & Nerves": 5, "Cancer": 5, "General Surgery": 5,
            "Lungs & Breathing": 4, "Mental Wellness": 4, "Sexual Health": 4, "Child Specialist": 4, "Kidney Issues": 4,
            "Women Health": 3, "Bones and Joints": 3, "Digestive Issues": 3, "Diabetes Management": 3, "Urinary Issues": 3,
            "General Physician": 2, "Dental Care": 2, "Ear, Nose & Throat": 2, "Eye Specialist": 2, "Physiotherapy": 2, "Veterinary": 2,
            "Skin and Hair": 1, "Homeopathy": 1, "Ayurveda": 1, "Diet & Nutrition": 1
        }
        
        base_priority = category_priority_map.get(category, 2)
        
        # Check ML model if available
        predicted_priority = base_priority
        if self.model_data and 'model' in self.model_data and 'categories' in self.model_data:
            categories = self.model_data['categories']
            if category in categories:
                cat_code = categories.index(category)
                try:
                    predicted_priority = int(self.model_data['model'].predict([[age, cat_code, symptom_count, duration_days]])[0])
                except Exception:
                    predicted_priority = base_priority

        # Critical red flags override
        critical_keywords = ['chest pain', 'shortness of breath', 'seizure', 'unconscious', 'severe bleeding', 'heart attack', 'coughing blood']
        symptoms_str = ' '.join(symptom_list).lower()
        if any(kw in symptoms_str for kw in critical_keywords) or category in ['Heart', 'Brain & Nerves', 'Covid'] and symptom_count >= 3:
            predicted_priority = 5

        # Urgency Level Mapping
        if predicted_priority >= 5:
            urgency_level = 'RED'
        elif predicted_priority == 4:
            urgency_level = 'ORANGE'
        elif predicted_priority == 3:
            urgency_level = 'YELLOW'
        else:
            urgency_level = 'GREEN'

        recommended_dept = category if category else "General Physician"

        rationale = f"Priority {predicted_priority} recommendation assigned based on reported symptoms ({symptom_count}), category severity, patient age ({age}), and triage risk assessment."

        disclaimer = "IMPORTANT: This tool provides AI-assisted health guidance for triage categorization and does NOT replace professional medical evaluation or emergency services."

        return {
            'priority': predicted_priority,
            'urgency_level': urgency_level,
            'recommended_department': recommended_dept,
            'symptom_count': symptom_count,
            'rationale': rationale,
            'safety_disclaimer': disclaimer
        }

triage_engine = TriageEngine()
