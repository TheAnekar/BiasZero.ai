
import pandas as pd
import numpy as np
import json
import ast
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from fairlearn.metrics import (
    MetricFrame, 
    demographic_parity_difference, 
    equalized_odds_difference,
    demographic_parity_ratio,
    equalized_odds_ratio
)
from fairlearn.reductions import ExponentiatedGradient, DemographicParity
import warnings
warnings.filterwarnings('ignore')


class BiasDetectionModel:
    
    def __init__(self):
        self.model = None
        self.le_gender = LabelEncoder()
        self.le_location = LabelEncoder()
        self.le_age_group = LabelEncoder()
        self.feature_columns = None
        self.bias_thresholds = {
            'Low': 0.15,
            'Medium': 0.35,
            'High': 1.0
        }
        
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
            
            
            certifications = self.parse_field(record.get('certifications', '{}'))
            feature_dict['has_certifications'] = int(certifications.get('has_certifications', False))
            feature_dict['num_certifications'] = len(certifications.get('entries', []))
            
           
            skills = self.parse_field(record.get('skills', '{}'))
            feature_dict['has_skills'] = int(skills.get('has_skills', False))
            feature_dict['num_technical_skills'] = len(skills.get('technical', []))
            feature_dict['num_soft_skills'] = len(skills.get('soft', []))
            
            
            feature_dict['raw_score'] = record.get('raw_score', 0)
            feature_dict['bias_score'] = record.get('bias_score', 0)
            feature_dict['bias_label'] = record.get('bias_label', 'Unknown')
            
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
    
    def prepare_demographic_features(self, df):
        
        df_copy = df.copy()
        
        
        df_copy['gender'] = df_copy['gender'].fillna('unknown')
        df_copy['gender_encoded'] = self.le_gender.fit_transform(df_copy['gender'])
        
        
        df_copy['age_group'] = pd.cut(
            df_copy['age'], 
            bins=[0, 25, 35, 45, 100], 
            labels=['18-25', '26-35', '36-45', '46+']
        )
        df_copy['age_group'] = df_copy['age_group'].fillna('26-35')
        df_copy['age_group_encoded'] = self.le_age_group.fit_transform(df_copy['age_group'])
        
        
        df_copy['location_type'] = df_copy['location'].apply(
            lambda x: 'remote' if 'remote' in str(x).lower() else 'onsite'
        )
        df_copy['location_encoded'] = self.le_location.fit_transform(df_copy['location_type'])
        
        return df_copy
    
    def train(self, data):
       
        print("\n" + "="*60)
        print("TRAINING BIAS DETECTION MODEL (FAIRLEARN)")
        print("="*60)
        
        
        print("\n[1/3] Extracting features from resume data...")
        df = self.extract_features(data)
        print(f"✓ Processed {len(df)} resumes")
        
        
        print("\n[2/3] Preparing demographic features...")
        df = self.prepare_demographic_features(df)
        
        
        self.feature_columns = [
            'has_education', 'num_degrees', 'avg_grade', 'latest_edu_year',
            'has_experience', 'num_jobs', 'years_experience', 
            'has_projects', 'num_projects', 'num_technologies',
            'has_certifications', 'num_certifications',
            'has_skills', 'num_technical_skills', 'num_soft_skills'
        ]
        
        X = df[self.feature_columns].fillna(0)
        y = (df['raw_score'] >= df['raw_score'].median()).astype(int)  
      
        print("\n[3/3] Training fairness-aware model...")
        base_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        
        sensitive_features = df['gender_encoded']
        
        self.model = ExponentiatedGradient(
            base_model,
            constraints=DemographicParity(),
            eps=0.01
        )
        
        self.model.fit(X, y, sensitive_features=sensitive_features)
        
        
        y_pred = self.model.predict(X)
        
        print("\n" + "-"*60)
        print("FAIRNESS METRICS")
        print("-"*60)
      
        dpd_gender = demographic_parity_difference(y, y_pred, sensitive_features=df['gender_encoded'])
        eod_gender = equalized_odds_difference(y, y_pred, sensitive_features=df['gender_encoded'])
        dpr_gender = demographic_parity_ratio(y, y_pred, sensitive_features=df['gender_encoded'])
        
        print(f"\n📊 Gender Bias Metrics:")
        print(f"   Demographic Parity Difference: {dpd_gender:.4f}")
        print(f"   Equalized Odds Difference: {eod_gender:.4f}")
        print(f"   Demographic Parity Ratio: {dpr_gender:.4f}")
        
        
        dpd_age = demographic_parity_difference(y, y_pred, sensitive_features=df['age_group_encoded'])
        eod_age = equalized_odds_difference(y, y_pred, sensitive_features=df['age_group_encoded'])
        
        print(f"\n📊 Age Bias Metrics:")
        print(f"   Demographic Parity Difference: {dpd_age:.4f}")
        print(f"   Equalized Odds Difference: {eod_age:.4f}")
        
        
        dpd_loc = demographic_parity_difference(y, y_pred, sensitive_features=df['location_encoded'])
        eod_loc = equalized_odds_difference(y, y_pred, sensitive_features=df['location_encoded'])
        
        print(f"\n📊 Location Bias Metrics:")
        print(f"   Demographic Parity Difference: {dpd_loc:.4f}")
        print(f"   Equalized Odds Difference: {eod_loc:.4f}")
        
        
        overall_bias = np.mean([abs(dpd_gender), abs(eod_gender), abs(dpd_age), abs(eod_age), abs(dpd_loc), abs(eod_loc)])
        print(f"\n🎯 Overall Bias Score: {overall_bias:.4f}")
        
        if overall_bias < 0.15:
            print("   Status: ✓ Low Bias (Fair)")
        elif overall_bias < 0.35:
            print("   Status: ⚠ Medium Bias (Monitor)")
        else:
            print("   Status: ✗ High Bias (Action Required)")
        
        print("\n" + "="*60)
        print("✓ BIAS DETECTION MODEL TRAINING COMPLETE")
        print("="*60)
        
        return self
    
    def detect_bias(self, data):
       
       
        df = self.extract_features(data)
        df = self.prepare_demographic_features(df)
        
        X = df[self.feature_columns].fillna(0)
        y_pred = self.model.predict(X)
        
        bias_metrics = {
            'gender_dpd': demographic_parity_difference(
                y_pred, y_pred, sensitive_features=df['gender_encoded']
            ),
            'age_dpd': demographic_parity_difference(
                y_pred, y_pred, sensitive_features=df['age_group_encoded']
            ),
            'location_dpd': demographic_parity_difference(
                y_pred, y_pred, sensitive_features=df['location_encoded']
            )
        }
        
        overall_bias = np.mean([abs(v) for v in bias_metrics.values()])
        
        
        if overall_bias < self.bias_thresholds['Low']:
            bias_level = 'Low'
        elif overall_bias < self.bias_thresholds['Medium']:
            bias_level = 'Medium'
        else:
            bias_level = 'High'
        
        return {
            'predictions': y_pred.tolist(),
            'bias_metrics': bias_metrics,
            'overall_bias_score': overall_bias,
            'bias_level': bias_level
        }
    
    def save_model(self, filepath='bias_detection_model.pkl'):
        
        model_data = {
            'model': self.model,
            'le_gender': self.le_gender,
            'le_location': self.le_location,
            'le_age_group': self.le_age_group,
            'feature_columns': self.feature_columns,
            'bias_thresholds': self.bias_thresholds
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"\n✓ Model saved to {filepath}")
    
    @classmethod
    def load_model(cls, filepath='bias_detection_model.pkl'):
        """Load a trained model"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        instance = cls()
        instance.model = model_data['model']
        instance.le_gender = model_data['le_gender']
        instance.le_location = model_data['le_location']
        instance.le_age_group = model_data['le_age_group']
        instance.feature_columns = model_data['feature_columns']
        instance.bias_thresholds = model_data['bias_thresholds']
        
        print(f"✓ Model loaded from {filepath}")
        return instance



if __name__ == "__main__":
    
    print("Loading training data from 'Biased Resume.json'...")
    with open('Biased Resumes.json', 'r') as f:
        training_data = json.load(f)
    
    print(f"Loaded {len(training_data)} resumes for training")
    
    
    model = BiasDetectionModel()
    model.train(training_data)
    
    
    model.save_model('bias_detection_model.pkl')
    
    print("\n✓ Training complete! Model saved as 'bias_detection_model.pkl'")