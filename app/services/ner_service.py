import re
from typing import List, Dict
import spacy
from app.config import settings

class NERService:
    def __init__(self):
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
        except:
            print(f"⚠️ SpaCy model '{settings.SPACY_MODEL}' not found. Run: python -m spacy download {settings.SPACY_MODEL}")
            self.nlp = None
        
        # Common blood test parameters with reference ranges
        self.blood_params = {
            'hemoglobin': {'unit': 'g/dL', 'min': 12.0, 'max': 16.0, 'aliases': ['hb', 'haemoglobin']},
            'wbc': {'unit': 'cells/mcL', 'min': 4000, 'max': 10000, 'aliases': ['white blood cells', 'leukocytes']},
            'rbc': {'unit': 'million cells/mcL', 'min': 4.5, 'max': 5.5, 'aliases': ['red blood cells', 'erythrocytes']},
            'platelets': {'unit': 'cells/mcL', 'min': 150000, 'max': 400000, 'aliases': ['platelet count', 'thrombocytes']},
            'glucose': {'unit': 'mg/dL', 'min': 70, 'max': 100, 'aliases': ['blood sugar', 'fasting glucose']},
            'cholesterol': {'unit': 'mg/dL', 'min': 0, 'max': 200, 'aliases': ['total cholesterol']},
            'triglycerides': {'unit': 'mg/dL', 'min': 0, 'max': 150, 'aliases': []},
            'hdl': {'unit': 'mg/dL', 'min': 40, 'max': 200, 'aliases': ['hdl cholesterol', 'good cholesterol']},
            'ldl': {'unit': 'mg/dL', 'min': 0, 'max': 100, 'aliases': ['ldl cholesterol', 'bad cholesterol']},
            'creatinine': {'unit': 'mg/dL', 'min': 0.7, 'max': 1.3, 'aliases': []},
            'urea': {'unit': 'mg/dL', 'min': 7, 'max': 20, 'aliases': ['blood urea nitrogen', 'bun']},
            'alt': {'unit': 'U/L', 'min': 7, 'max': 56, 'aliases': ['sgpt', 'alanine aminotransferase']},
            'ast': {'unit': 'U/L', 'min': 10, 'max': 40, 'aliases': ['sgot', 'aspartate aminotransferase']},
            'tsh': {'unit': 'mIU/L', 'min': 0.4, 'max': 4.0, 'aliases': ['thyroid stimulating hormone']},
            't3': {'unit': 'ng/dL', 'min': 80, 'max': 200, 'aliases': ['triiodothyronine']},
            't4': {'unit': 'mcg/dL', 'min': 5.0, 'max': 12.0, 'aliases': ['thyroxine']},
        }
    
    def extract_metrics(self, text: str) -> List[Dict]:
        """Extract blood test metrics from text"""
        metrics = []
        text_lower = text.lower()
        
        # Pattern to match: parameter_name : value unit
        pattern = r'([a-zA-Z\s]+?)\s*[:\-]\s*(\d+\.?\d*)\s*([a-zA-Z/]+)?'
        matches = re.findall(pattern, text)
        
        for match in matches:
            param_name = match[0].strip().lower()
            value_str = match[1].strip()
            unit = match[2].strip() if len(match) > 2 and match[2] else None
            
            try:
                value = float(value_str)
            except ValueError:
                continue
            
            # Find matching parameter
            found_param = None
            for param_key, param_info in self.blood_params.items():
                if param_key in param_name or any(alias in param_name for alias in param_info['aliases']):
                    found_param = param_key
                    break
            
            if found_param:
                param_info = self.blood_params[found_param]
                
                # Determine status
                status = 'normal'
                if value < param_info['min']:
                    status = 'low'
                elif value > param_info['max']:
                    status = 'high'
                
                metrics.append({
                    'name': found_param.capitalize(),
                    'value': value,
                    'unit': unit or param_info['unit'],
                    'reference_min': param_info['min'],
                    'reference_max': param_info['max'],
                    'status': status
                })
        
        return metrics
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text and extract blood test information"""
        metrics = self.extract_metrics(text)
        
        # Determine overall status
        status = 'normal'
        if any(m['status'] in ['low', 'high'] for m in metrics):
            status = 'warning'
        if any(m['status'] == 'critical' for m in metrics):
            status = 'critical'
        
        return {
            'metrics': metrics,
            'status': status,
            'total_params': len(metrics)
        }