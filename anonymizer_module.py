

import ast
import hashlib
import json
import os
import re
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


def safe_parse(s: Any) -> Any:
   
    if isinstance(s, str):
        try:
            return ast.literal_eval(s)
        except Exception:
            return s
    return s


def _hash_text(text: str, salt: str = "") -> str:
    h = hashlib.sha256((salt + text).encode('utf-8')).hexdigest()
    return h


class Anonymizer:


    DEFAULT_ID_PREFIX = "CAND_"

    def __init__(self, reversible: bool = False, preserve_numeric_features: bool = True,
                 mapping_path: Optional[str] = None, id_prefix: str = DEFAULT_ID_PREFIX, salt: str = ""):
        self.reversible = reversible
        self.preserve_numeric_features = preserve_numeric_features
        self.mapping_path = mapping_path or "anonymizer_mapping.json"
        self.id_prefix = id_prefix
        self.salt = salt

        
        self._mapping = {
            'name': {},
            'email': {},
            'phone': {},
            'university': {},
            'company': {},
            'technology': {},
            'project_title': {},
            'location': {}
        }

     
        self._counters = {
            'ORG': 0,
            'UNIV': 0,
            'TECH': 0,
            'PROJ': 0
        }

  
    def _get_or_create_token(self, category: str, original: str, prefix: str) -> str:
        original_norm = str(original).strip()
        if not original_norm:
            return f"{prefix}_UNKNOWN"

        if self.reversible:
            if original_norm in self._mapping.get(category, {}):
                return self._mapping[category][original_norm]
            
            token = f"{prefix}_{_hash_text(original_norm, self.salt)[:12]}"
            self._mapping[category][original_norm] = token
            return token
        else:
            
            self._counters[prefix] = self._counters.get(prefix, 0) + 1
            return f"{prefix}_{self._counters[prefix]}"

    def _mask_email(self, email: str) -> str:
        email = str(email)
        if '@' not in email:
            return 'anon@example.com'
        local, domain = email.split('@', 1)
        if self.reversible:
            token = self._get_or_create_token('email', email, 'EMAIL')
            return f"{token}@example.com"
        
        return f"anon+{_hash_text(local, self.salt)[:8]}@{domain.split('.')[-1]}.example"

    def _mask_phone(self, phone: str) -> str:
        phone = str(phone)
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 4:
            masked = 'X' * (len(digits) - 4) + digits[-4:]
        else:
            masked = 'X' * max(3, len(digits))
        if self.reversible:
            token = self._get_or_create_token('phone', phone, 'PHONE')
            return f"{token}"
        return masked

    def _anonymize_name(self, name: str) -> str:
        name = str(name).strip()
        if not name:
            return ""
        if self.reversible:
            token = self._get_or_create_token('name', name, 'CAND')
            return token
        
        return f"{self.id_prefix}{_hash_text(name, self.salt)[:8]}"

    def _anonymize_location(self, loc: str) -> str:
        loc = str(loc).strip()
        if not loc:
            return 'UNKNOWN'
       
        cat = 'remote' if 'remote' in loc.lower() else 'onsite'
        if self.reversible:
            token = self._get_or_create_token('location', loc, 'LOC')
            return f"{cat.upper()}_{token}"
        return f"{cat.upper()}_{_hash_text(loc, self.salt)[:8]}"

    def _clean_project_title(self, title: str) -> str:
        title = str(title)
        
        title = re.sub(r"#\d+", "", title).strip()
        if self.reversible:
            token = self._get_or_create_token('project_title', title, 'PROJ')
            return token
        
        words = re.findall(r"[A-Za-z0-9]+", title)
        short = "_".join(words[:5])
        return f"PROJ_{_hash_text(short, self.salt)[:8]}"

    def _tokenize_technologies(self, techs: List[str]) -> List[str]:
        tokens = []
        for t in techs:
            tclean = str(t).strip().lower()
            if not tclean:
                continue
            if self.reversible:
                token = self._get_or_create_token('technology', tclean, 'TECH')
                tokens.append(token)
            else:
               
                tokens.append(f"TECH_{_hash_text(tclean, self.salt)[:6]}")
        return tokens

    
    def anonymize_personal_info(self, personal_field: Any, fields_to_mask: Optional[List[str]] = None) -> Dict:
        personal = safe_parse(personal_field) if personal_field is not None else {}
        if not isinstance(personal, dict):
            
            return {}

        fields_to_mask = fields_to_mask or ['name', 'contact_email', 'contact_phone', 'age', 'gender', 'location']

        out = deepcopy(personal)

        if 'name' in out and 'name' in fields_to_mask:
            out['name'] = self._anonymize_name(out.get('name', ''))

        if 'contact_email' in out and 'contact_email' in fields_to_mask:
            out['contact_email'] = self._mask_email(out.get('contact_email', ''))

        if 'contact_phone' in out and 'contact_phone' in fields_to_mask:
            out['contact_phone'] = self._mask_phone(out.get('contact_phone', ''))

        if 'age' in out and 'age' in fields_to_mask:
            
            try:
                age = int(out.get('age', 0))
                if age <= 25:
                    out['age'] = '18-25'
                elif age <= 35:
                    out['age'] = '26-35'
                elif age <= 45:
                    out['age'] = '36-45'
                else:
                    out['age'] = '46+'
            except Exception:
                out['age'] = 'UNKNOWN'

        if 'gender' in out and 'gender' in fields_to_mask:
            
            out['gender'] = 'undisclosed'

        if 'location' in out and 'location' in fields_to_mask:
            out['location'] = self._anonymize_location(out.get('location', ''))

        return out

    def anonymize_education(self, education_field: Any, fields_to_mask: Optional[List[str]] = None) -> Dict:
        education = safe_parse(education_field) if education_field is not None else {}
        if not isinstance(education, dict):
            return {}
        out = deepcopy(education)
        entries = out.get('entries', [])
        new_entries = []
        for e in entries:
            e_new = deepcopy(e)
            if 'university' in e_new:
                uni = e_new.get('university', '')
                e_new['university'] = self._get_or_create_token('university', uni, 'UNIV') if uni else 'UNIV_UNKNOWN'
            
            if not self.preserve_numeric_features:
                e_new.pop('grade', None)
                e_new.pop('year', None)
            new_entries.append(e_new)
        out['entries'] = new_entries
        return out

    def anonymize_experience(self, experience_field: Any) -> Dict:
        experience = safe_parse(experience_field) if experience_field is not None else {}
        if not isinstance(experience, dict):
            return {}
        out = deepcopy(experience)
        entries = out.get('entries', [])
        new_entries = []
        for e in entries:
            e_new = deepcopy(e)
            if 'company' in e_new:
                comp = e_new.get('company', '')
                e_new['company'] = self._get_or_create_token('company', comp, 'ORG') if comp else 'ORG_UNKNOWN'
           
            if 'job_title' in e_new:
                e_new['job_title'] = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|\d{5,}", "", str(e_new.get('job_title')))
            new_entries.append(e_new)
        out['entries'] = new_entries
        return out

    def anonymize_projects(self, projects_field: Any) -> Dict:
        projects = safe_parse(projects_field) if projects_field is not None else {}
        if not isinstance(projects, dict):
            return {}
        out = deepcopy(projects)
        entries = out.get('entries', [])
        new_entries = []
        for p in entries:
            p_new = deepcopy(p)
            if 'title' in p_new:
                p_new['title'] = self._clean_project_title(p_new.get('title', ''))
            if 'description' in p_new:
                
                desc = str(p_new.get('description', ''))
                desc = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", "[email]", desc)
                desc = re.sub(r"\+?\d[\d\s\-()]{6,}", "[phone]", desc)
                
                p_new['description'] = (desc[:500] + '...') if len(desc) > 500 else desc
            if 'technologies' in p_new:
                techs = p_new.get('technologies', [])
                
                if isinstance(techs, str):
                    techs_list = [t.strip() for t in techs.split('|') if t.strip()]
                elif isinstance(techs, (list, tuple)):
                    techs_list = techs
                else:
                    techs_list = []
                p_new['technologies'] = self._tokenize_technologies(techs_list)
            new_entries.append(p_new)
        out['entries'] = new_entries
        return out

    def anonymize_certifications(self, cert_field: Any) -> Dict:
        certs = safe_parse(cert_field) if cert_field is not None else {}
        if not isinstance(certs, dict):
            return {}
        
        out = deepcopy(certs)
        entries = out.get('entries', [])
        new_entries = []
        for c in entries:
            c_new = deepcopy(c)
            c_new.pop('issuer', None)
            c_new.pop('id', None)
           
            if 'name' in c_new:
                c_new['name'] = re.sub(r"#\d+|\d{6,}", "", str(c_new['name']))
            new_entries.append(c_new)
        out['entries'] = new_entries
        return out

    def anonymize_skills(self, skills_field: Any) -> Dict:
        skills = safe_parse(skills_field) if skills_field is not None else {}
        if not isinstance(skills, dict):
            return {}
        out = deepcopy(skills)
        techs = out.get('technical', [])
        softs = out.get('soft', [])
       
        out['technical'] = self._tokenize_technologies(techs if isinstance(techs, (list, tuple)) else [techs])
       
        new_soft = []
        for s in (softs if isinstance(softs, (list, tuple)) else [softs]):
            s_clean = re.sub(r"\bI\b|\bme\b|\bmy\b", "[person]", str(s), flags=re.IGNORECASE)
            s_clean = (s_clean[:120] + '...') if len(s_clean) > 120 else s_clean
            new_soft.append(s_clean)
        out['soft'] = new_soft
        return out

   
    def anonymize_record(self, record: Dict, detected_fields: Optional[List[str]] = None) -> Dict:
      
        rec = deepcopy(record)
        
        default_fields = [
            'personal_info.name', 'personal_info.contact_email', 'personal_info.contact_phone',
            'personal_info.age', 'personal_info.gender', 'personal_info.location',
            'education.university', 'experience.company', 'projects.title', 'projects.description',
            'projects.technologies', 'skills.technical'
        ]

        detected_fields = detected_fields or default_fields

        
        rec['personal_info'] = self.anonymize_personal_info(rec.get('personal_info'),
                                                            fields_to_mask=[f.split('.')[-1] for f in detected_fields if f.startswith('personal_info')])

        
        rec['education'] = self.anonymize_education(rec.get('education'))

       
        rec['experience'] = self.anonymize_experience(rec.get('experience'))

        
        rec['projects'] = self.anonymize_projects(rec.get('projects'))

        
        rec['certifications'] = self.anonymize_certifications(rec.get('certifications'))

        
        rec['skills'] = self.anonymize_skills(rec.get('skills'))

        
        if not self.preserve_numeric_features:
            rec.pop('raw_score', None)
            rec.pop('bias_score', None)
            rec.pop('bias_label', None)

        return rec

    def anonymize_dataset(self, data: List[Dict], detected_fields: Optional[List[str]] = None) -> List[Dict]:
        out = []
        for rec in data:
            out.append(self.anonymize_record(rec, detected_fields=detected_fields))
        if self.reversible:
            
            safe_dir = os.path.dirname(self.mapping_path)
            if safe_dir and not os.path.exists(safe_dir):
                os.makedirs(safe_dir, exist_ok=True)
            with open(self.mapping_path, 'w') as f:
                json.dump({'mapping': self._mapping}, f, indent=2)
        return out


if __name__ == '__main__':
    
    sample = {
      "_id": {"$oid": "68d9392f80b9ba8a7173a79f"},
      "personal_info": "{'name': 'barjraj', 'age': 28, 'gender': 'm', 'location': 'Remote', 'contact_email': 'barjraj@example.com', 'contact_phone': '+918489438044'}",
      "education": "{'has_education': True, 'entries': [{'degree': \"Bachelor's in Communication\", 'university': 'Wichita State University', 'year': 2012, 'grade': 6.84}]}",
      "experience": "{'has_experience': True, 'entries': [{'job_title': 'Engineer', 'company': 'Tata Systems', 'start_date': '08/2011', 'end_date': '03/2014'}]}",
      "projects": "{'has_projects': True, 'entries': [{'title': 'Real-time Chat Application #76', 'description': 'A project centered around efficiency, usability, and integration of emerging trends. It ensures a balance of complexity and simplicity for effective results. This project is designed to demonstrate practical use of data-driven methods in solving real-world problems. It focuses on user needs and provides scalable results.', 'technologies': ['React|Node.js|MongoDB']}, {'title': 'Personal Finance Dashboard #144', 'description': 'This system leverages AI and modern frameworks to provide intelligent decision-making in dynamic contexts. It is lightweight, robust, and adaptive. This project is designed to demonstrate practical use of data-driven methods in solving real-world problems. It focuses on user needs and provides scalable results.', 'technologies': ['TensorFlow|Keras|Python']}]}",
      "certifications": "{'has_certifications': False, 'entries': []}",
      "skills": "{'has_skills': True, 'technical': ['UNIX', 'python', 'R', 'data analytics', 'Capital management'], 'soft': ['ability to work efficiently without supervision', 'interest to learn']}",
      "raw_score": 3,
      "bias_score": 0.4109589041095891,
      "bias_label": "Medium"
    }

    anon = Anonymizer(reversible=False, preserve_numeric_features=True, salt='biaszero')
    result = anon.anonymize_dataset([sample])
    print(json.dumps(result[0], indent=2))
