
import pandas as pd
import numpy as np
import json
import ast
import pickle
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    accuracy_score,
    f1_score,
    precision_score,
    recall_score
)
import warnings
warnings.filterwarnings('ignore')


class BiasClassifier:
  
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.le_label = LabelEncoder()
        self.le_gender = LabelEncoder()
        self.le_location = LabelEncoder()
        self.feature_columns = None
        self.trained = False
        
    def parse_field(self, field_str):
       
        try:
            if isinstance(field_str, str):
                return ast.literal_eval(field_str)
            return field_str
        except:
            return {}
    
    def extract_features(self, data):
        
        features = []
        
        for record in data:
            feature_dict = {}
            
            
            personal = self.parse_field(record.get('personal_info', '{}'))
            feature_dict['age'] = personal.get('age', 30)
            feature_dict['gender'] = personal.get('gender', 'unknown')
            feature_dict['location'] = personal.get('location', 'unknown')
            
            
            education = self.parse_field(record.get('education', '{}'))
            feature_dict['has_education'] = int(education.get('has_education', False))
            edu_entries = education.get('entries', [])
            feature_dict['num_degrees'] = len(edu_entries)
            feature_dict['avg_grade'] = np.mean([e.get('grade', 0) for e in edu_entries]) if edu_entries else 0
            feature_dict['latest_edu_year'] = max([e.get('year', 2000) for e in edu_entries]) if edu_entries else 2000
            feature_dict['education_recency'] = 2025 - feature_dict['latest_edu_year']
            
           
            experience = self.parse_field(record.get('experience', '{}'))
            feature_dict['has_experience'] = int(experience.get('has_experience', False))
            exp_entries = experience.get('entries', [])
            feature_dict['num_jobs'] = len(exp_entries)
            feature_dict['years_experience'] = self._calculate_experience_years(exp_entries)
            
            
            projects = self.parse_field(record.get('projects', '{}'))
            feature_dict['has_projects'] = int(projects.get('has_projects', False))
            proj_entries = projects.get('entries', [])
            feature_dict['num_projects'] = len(proj_entries)
            feature_dict['num_technologies'] = sum([len(str(p.get('technologies', [])).split('|')) for p in proj_entries])
            feature_dict['avg_tech_per_project'] = (
                feature_dict['num_technologies'] / feature_dict['num_projects'] 
                if feature_dict['num_projects'] > 0 else 0
            )
            
            
            certifications = self.parse_field(record.get('certifications', '{}'))
            feature_dict['has_certifications'] = int(certifications.get('has_certifications', False))
            feature_dict['num_certifications'] = len(certifications.get('entries', []))
            
            
            skills = self.parse_field(record.get('skills', '{}'))
            feature_dict['has_skills'] = int(skills.get('has_skills', False))
            feature_dict['num_technical_skills'] = len(skills.get('technical', []))
            feature_dict['num_soft_skills'] = len(skills.get('soft', []))
            feature_dict['total_skills'] = feature_dict['num_technical_skills'] + feature_dict['num_soft_skills']
            
            
            feature_dict['experience_to_age_ratio'] = (
                feature_dict['years_experience'] / feature_dict['age'] 
                if feature_dict['age'] > 0 else 0
            )
            feature_dict['skills_to_experience_ratio'] = (
                feature_dict['total_skills'] / (feature_dict['years_experience'] + 1)
            )
            
            
            feature_dict['raw_score'] = record.get('raw_score', 0)
            feature_dict['bias_score'] = record.get('bias_score', 0)
            feature_dict['bias_label'] = record.get('bias_label', 'Medium')
            
            features.append(feature_dict)
        
        return pd.DataFrame(features)
    
    def _calculate_experience_years(self, exp_entries):
        
        total_months = 0
        for exp in exp_entries:
            try:
                start = exp.get('start_date', '01/2020')
                end = exp.get('end_date', '01/2020')
                start_m, start_y = map(int, start.split('/'))
                end_m, end_y = map(int, end.split('/'))
                months = (end_y - start_y) * 12 + (end_m - start_m)
                total_months += max(0, months)
            except:
                continue
        return total_months / 12.0
    
    def prepare_features(self, df, fit=False):
        
        df_copy = df.copy()
        
        
        if fit:
            df_copy['gender_encoded'] = self.le_gender.fit_transform(df_copy['gender'].fillna('unknown'))
        else:
            df_copy['gender_encoded'] = self.le_gender.transform(df_copy['gender'].fillna('unknown'))
        
        
        df_copy['location_type'] = df_copy['location'].apply(
            lambda x: 'remote' if 'remote' in str(x).lower() else 'onsite'
        )
        
        if fit:
            df_copy['location_encoded'] = self.le_location.fit_transform(df_copy['location_type'])
        else:
            df_copy['location_encoded'] = self.le_location.transform(df_copy['location_type'])
        
        
        df_copy['age_group'] = pd.cut(
            df_copy['age'], 
            bins=[0, 25, 35, 45, 100], 
            labels=[0, 1, 2, 3]
        )
        df_copy['age_group'] = df_copy['age_group'].fillna(1).astype(int)
        
        
        self.feature_columns = [
            'age', 'age_group', 'gender_encoded', 'location_encoded',
            'has_education', 'num_degrees', 'avg_grade', 'latest_edu_year', 'education_recency',
            'has_experience', 'num_jobs', 'years_experience',
            'has_projects', 'num_projects', 'num_technologies', 'avg_tech_per_project',
            'has_certifications', 'num_certifications',
            'has_skills', 'num_technical_skills', 'num_soft_skills', 'total_skills',
            'experience_to_age_ratio', 'skills_to_experience_ratio',
            'raw_score', 'bias_score'
        ]
        
        return df_copy[self.feature_columns].fillna(0)
    
    def train(self, data, optimize=True):
       
        print("\n" + "="*60)
        print("TRAINING BIAS CLASSIFIER MODEL (ML)")
        print("="*60)
        
        
        print("\n[1/4] Extracting features from resume data...")
        df = self.extract_features(data)
        print(f"✓ Processed {len(df)} resumes")
        
        
        print("\n[2/4] Preparing features for training...")
        X = self.prepare_features(df, fit=True)
        y = df['bias_label']
        
       
        y_encoded = self.le_label.fit_transform(y)
        label_mapping = dict(zip(self.le_label.classes_, range(len(self.le_label.classes_))))
        print(f"✓ Label mapping: {label_mapping}")
        
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        print(f"✓ Training set: {len(X_train)} samples")
        print(f"✓ Test set: {len(X_test)} samples")
        
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        
        print("\n[3/4] Training Gradient Boosting Classifier...")
        
        if optimize:
            print("   Performing hyperparameter optimization...")
            param_grid = {
                'n_estimators': [100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1],
                'min_samples_split': [2, 5],
                'min_samples_leaf': [1, 2]
            }
            
            base_model = GradientBoostingClassifier(random_state=42)
            grid_search = GridSearchCV(
                base_model, param_grid, cv=5, scoring='f1_weighted', n_jobs=-1, verbose=0
            )
            grid_search.fit(X_train_scaled, y_train)
            self.model = grid_search.best_estimator_
            print(f"   Best parameters: {grid_search.best_params_}")
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                min_samples_split=2,
                min_samples_leaf=1,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
        
        self.trained = True
        
        
        print("\n[4/4] Evaluating model performance...")
        y_pred = self.model.predict(X_test_scaled)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        print("\n" + "-"*60)
        print("MODEL PERFORMANCE METRICS")
        print("-"*60)
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1-Score:  {f1:.4f}")
        
        print("\n" + "-"*60)
        print("CLASSIFICATION REPORT")
        print("-"*60)
        print(classification_report(y_test, y_pred, target_names=self.le_label.classes_))
        
        print("\n" + "-"*60)
        print("CONFUSION MATRIX")
        print("-"*60)
        cm = confusion_matrix(y_test, y_pred)
        print(pd.DataFrame(cm, index=self.le_label.classes_, columns=self.le_label.classes_))
        
        print("\n" + "-"*60)
        print("FEATURE IMPORTANCE (Top 15)")
        print("-"*60)
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        print(feature_importance.head(15).to_string(index=False))
        
        print("\n" + "="*60)
        print("✓ BIAS CLASSIFIER MODEL TRAINING COMPLETE")
        print("="*60)
        
        return self
    
    def predict(self, data):
        
        if not self.trained:
            raise ValueError("Model not trained! Load a trained model or train first.")
        
        df = self.extract_features(data)
        X = self.prepare_features(df, fit=False)
        X_scaled = self.scaler.transform(X)
        
        y_pred_encoded = self.model.predict(X_scaled)
        y_pred_proba = self.model.predict_proba(X_scaled)
        
        y_pred = self.le_label.inverse_transform(y_pred_encoded)
        
        results = []
        for i, pred in enumerate(y_pred):
            results.append({
                'bias_label': pred,
                'confidence': float(y_pred_proba[i].max()),
                'probabilities': {
                    label: float(prob) 
                    for label, prob in zip(self.le_label.classes_, y_pred_proba[i])
                }
            })
        
        return results
    
    def save_model(self, filepath='bias_classifier_model.pkl'):
        
        if not self.trained:
            raise ValueError("Cannot save untrained model!")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'le_label': self.le_label,
            'le_gender': self.le_gender,
            'le_location': self.le_location,
            'feature_columns': self.feature_columns,
            'trained': self.trained
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"\n✓ Model saved to {filepath}")
    
    @classmethod
    def load_model(cls, filepath='bias_classifier_model.pkl'):
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        instance = cls()
        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.le_label = model_data['le_label']
        instance.le_gender = model_data['le_gender']
        instance.le_location = model_data['le_location']
        instance.feature_columns = model_data['feature_columns']
        instance.trained = model_data['trained']
        
        print(f"✓ Model loaded from {filepath}")
        return instance



if __name__ == "__main__":
    print("Loading training data from 'Biased Resume.json'...")
    with open('Biased Resumes.json', 'r') as f:
        training_data = json.load(f)
    
    print(f"Loaded {len(training_data)} resumes for training")
    
    classifier = BiasClassifier()
    classifier.train(training_data, optimize=True)
    classifier.save_model('bias_classifier_model.pkl')
    
    print("\n✓ Training complete! Model saved as 'bias_classifier_model.pkl'")
