import sys
from typing import Any, Set


class AIService:

    def __init__(self, model_name: str = "pt_core_news_sm") -> None:
        self.model_name = model_name
        self.nlp = self._load_model()

    def _load_model(self) -> Any:
        try:
            import spacy

            try:
                return spacy.load(self.model_name)
            except OSError:
                sys.stderr.write(
                    f"[!] Warning: spaCy model '{self.model_name}' not found.\n"
                    f"[!] Attempting to download '{self.model_name}' automatically...\n"
                )
                from spacy.cli import download

                download(self.model_name)
                return spacy.load(self.model_name)
        except ImportError:
            sys.stderr.write(
                "[!] Error: 'spacy' library is required when running with --use-ai.\n"
                "[!] Please install it via: pip install spacy\n"
            )
            sys.exit(1)
        except Exception as exc:
            sys.stderr.write(f"[!] Error initializing AI Engine: {exc}\n")
            sys.exit(1)

    def extract_unstructured_pii(self, text: str) -> Set[str]:
        doc = self.nlp(text)
        pii_entities = set()
        for ent in doc.ents:
            if ent.label_ in ("PER", "PERSON", "LOC", "GPE", "ORG"):
                pii_entities.add(ent.text)
        return pii_entities