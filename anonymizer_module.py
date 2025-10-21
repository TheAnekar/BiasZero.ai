"""
BiasZero Anonymizer
===================
A standalone Python module to anonymize resume JSON records for the BiasZero project.

Features
- Heuristic parsing of stringified fields (uses ast.literal_eval safely)
- Field-level anonymization (name, email, phone, age, gender, location)
- Organization and university tokenization (ORG_1, UNIV_1, ...)
- Technology tokenization (TECH_1, TECH_2, ...)
- Project/title/content sanitization (removes trailing ids like "#76", strips personal mentions)
- Options to preserve numeric features used by models while removing identifiers
- Optional reversible mode (stores mapping to disk; reversible mapping saved as JSON)

Usage
>>> from biaszero_anonymizer import Anonymizer
>>> an = Anonymizer(reversible=False, preserve_numeric_features=True)
>>> anonymized = an.anonymize_dataset([record1, record2], detected_fields=None)

Notes
- If you want the anonymizer to act only on fields that your bias detector flagged, pass the
  `detected_fields` argument (see docs inside the module). Otherwise it will anonymize a
  conservative default set of identifiers typically responsible for demographic leakage.
- Reversible mode writes a mapping file that must be protected (it contains re-identification
  information). Use only in secure, access-controlled settings.
"""

import ast
import hashlib
import json
import os
import re
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


def safe_parse(s: Any) -> Any:
    """Try to convert stringified Python dict/list to Python objects; otherwise return input."""
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
    """Main anonymizer class for resume records.

    Parameters
    ----------
    reversible : bool
        If True, saves a mapping file that allows reversing anonymized identifiers. Use with care.
    preserve_numeric_features : bool
        If True, preserves numeric features (grades, years_experience, num_jobs, raw_score, etc.)
        since ML models often need them. Identifiers will still be removed.
    mapping_path : Optional[str]
        If reversible=True, path where mapping will be stored.
    id_prefix : str
        Prefix for generated candidate IDs (e.g., CAND_).
    salt : str
        Optional salt used for deterministic hashing of textual fields.
    """

    DEFAULT_ID_PREFIX = "CAND_"

    def __init__(self, reversible: bool = False, preserve_numeric_features: bool = True,
                 mapping_path: Optional[str] = None, id_prefix: str = DEFAULT_ID_PREFIX, salt: str = ""):
        self.reversible = reversible
        self.preserve_numeric_features = preserve_numeric_features
        self.mapping_path = mapping_path or "anonymizer_mapping.json"
        self.id_prefix = id_prefix
        self.salt = salt

        # internal mapping stores (used when reversible=True); structure: {token_type: {original: token}}
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

        # counters for token numbering when deterministic mapping not used
        self._counters = {
            'ORG': 0,
            'UNIV': 0,
            'TECH': 0,
            'PROJ': 0
        }

    # ---------------------- Utility tokenizers ----------------------
    def _get_or_create_token(self, category: str, original: str, prefix: str) -> str:
        original_norm = str(original).strip()
        if not original_norm:
            return f"{prefix}_UNKNOWN"

        if self.reversible:
            if original_norm in self._mapping.get(category, {}):
                return self._mapping[category][original_norm]
            # deterministic token derived from hash to avoid leaking order information
            token = f"{prefix}_{_hash_text(original_norm, self.salt)[:12]}"
            self._mapping[category][original_norm] = token
            return token
        else:
            # non-reversible sequential token
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
        # mask local part partial
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
        # non-reversible candidate id using hash prefix
        return f"{self.id_prefix}{_hash_text(name, self.salt)[:8]}"

    def _anonymize_location(self, loc: str) -> str:
        loc = str(loc).strip()
        if not loc:
            return 'UNKNOWN'
        # collapse to general category: remote/onsite + hashed token for region
        cat = 'remote' if 'remote' in loc.lower() else 'onsite'
        if self.reversible:
            token = self._get_or_create_token('location', loc, 'LOC')
            return f"{cat.upper()}_{token}"
        return f"{cat.upper()}_{_hash_text(loc, self.salt)[:8]}"

    def _clean_project_title(self, title: str) -> str:
        title = str(title)
        # remove trailing #numbers or ids
        title = re.sub(r"#\d+", "", title).strip()
        if self.reversible:
            token = self._get_or_create_token('project_title', title, 'PROJ')
            return token
        # keep a short sanitized title limited to words
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
                # for non-reversible mode, create short tokens using hash
                tokens.append(f"TECH_{_hash_text(tclean, self.salt)[:6]}")
        return tokens

    # ---------------------- Anonymization routines ----------------------
    def anonymize_personal_info(self, personal_field: Any, fields_to_mask: Optional[List[str]] = None) -> Dict:
        personal = safe_parse(personal_field) if personal_field is not None else {}
        if not isinstance(personal, dict):
            # if it's a raw string with comma-separated parts, leave as empty dict
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
            # replace exact age with age bucket
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
            # map gender to 'undisclosed' to remove explicit gender signals
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
            # grades and years preserved by default unless preserve_numeric_features=False
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
            # Keep job_title but remove personal mentions
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
                # remove email addresses, phone numbers, or long unique ids from descriptions
                desc = str(p_new.get('description', ''))
                desc = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", "[email]", desc)
                desc = re.sub(r"\+?\d[\d\s\-()]{6,}", "[phone]", desc)
                # truncate to a sensible length
                p_new['description'] = (desc[:500] + '...') if len(desc) > 500 else desc
            if 'technologies' in p_new:
                techs = p_new.get('technologies', [])
                # technologies may be a pipe-separated string or list
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
        # we remove issuer names but preserve count
        out = deepcopy(certs)
        entries = out.get('entries', [])
        new_entries = []
        for c in entries:
            c_new = deepcopy(c)
            c_new.pop('issuer', None)
            c_new.pop('id', None)
            # preserve certificate name but remove long unique ids
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
        # tokenise technical skills
        out['technical'] = self._tokenize_technologies(techs if isinstance(techs, (list, tuple)) else [techs])
        # truncate and sanitize soft skills
        new_soft = []
        for s in (softs if isinstance(softs, (list, tuple)) else [softs]):
            s_clean = re.sub(r"\bI\b|\bme\b|\bmy\b", "[person]", str(s), flags=re.IGNORECASE)
            s_clean = (s_clean[:120] + '...') if len(s_clean) > 120 else s_clean
            new_soft.append(s_clean)
        out['soft'] = new_soft
        return out

    # ---------------------- High-level dataset anonymization ----------------------
    def anonymize_record(self, record: Dict, detected_fields: Optional[List[str]] = None) -> Dict:
        """Anonymize a single resume record.

        Parameters
        ----------
        record : Dict
            The original resume record (may contain stringified nested fields)
        detected_fields : Optional[List[str]]
            If provided, acts as a whitelist of ResumeField paths to anonymize. Example paths:
                ['personal_info.name', 'personal_info.location', 'experience.company']
            If None, a safe default set is anonymized (see code).
        """
        rec = deepcopy(record)
        # default fields we anonymize if no detected_fields provided
        default_fields = [
            'personal_info.name', 'personal_info.contact_email', 'personal_info.contact_phone',
            'personal_info.age', 'personal_info.gender', 'personal_info.location',
            'education.university', 'experience.company', 'projects.title', 'projects.description',
            'projects.technologies', 'skills.technical'
        ]

        detected_fields = detected_fields or default_fields

        # Personal info
        rec['personal_info'] = self.anonymize_personal_info(rec.get('personal_info'),
                                                            fields_to_mask=[f.split('.')[-1] for f in detected_fields if f.startswith('personal_info')])

        # Education
        rec['education'] = self.anonymize_education(rec.get('education'))

        # Experience
        rec['experience'] = self.anonymize_experience(rec.get('experience'))

        # Projects
        rec['projects'] = self.anonymize_projects(rec.get('projects'))

        # Certifications
        rec['certifications'] = self.anonymize_certifications(rec.get('certifications'))

        # Skills
        rec['skills'] = self.anonymize_skills(rec.get('skills'))

        # Optionally wipe or keep scoring fields
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
            # save mapping
            safe_dir = os.path.dirname(self.mapping_path)
            if safe_dir and not os.path.exists(safe_dir):
                os.makedirs(safe_dir, exist_ok=True)
            with open(self.mapping_path, 'w') as f:
                json.dump({'mapping': self._mapping}, f, indent=2)
        return out


# ---------------------- Example quick-run when executed directly ----------------------
if __name__ == '__main__':
    # quick demo using the user's example resume
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
