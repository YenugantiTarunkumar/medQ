# train_model.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
import joblib

# Categories mapped to base severity
category_priority = {
    "Covid": 5, "Skin and Hair": 1, "Women Health": 3, "General Physician": 2,
    "Dental Care": 2, "Bones and Joints": 3, "Mental Wellness": 4, "Ear, Nose & Throat": 2,
    "Sexual Health": 4, "Child Specialist": 4, "Homeopathy": 1, "Digestive Issues": 3,
    "Eye Specialist": 2, "Heart": 5, "Physiotherapy": 2, "Brain & Nerves": 5,
    "Lungs & Breathing": 4, "Kidney Issues": 4, "General Surgery": 5, "Diabetes Management": 3,
    "Ayurveda": 1, "Cancer": 5, "Urinary Issues": 3, "Veterinary": 2, "Diet & Nutrition": 2
}

def generate_synthetic_triage_dataset():
    data = []
    categories = list(category_priority.keys())
    
    np.random.seed(42)
    for _ in range(2000):
        cat = np.random.choice(categories)
        base_prio = category_priority[cat]
        age = int(np.random.randint(1, 90))
        symptom_count = int(np.random.randint(1, 8))
        duration_days = int(np.random.randint(1, 30))
        
        # Calculate dynamic priority 1-5 based on risk factors
        prio = base_prio
        if age > 65 or age < 5:
            prio += 1
        if symptom_count >= 4:
            prio += 1
        if duration_days > 14 and prio < 4:
            prio += 1
            
        prio = max(1, min(5, prio))
        cat_code = categories.index(cat)
        
        data.append([age, cat_code, symptom_count, duration_days, prio])
        
    df = pd.DataFrame(data, columns=['age', 'category_code', 'symptom_count', 'duration_days', 'priority'])
    return df, categories

def train_priority_model():
    df, categories = generate_synthetic_triage_dataset()
    X = df[['age', 'category_code', 'symptom_count', 'duration_days']]
    y = df['priority']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = DecisionTreeClassifier(max_depth=6, random_state=42)
    clf.fit(X_train, y_train)
    
    accuracy = clf.score(X_test, y_test)
    print(f"Priority Model trained with Accuracy: {accuracy * 100:.2f}%")
    
    # Save model and categories metadata
    joblib.dump({'model': clf, 'categories': categories}, 'priority_model.pkl')
    print("Saved model package to 'priority_model.pkl'")

if __name__ == '__main__':
    train_priority_model()
