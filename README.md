<<<<<<< HEAD
# BiasZero.ai

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
=======
# BiasZero.ai
>>>>>>> 9efd14f5c21c62e2ff9236c15e5bda0d58e5a367
