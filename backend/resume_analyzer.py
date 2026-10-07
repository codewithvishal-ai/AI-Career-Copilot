import os
import re
from urllib.parse import urlparse


class ResumeAnalyzer:

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        self.supported_extensions = [
            ".pdf",
            ".docx",
            ".txt"
        ]

        # --------------------------------------------------------
        # SKILL DATABASE
        # --------------------------------------------------------

        self.skill_database = [
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "C",
            "C++",
            "C#",
            "SQL",

            "HTML",
            "CSS",

            "React",
            "React.js",
            "Node.js",
            "Express.js",

            "Flask",
            "Django",
            "FastAPI",

            "Git",
            "GitHub",
            "GitLab",
            "GitHub Actions",

            "Machine Learning",
            "Deep Learning",
            "Artificial Intelligence",
            "AI",

            "Data Science",
            "Data Analytics",
            "Data Analysis",

            "Pandas",
            "NumPy",
            "Matplotlib",
            "Seaborn",

            "TensorFlow",
            "PyTorch",
            "Scikit-learn",

            "OpenCV",

            "NLP",
            "Natural Language Processing",

            "Power BI",
            "Excel",

            "MongoDB",
            "MySQL",
            "PostgreSQL",
            "SQLite",

            "AWS",
            "Azure",
            "Google Cloud",

            "Docker",
            "Kubernetes",

            "REST API",
            "API",

            "Linux",

            "Figma",
            "Canva",

            "Jupyter",
            "Jupyter Notebook",

            "Streamlit",

            "Generative AI",
            "LLM",
            "Large Language Models",
            "Prompt Engineering",

            "Computer Vision"
        ]

        self.skill_database = list(
            dict.fromkeys(self.skill_database)
        )

        # --------------------------------------------------------
        # SECTION KEYWORDS
        # --------------------------------------------------------

        self.section_keywords = {

            "Summary": [
                "summary",
                "professional summary",
                "profile",
                "about me",
                "career profile"
            ],

            "Objective": [
                "objective",
                "career objective",
                "professional objective"
            ],

            "Education": [
                "education",
                "academic background",
                "academic qualifications",
                "qualifications",
                "educational background"
            ],

            "Experience": [
                "experience",
                "work experience",
                "professional experience",
                "employment history",
                "work history"
            ],

            "Internship": [
                "internship",
                "internships",
                "intern experience"
            ],

            "Projects": [
                "projects",
                "personal projects",
                "academic projects",
                "project experience"
            ],

            "Skills": [
                "skills",
                "technical skills",
                "key skills",
                "core skills",
                "technologies",
                "technical expertise"
            ],

            "Certifications": [
                "certifications",
                "certificates",
                "certification",
                "credentials"
            ],

            "Achievements": [
                "achievements",
                "awards",
                "honors",
                "accomplishments"
            ],

            "Languages": [
                "languages",
                "language proficiency"
            ],

            "Interests": [
                "interests",
                "hobbies",
                "activities"
            ]
        }

        # --------------------------------------------------------
        # ACTION VERBS
        # --------------------------------------------------------

        self.strong_action_verbs = [
            "built",
            "developed",
            "designed",
            "implemented",
            "created",
            "engineered",
            "architected",
            "automated",
            "optimized",
            "analyzed",
            "deployed",
            "integrated",
            "led",
            "managed",
            "delivered",
            "launched",
            "improved",
            "increased",
            "reduced",
            "streamlined",
            "transformed",
            "programmed",
            "configured",
            "tested",
            "debugged",
            "migrated",
            "trained",
            "evaluated",
            "researched",
            "maintained",
            "coordinated",
            "solved",
            "executed"
        ]

        # --------------------------------------------------------
        # WEAK ACTION VERBS
        # --------------------------------------------------------

        self.weak_action_verbs = [
            "worked",
            "helped",
            "did",
            "made",
            "used",
            "responsible",
            "handled",
            "participated",
            "involved",
            "assisted",
            "supported",
            "learned",
            "tried",
            "was",
            "were"
        ]

        # --------------------------------------------------------
        # GENERIC PHRASES
        # --------------------------------------------------------

        self.generic_phrases = [
            "hardworking",
            "hard working",
            "team player",
            "quick learner",
            "self motivated",
            "self-motivated",
            "good communication skills",
            "excellent communication skills",
            "passionate",
            "dedicated",
            "responsible",
            "detail oriented",
            "detail-oriented",
            "results oriented",
            "results-oriented",
            "motivated individual",
            "dynamic individual",
            "positive attitude",
            "can work under pressure",
            "works well in a team",
            "seeking a challenging position",
            "looking for an opportunity",
            "to obtain a challenging position",
            "proven track record"
        ]

        self.recommended_sections = [
            "Summary",
            "Education",
            "Skills",
            "Projects",
            "Experience",
            "Internship",
            "Certifications",
            "Achievements"
        ]

        self.core_sections = [
            "Education",
            "Skills",
            "Projects",
            "Experience"
        ]

        # --------------------------------------------------------
        # ROLE KEYWORDS
        # --------------------------------------------------------

        self.role_keywords = {

            "AI / ML": [
                "Python",
                "Machine Learning",
                "Artificial Intelligence",
                "AI",
                "Deep Learning",
                "Pandas",
                "NumPy",
                "Scikit-learn",
                "TensorFlow",
                "PyTorch",
                "NLP",
                "Computer Vision",
                "LLM",
                "Generative AI"
            ],

            "Python Developer": [
                "Python",
                "Flask",
                "Django",
                "FastAPI",
                "REST API",
                "SQL",
                "Git",
                "GitHub",
                "API",
                "Docker"
            ],

            "Data Science": [
                "Python",
                "Pandas",
                "NumPy",
                "Matplotlib",
                "Seaborn",
                "Machine Learning",
                "Data Analysis",
                "Data Science",
                "SQL",
                "Scikit-learn"
            ],

            "Web Development": [
                "HTML",
                "CSS",
                "JavaScript",
                "React",
                "Node.js",
                "Express.js",
                "SQL",
                "Git",
                "GitHub",
                "REST API"
            ]
        }

    # ============================================================
    # BASIC UTILITIES
    # ============================================================

    def _safe_text(self, value):
        if value is None:
            return ""
        return str(value)

    def _clean_url(self, url):
        if not url:
            return ""

        url = self._safe_text(url).strip()

        # Remove whitespace accidentally introduced by PDF extraction
        url = re.sub(r"\s+", "", url)

        # Remove common surrounding punctuation
        url = url.strip("<>[]{}()\"'")

        url = url.rstrip(
            ".,;:!?)]}>\"'"
        )

        return url

    def _normalize_url(self, url):

        url = self._clean_url(url).lower()

        if not url:
            return ""

        if url.startswith("www."):
            url = "https://" + url

        elif not re.match(
            r"^[a-z][a-z0-9+\-.]*://",
            url,
            re.IGNORECASE
        ):
            if re.match(
                r"^(linkedin\.com|github\.com|gitlab\.com|"
                r"x\.com|twitter\.com|behance\.net|"
                r"dribbble\.com)(/|$)",
                url,
                re.IGNORECASE
            ):
                url = "https://" + url

        # Remove fragment
        try:
            parsed = urlparse(url)

            if parsed.scheme and parsed.netloc:
                url = (
                    parsed.scheme.lower()
                    + "://"
                    + parsed.netloc.lower()
                    + parsed.path.rstrip("/")
                )

                if parsed.query:
                    url += "?" + parsed.query

        except Exception:
            pass

        return url.rstrip("/")

    def _same_url(self, url1, url2):

        return (
            self._normalize_url(url1)
            == self._normalize_url(url2)
        )

    # ============================================================
    # EXTRACT TEXT
    # ============================================================

    def extract_text(self, file_path):

        if not file_path:
            raise ValueError(
                "No resume file path provided."
            )

        if not os.path.exists(file_path):
            raise FileNotFoundError(
                "Resume file not found."
            )

        extension = os.path.splitext(
            file_path
        )[1].lower()

        if extension not in self.supported_extensions:
            raise ValueError(
                "Unsupported resume format. "
                "Use PDF, DOCX or TXT."
            )

        if extension == ".pdf":
            return self._extract_pdf_text(file_path)

        if extension == ".docx":
            return self._extract_docx_text(file_path)

        return self._extract_txt_text(file_path)

    # ============================================================
    # TXT EXTRACTION
    # ============================================================

    def _extract_txt_text(self, file_path):

        encodings = [
            "utf-8",
            "utf-8-sig",
            "utf-16",
            "cp1252",
            "latin-1"
        ]

        last_error = None

        for encoding in encodings:

            try:

                with open(
                    file_path,
                    "r",
                    encoding=encoding
                ) as file:

                    return file.read()

            except UnicodeDecodeError as error:

                last_error = error
                continue

        raise Exception(
            f"TXT extraction failed: {last_error}"
        )

    # ============================================================
    # PDF TEXT EXTRACTION
    # ============================================================

    def _extract_pdf_text(self, file_path):

        try:

            try:
                from pypdf import PdfReader
            except ImportError:

                import PyPDF2
                PdfReader = PyPDF2.PdfReader

            text_parts = []

            with open(
                file_path,
                "rb"
            ) as file:

                reader = PdfReader(file)

                if reader.is_encrypted:

                    try:
                        reader.decrypt("")
                    except Exception:
                        pass

                for page in reader.pages:

                    try:

                        page_text = (
                            page.extract_text()
                            or ""
                        )

                        if page_text.strip():
                            text_parts.append(page_text)

                    except Exception:
                        continue

            return "\n".join(text_parts)

        except ImportError:

            raise ImportError(
                "pypdf/PyPDF2 is not installed. "
                "Run: pip install pypdf"
            )

        except Exception as error:

            raise Exception(
                f"PDF extraction failed: {error}"
            )

    # ============================================================
    # PDF EMBEDDED LINKS
    # ============================================================

    def _extract_pdf_links(self, file_path):

        links = []

        try:

            try:
                from pypdf import PdfReader
            except ImportError:

                import PyPDF2
                PdfReader = PyPDF2.PdfReader

            with open(
                file_path,
                "rb"
            ) as file:

                reader = PdfReader(file)

                for page_number, page in enumerate(
                    reader.pages,
                    start=1
                ):

                    try:

                        annotations = page.get(
                            "/Annots"
                        )

                        if not annotations:
                            continue

                        for annotation_ref in annotations:

                            try:

                                annotation = (
                                    annotation_ref.get_object()
                                )

                                if not annotation:
                                    continue

                                subtype = annotation.get(
                                    "/Subtype"
                                )

                                if str(subtype) != "/Link":
                                    continue

                                action = annotation.get(
                                    "/A"
                                )

                                if action:

                                    try:
                                        action = (
                                            action.get_object()
                                        )
                                    except Exception:
                                        pass

                                    uri = action.get(
                                        "/URI"
                                    )

                                    if uri:

                                        url = self._clean_url(
                                            str(uri)
                                        )

                                        if url:

                                            links.append({
                                                "url": url,
                                                "text": "",
                                                "type":
                                                    self._classify_link(
                                                        url
                                                    ),
                                                "source":
                                                    "pdf_annotation",
                                                "embedded": True,
                                                "page":
                                                    page_number
                                            })

                            except Exception:
                                continue

                    except Exception:
                        continue

        except Exception:
            return []

        return links

    # ============================================================
    # DOCX TEXT EXTRACTION
    # ============================================================

    def _extract_docx_text(self, file_path):

        try:

            from docx import Document

            document = Document(file_path)

            parts = []

            # Paragraphs
            for paragraph in document.paragraphs:

                text = paragraph.text.strip()

                if text:
                    parts.append(text)

            # Tables
            for table in document.tables:

                for row in table.rows:

                    row_text = []

                    for cell in row.cells:

                        cell_text = cell.text.strip()

                        if cell_text:
                            row_text.append(cell_text)

                    if row_text:

                        parts.append(
                            " ".join(row_text)
                        )

            return "\n".join(parts)

        except ImportError:

            raise ImportError(
                "python-docx is not installed. "
                "Run: pip install python-docx"
            )

        except Exception as error:

            raise Exception(
                f"DOCX extraction failed: {error}"
            )

    # ============================================================
    # DOCX HYPERLINK EXTRACTION
    # ============================================================

    def _extract_docx_links(self, file_path):

        links = []

        try:

            from docx import Document

            document = Document(file_path)

            relationship_namespace = (
                "{http://schemas.openxmlformats.org/"
                "officeDocument/2006/relationships}id"
            )

            def process_paragraph(paragraph):

                paragraph_links = []

                try:

                    hyperlink_elements = (
                        paragraph._element.xpath(
                            ".//w:hyperlink"
                        )
                    )

                except Exception:

                    hyperlink_elements = []

                for hyperlink in hyperlink_elements:

                    try:

                        relationship_id = (
                            hyperlink.get(
                                relationship_namespace
                            )
                        )

                        if not relationship_id:
                            continue

                        url = ""

                        try:

                            relationship = (
                                paragraph.part.rels[
                                    relationship_id
                                ]
                            )

                            url = relationship.target_ref

                        except Exception:
                            continue

                        url = self._clean_url(url)

                        if not url:
                            continue

                        display_text = "".join(
                            hyperlink.itertext()
                        ).strip()

                        paragraph_links.append({
                            "url": url,
                            "text": display_text,
                            "type":
                                self._classify_link(url),
                            "source":
                                "docx_hyperlink",
                            "embedded": True
                        })

                    except Exception:
                        continue

                return paragraph_links

            # Normal paragraphs
            for paragraph in document.paragraphs:

                links.extend(
                    process_paragraph(
                        paragraph
                    )
                )

            # Tables
            for table in document.tables:

                for row in table.rows:

                    for cell in row.cells:

                        for paragraph in cell.paragraphs:

                            links.extend(
                                process_paragraph(
                                    paragraph
                                )
                            )

        except Exception:
            return []

        return links

    # ============================================================
    # EXTRACT ALL LINKS
    # ============================================================

    def extract_links(
        self,
        file_path,
        text=""
    ):

        extension = os.path.splitext(
            file_path
        )[1].lower()

        links = []

        # --------------------------------------------------------
        # Visible URLs
        # --------------------------------------------------------

        visible_urls = (
            self._extract_visible_urls(
                text
            )
        )

        for url in visible_urls:

            links.append({
                "url": url,
                "text": url,
                "type":
                    self._classify_link(url),
                "source":
                    "visible_text",
                "embedded": False
            })

        # --------------------------------------------------------
        # PDF links
        # --------------------------------------------------------

        if extension == ".pdf":

            links.extend(
                self._extract_pdf_links(
                    file_path
                )
            )

        # --------------------------------------------------------
        # DOCX links
        # --------------------------------------------------------

        elif extension == ".docx":

            links.extend(
                self._extract_docx_links(
                    file_path
                )
            )

        # --------------------------------------------------------
        # Deduplicate
        # --------------------------------------------------------

        unique_links = []
        seen = set()

        for item in links:

            url = self._clean_url(
                item.get("url", "")
            )

            if not url:
                continue

            normalized = (
                self._normalize_url(
                    url
                )
            )

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)

            item["url"] = url

            item["type"] = (
                self._classify_link(
                    url
                )
            )

            unique_links.append(item)

        return unique_links

    # ============================================================
    # VISIBLE URL DETECTION
    # ============================================================

    def _extract_visible_urls(self, text):

        if not text:
            return []

        text = self._safe_text(text)

        # Handles:
        # https://...
        # http://...
        # www....
        # linkedin.com/...
        # github.com/...

        pattern = (
            r"(?i)"
            r"(?<![\w@])"
            r"(?:"
            r"https?://"
            r"|www\."
            r"|linkedin\.com/"
            r"|github\.com/"
            r"|gitlab\.com/"
            r"|x\.com/"
            r"|twitter\.com/"
            r")"
            r"[^\s<>\[\]{}|\"']+"
        )

        matches = re.findall(
            pattern,
            text
        )

        cleaned = []

        for url in matches:

            url = self._clean_url(url)

            if not url:
                continue

            if url not in cleaned:
                cleaned.append(url)

        return cleaned

    # ============================================================
    # LINK CLASSIFICATION
    # ============================================================

    def _classify_link(self, url):

        lower_url = (
            self._safe_text(url)
            .lower()
            .strip()
        )

        if "linkedin.com" in lower_url:
            return "LinkedIn"

        if "github.com" in lower_url:
            return "GitHub"

        if "gitlab.com" in lower_url:
            return "GitLab"

        if "twitter.com" in lower_url:
            return "Twitter"

        if "x.com" in lower_url:
            return "X"

        if (
            "behance.net" in lower_url
            or "dribbble.com" in lower_url
        ):
            return "Design Portfolio"

        if (
            "portfolio" in lower_url
            or "portfolio." in lower_url
        ):
            return "Portfolio"

        return "Website"

    # ============================================================
    # DETECT EMAIL
    # ============================================================

    def detect_email(self, text):

        if not text:
            return ""

        text = self._safe_text(text)

        # First try normal email
        patterns = [

            r"(?<![\w.+-])"
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
            r"@"
            r"[A-Za-z0-9-]+"
            r"(?:\.[A-Za-z0-9-]+)+"
            r"(?![\w.-])",

            # Handles PDF extraction like:
            # name @ gmail . com
            r"(?i)"
            r"([A-Za-z0-9._%+\-]+)"
            r"\s*@\s*"
            r"([A-Za-z0-9.\-]+)"
            r"\s*\.\s*"
            r"([A-Za-z]{2,})"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                if len(match.groups()) == 3:

                    email = (
                        match.group(1)
                        + "@"
                        + match.group(2)
                        + "."
                        + match.group(3)
                    )

                else:

                    email = match.group(0)

                email = re.sub(
                    r"\s+",
                    "",
                    email
                )

                email = email.strip(
                    ".,;:!?)]}>"
                )

                return email

        return ""

    # ============================================================
    # DETECT PHONE
    # ============================================================

    def detect_phone(self, text):

        if not text:
            return ""

        text = self._safe_text(text)

        patterns = [

            # India +91
            r"(?<!\d)"
            r"\+91[\s\-()]?"
            r"[6-9]\d{4}[\s\-]?\d{5}"
            r"(?!\d)",

            r"(?<!\d)"
            r"\+91[\s\-()]?"
            r"[6-9]\d{9}"
            r"(?!\d)",

            # Indian 10 digit
            r"(?<!\d)"
            r"[6-9]\d{9}"
            r"(?!\d)",

            # International
            r"(?<!\d)"
            r"\+\d{1,3}"
            r"[\s\-()]?"
            r"\d{7,12}"
            r"(?!\d)",

            # 123-456-7890
            r"(?<!\d)"
            r"\d{3}[\s\-]\d{3}[\s\-]\d{4}"
            r"(?!\d)",

            # 12345-67890
            r"(?<!\d)"
            r"\d{5}[\s\-]\d{5}"
            r"(?!\d)"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                value = match.group(0).strip()

                digits = re.sub(
                    r"\D",
                    "",
                    value
                )

                # Reject suspicious short values
                if len(digits) >= 10:
                    return value

        return ""

    # ============================================================
    # DETECT NAME - ROBUST CANDIDATE SCORING
    # ============================================================

    def detect_name(self, text):

        if not text:
            return ""

        text = self.clean_text(text)

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if not lines:
            return ""

        ignored = {
            "resume",
            "curriculum vitae",
            "curriculum",
            "vitae",
            "cv",
            "profile",
            "contact",
            "contact information",
            "contact details",
            "objective",
            "summary",
            "professional summary",
            "resume profile",
            "about me",
            "education",
            "experience",
            "work experience",
            "professional experience",
            "projects",
            "skills",
            "technical skills",
            "certifications",
            "achievements",
            "languages",
            "interests",
            "internship"
        }

        heading_words = {
            "education",
            "experience",
            "projects",
            "skills",
            "certifications",
            "achievements",
            "languages",
            "interests",
            "internship",
            "objective",
            "summary",
            "contact"
        }

        candidates = []

        # Analyze first 30 meaningful lines.
        # PDF extraction can reorder lines, so don't use only first line.
        for index, raw_line in enumerate(lines[:30]):

            line = re.sub(
                r"\s+",
                " ",
                raw_line
            ).strip()

            if not line:
                continue

            lower = line.lower()

            # Remove common decorative separators
            line = line.strip(
                "|•▪●◦‣➢➤►_-"
            )

            lower = line.lower()

            if lower in ignored:
                continue

            if lower in heading_words:
                continue

            # Contact information is not a name
            if "@" in line:
                continue

            if re.search(
                r"(linkedin|github|gitlab|"
                r"portfolio|behance|dribbble|"
                r"www\.|https?://)",
                lower
            ):
                continue

            # Don't accept lines containing obvious contact labels
            if re.search(
                r"\b(email|phone|mobile|"
                r"contact|address|location)\b",
                lower
            ):
                continue

            # Names should not contain digits
            if re.search(
                r"\d",
                line
            ):
                continue

            # Remove separators around name
            candidate = re.sub(
                r"[|•▪●◦‣➢➤►]+",
                " ",
                line
            )

            candidate = re.sub(
                r"\s+",
                " ",
                candidate
            ).strip()

            words = candidate.split()

            if not (2 <= len(words) <= 5):
                continue

            valid = True

            for word in words:

                clean_word = word.strip(
                    ".,'-"
                )

                if not clean_word:
                    valid = False
                    break

                if not re.match(
                    r"^[A-Za-z][A-Za-z.\-']*$",
                    clean_word
                ):
                    valid = False
                    break

            if not valid:
                continue

            score = 0

            # Earlier lines are more likely to contain the name
            score += max(
                0,
                30 - index
            )

            # 2 or 3 words are most common
            if len(words) == 2:
                score += 25

            elif len(words) == 3:
                score += 22

            elif len(words) == 4:
                score += 10

            else:
                score += 4

            # Names generally have capitalized words
            capitalized_count = sum(
                1
                for word in words
                if word[:1].isupper()
            )

            if capitalized_count == len(words):
                score += 20

            elif capitalized_count >= 2:
                score += 10

            # Reject obvious role/title lines
            role_words = {
                "developer",
                "engineer",
                "student",
                "intern",
                "designer",
                "analyst",
                "manager",
                "programmer",
                "consultant",
                "specialist",
                "scientist",
                "architect",
                "director",
                "lead"
            }

            if any(
                word.lower().strip(".,")
                in role_words
                for word in words
            ):
                score -= 20

            candidates.append(
                (
                    score,
                    candidate
                )
            )

        if candidates:

            candidates.sort(
                key=lambda item: item[0],
                reverse=True
            )

            return candidates[0][1]

        return ""

    # ============================================================
    # DETECT LINKEDIN FROM TEXT
    # ============================================================

    def detect_linkedin(self, text):

        if not text:
            return ""

        pattern = (
            r"(?i)"
            r"(?<![\w])"
            r"(?:https?://)?"
            r"(?:www\.)?"
            r"linkedin\.com/"
            r"[^\s<>\[\]{}|\"']+"
        )

        matches = re.findall(
            pattern,
            text
        )

        for match in matches:

            url = self._clean_url(match)

            if url:

                if not re.match(
                    r"(?i)^https?://",
                    url
                ):
                    url = "https://" + url

                return url

        return ""

    # ============================================================
    # DETECT GITHUB FROM TEXT
    # ============================================================

    def detect_github(self, text):

        if not text:
            return ""

        pattern = (
            r"(?i)"
            r"(?<![\w])"
            r"(?:https?://)?"
            r"(?:www\.)?"
            r"github\.com/"
            r"[^\s<>\[\]{}|\"']+"
        )

        matches = re.findall(
            pattern,
            text
        )

        for match in matches:

            url = self._clean_url(match)

            if url:

                if not re.match(
                    r"(?i)^https?://",
                    url
                ):
                    url = "https://" + url

                return url

        return ""

    # ============================================================
    # DETECT PROFILE FROM LINKS
    # ============================================================

    def detect_linkedin_from_links(self, links):

        for link in links or []:

            url = self._safe_text(
                link.get("url", "")
            )

            if "linkedin.com" in url.lower():

                return self._normalize_url(
                    url
                )

        return ""

    def detect_github_from_links(self, links):

        for link in links or []:

            url = self._safe_text(
                link.get("url", "")
            )

            if "github.com" in url.lower():

                return self._normalize_url(
                    url
                )

        return ""

    # ============================================================
    # SKILLS
    # ============================================================

    def get_skill_database(self):
        return self.skill_database

    def detect_skills(self, text):

        if not text:
            return []

        detected_skills = []

        skills_sorted = sorted(
            self.skill_database,
            key=len,
            reverse=True
        )

        for skill in skills_sorted:

            pattern = (
                r"(?<![A-Za-z0-9])"
                + re.escape(skill)
                + r"(?![A-Za-z0-9])"
            )

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):

                if skill not in detected_skills:
                    detected_skills.append(skill)

        return detected_skills

    # ============================================================
    # SECTIONS
    # ============================================================

    def get_section_keywords(self):
        return self.section_keywords

    def detect_sections(self, text):

        if not text:
            return []

        sections = []

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for section, keywords in self.section_keywords.items():

            found = False

            for line in lines:

                normalized_line = re.sub(
                    r"[^a-zA-Z ]",
                    " ",
                    line.lower()
                )

                normalized_line = re.sub(
                    r"\s+",
                    " ",
                    normalized_line
                ).strip()

                for keyword in keywords:

                    normalized_keyword = (
                        re.sub(
                            r"[^a-zA-Z ]",
                            " ",
                            keyword.lower()
                        )
                    )

                    normalized_keyword = re.sub(
                        r"\s+",
                        " ",
                        normalized_keyword
                    ).strip()

                    # Stronger section matching:
                    # either exact heading or very short heading line
                    if (
                        normalized_line
                        == normalized_keyword
                    ):

                        found = True
                        break

                if found:
                    break

            if found:
                sections.append(section)

        return sections

    # ============================================================
    # CONTENT QUALITY
    # ============================================================

    def calculate_content_quality(self, text):

        word_count = len(text.split())
        character_count = len(text)

        score = 0

        if word_count >= 500:
            score += 35
        elif word_count >= 400:
            score += 32
        elif word_count >= 300:
            score += 28
        elif word_count >= 250:
            score += 25
        elif word_count >= 150:
            score += 18
        elif word_count >= 75:
            score += 10
        else:
            score += 5

        if character_count >= 2500:
            score += 15
        elif character_count >= 1800:
            score += 13
        elif character_count >= 1200:
            score += 10
        elif character_count >= 600:
            score += 7
        else:
            score += 3

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if len(lines) >= 12:
            score += 15
        elif len(lines) >= 8:
            score += 12
        elif len(lines) >= 5:
            score += 8
        else:
            score += 4

        action_count = self.count_action_verbs(text)

        if action_count >= 8:
            score += 20
        elif action_count >= 5:
            score += 16
        elif action_count >= 3:
            score += 12
        elif action_count >= 1:
            score += 7
        else:
            score += 2

        generic_count = self.count_generic_phrases(text)

        score -= min(
            generic_count * 2,
            10
        )

        return max(
            0,
            min(score, 100)
        )

    # ============================================================
    # ACTION VERBS
    # ============================================================

    def count_action_verbs(self, text):

        lower_text = text.lower()

        count = 0

        for verb in self.strong_action_verbs:

            count += len(
                re.findall(
                    r"\b"
                    + re.escape(verb)
                    + r"\b",
                    lower_text
                )
            )

        return count

    def detect_weak_action_verbs(self, text):

        lower_text = text.lower()

        detected = []

        for verb in self.weak_action_verbs:

            if re.search(
                r"\b"
                + re.escape(verb)
                + r"\b",
                lower_text
            ):

                if verb not in detected:
                    detected.append(verb)

        return detected

    # ============================================================
    # GENERIC PHRASES
    # ============================================================

    def count_generic_phrases(self, text):

        lower_text = text.lower()

        return sum(
            1
            for phrase in self.generic_phrases
            if phrase in lower_text
        )

    def detect_generic_descriptions(self, text):

        lower_text = text.lower()

        return [
            phrase
            for phrase in self.generic_phrases
            if phrase in lower_text
        ]

    # ============================================================
    # METRICS
    # ============================================================

    def detect_metrics(self, text):

        metric_patterns = [

            r"\b\d+(?:\.\d+)?%",

            r"\b\d+(?:\.\d+)?\+",

            r"\b\d+(?:,\d{3})+\+?",

            r"\b\d+(?:\.\d+)?\s*"
            r"(?:users|clients|customers|projects|"
            r"students|records|requests|applications|"
            r"members|hours|days|months|years)",

            r"\b(?:increased|improved|reduced|"
            r"optimized|saved|grew|boosted)"
            r".{0,60}"
            r"\b\d+(?:\.\d+)?%?"
        ]

        found = []

        for pattern in metric_patterns:

            matches = re.findall(
                pattern,
                text,
                re.IGNORECASE
            )

            for match in matches:

                if isinstance(match, tuple):
                    value = " ".join(match)
                else:
                    value = match

                value = value.strip()

                if value and value not in found:
                    found.append(value)

        return found

    # ============================================================
    # ACHIEVEMENT STRENGTH
    # ============================================================

    def calculate_achievement_strength(self, text):

        score = 0

        metrics = self.detect_metrics(text)

        action_count = self.count_action_verbs(text)

        weak_verbs = self.detect_weak_action_verbs(text)

        achievements_section = (
            "Achievements"
            in self.detect_sections(text)
        )

        if len(metrics) >= 8:
            score += 40
        elif len(metrics) >= 5:
            score += 32
        elif len(metrics) >= 3:
            score += 24
        elif len(metrics) >= 1:
            score += 12

        if action_count >= 10:
            score += 30
        elif action_count >= 7:
            score += 25
        elif action_count >= 4:
            score += 18
        elif action_count >= 2:
            score += 10

        if achievements_section:
            score += 15

        score -= min(
            len(weak_verbs) * 2,
            10
        )

        return max(
            0,
            min(score, 100)
        )

    # ============================================================
    # SKILLS STRENGTH
    # ============================================================

    def calculate_skills_strength(self, skills):

        count = len(skills)

        if count >= 15:
            return 100
        if count >= 12:
            return 94
        if count >= 10:
            return 88
        if count >= 8:
            return 80
        if count >= 6:
            return 70
        if count >= 4:
            return 58
        if count >= 2:
            return 40
        if count == 1:
            return 25

        return 10

    # ============================================================
    # KEYWORD COVERAGE
    # ============================================================

    def calculate_keyword_coverage(
        self,
        skills,
        text
    ):

        all_keywords = set()

        for keywords in self.role_keywords.values():

            for keyword in keywords:
                all_keywords.add(keyword)

        matched = []
        missing = []

        for keyword in sorted(
            all_keywords,
            key=len,
            reverse=True
        ):

            pattern = (
                r"(?<![A-Za-z0-9])"
                + re.escape(keyword)
                + r"(?![A-Za-z0-9])"
            )

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):
                matched.append(keyword)
            else:
                missing.append(keyword)

        total = len(
            matched
        ) + len(
            missing
        )

        score = (
            round(
                len(matched) / total * 100
            )
            if total
            else 0
        )

        return {
            "score": score,
            "matched_keywords": matched,
            "missing_keywords": missing
        }

    # ============================================================
    # ROLE KEYWORD COVERAGE
    # ============================================================

    def calculate_role_keyword_coverage(self, text):

        result = {}

        for role, keywords in self.role_keywords.items():

            matched = []
            missing = []

            for keyword in keywords:

                pattern = (
                    r"(?<![A-Za-z0-9])"
                    + re.escape(keyword)
                    + r"(?![A-Za-z0-9])"
                )

                if re.search(
                    pattern,
                    text,
                    re.IGNORECASE
                ):
                    matched.append(keyword)
                else:
                    missing.append(keyword)

            total = len(keywords)

            score = (
                round(
                    len(matched) / total * 100
                )
                if total
                else 0
            )

            result[role] = {
                "score": score,
                "matched_keywords": matched,
                "missing_keywords": missing
            }

        return result

    # ============================================================
    # ATS SCORE
    # ============================================================

    def calculate_ats_score(
        self,
        text,
        skills,
        sections,
        email,
        phone,
        linkedin="",
        github=""
    ):

        score = 0

        if email:
            score += 8

        if phone:
            score += 7

        if linkedin:
            score += 5

        if github:
            score += 5

        required_sections = [
            "Education",
            "Skills",
            "Projects",
            "Experience"
        ]

        for section in required_sections:

            if section in sections:
                score += 8

        skill_count = len(skills)

        if skill_count >= 10:
            score += 15
        elif skill_count >= 7:
            score += 12
        elif skill_count >= 5:
            score += 10
        elif skill_count >= 3:
            score += 7
        elif skill_count >= 1:
            score += 4

        word_count = len(text.split())

        if 300 <= word_count <= 800:
            score += 10
        elif 200 <= word_count <= 1000:
            score += 8
        elif word_count >= 100:
            score += 5

        action_count = self.count_action_verbs(text)

        if action_count >= 8:
            score += 10
        elif action_count >= 5:
            score += 8
        elif action_count >= 3:
            score += 6
        elif action_count >= 1:
            score += 3

        metrics = self.detect_metrics(text)

        if len(metrics) >= 5:
            score += 10
        elif len(metrics) >= 3:
            score += 7
        elif len(metrics) >= 1:
            score += 4

        return max(
            0,
            min(score, 100)
        )

    # ============================================================
    # OVERALL SCORE
    # ============================================================

    def calculate_overall_score(
        self,
        ats_score,
        content_quality,
        skills_strength,
        achievement_strength
    ):

        overall = (
            ats_score * 0.30
            + content_quality * 0.25
            + skills_strength * 0.20
            + achievement_strength * 0.25
        )

        return round(overall)

    # ============================================================
    # MISSING SECTIONS
    # ============================================================

    def detect_missing_sections(self, sections):

        return [
            section
            for section in self.recommended_sections
            if section not in sections
        ]

    # ============================================================
    # WEAK SECTIONS
    # ============================================================

    def detect_weak_sections(
        self,
        text,
        sections
    ):

        weak_sections = []

        lower_text = text.lower()

        if "Projects" in sections:

            project_keywords = [
                "built",
                "developed",
                "implemented",
                "created",
                "designed",
                "%",
                "users",
                "accuracy",
                "performance"
            ]

            count = sum(
                1
                for keyword in project_keywords
                if keyword in lower_text
            )

            if count < 3:
                weak_sections.append("Projects")

        if "Experience" in sections:

            signals = [
                "developed",
                "managed",
                "implemented",
                "improved",
                "increased",
                "reduced",
                "optimized"
            ]

            count = sum(
                1
                for keyword in signals
                if keyword in lower_text
            )

            if count < 2:
                weak_sections.append("Experience")

        if "Skills" in sections:

            if len(self.detect_skills(text)) < 5:
                weak_sections.append("Skills")

        if "Achievements" in sections:

            if len(self.detect_metrics(text)) < 2:
                weak_sections.append("Achievements")

        if "Summary" in sections:

            signals = [
                "python",
                "developer",
                "engineer",
                "data",
                "ai",
                "machine learning",
                "software"
            ]

            count = sum(
                1
                for signal in signals
                if signal in lower_text
            )

            if count < 2:
                weak_sections.append("Summary")

        return list(
            dict.fromkeys(
                weak_sections
            )
        )

    # ============================================================
    # WEAKNESSES
    # ============================================================

    def detect_weaknesses(
        self,
        text,
        skills,
        sections,
        email,
        phone,
        linkedin,
        github
    ):

        weaknesses = []

        missing_sections = (
            self.detect_missing_sections(
                sections
            )
        )

        for section in missing_sections:

            if section in [
                "Languages",
                "Interests",
                "Objective"
            ]:
                continue

            weaknesses.append({
                "type": "missing_section",
                "severity": "medium",
                "section": section,
                "message":
                    f"{section} section is missing."
            })

        weak_sections = (
            self.detect_weak_sections(
                text,
                sections
            )
        )

        for section in weak_sections:

            weaknesses.append({
                "type": "weak_section",
                "severity": "medium",
                "section": section,
                "message":
                    f"{section} section needs stronger content."
            })

        if not email:

            weaknesses.append({
                "type": "contact",
                "severity": "high",
                "section": "Contact",
                "message":
                    "Professional email address is missing."
            })

        if not phone:

            weaknesses.append({
                "type": "contact",
                "severity": "high",
                "section": "Contact",
                "message":
                    "Phone number is missing."
            })

        if not linkedin:

            weaknesses.append({
                "type": "profile",
                "severity": "medium",
                "section": "LinkedIn",
                "message":
                    "LinkedIn profile is missing."
            })

        if not github:

            weaknesses.append({
                "type": "profile",
                "severity": "medium",
                "section": "GitHub",
                "message":
                    "GitHub profile is missing."
            })

        if len(skills) < 5:

            weaknesses.append({
                "type": "skills",
                "severity": "high",
                "section": "Skills",
                "message":
                    "Insufficient technical skills detected."
            })

        metrics = self.detect_metrics(text)

        if len(metrics) == 0:

            weaknesses.append({
                "type": "metrics",
                "severity": "high",
                "section": "Achievements",
                "message":
                    "No measurable achievements or metrics detected."
            })

        elif len(metrics) < 3:

            weaknesses.append({
                "type": "metrics",
                "severity": "medium",
                "section": "Achievements",
                "message":
                    "Resume contains too few measurable results."
            })

        weak_verbs = (
            self.detect_weak_action_verbs(
                text
            )
        )

        if len(weak_verbs) >= 3:

            weaknesses.append({
                "type": "action_verbs",
                "severity": "medium",
                "section": "Content",
                "message":
                    "Several weak or passive action verbs were detected.",
                "examples":
                    weak_verbs[:8]
            })

        strong_count = (
            self.count_action_verbs(
                text
            )
        )

        if strong_count < 3:

            weaknesses.append({
                "type": "action_verbs",
                "severity": "high",
                "section": "Content",
                "message":
                    "Resume uses too few strong action verbs."
            })

        generic_phrases = (
            self.detect_generic_descriptions(
                text
            )
        )

        if generic_phrases:

            weaknesses.append({
                "type": "generic_description",
                "severity": "medium",
                "section": "Content",
                "message":
                    "Generic resume language was detected.",
                "examples":
                    generic_phrases[:8]
            })

        word_count = len(text.split())

        if word_count < 150:

            weaknesses.append({
                "type": "content_length",
                "severity": "high",
                "section": "Content",
                "message":
                    "Resume content is too short."
            })

        elif word_count < 250:

            weaknesses.append({
                "type": "content_length",
                "severity": "medium",
                "section": "Content",
                "message":
                    "Resume may need more detail."
            })

        keyword_data = (
            self.calculate_keyword_coverage(
                skills,
                text
            )
        )

        if keyword_data["score"] < 30:

            weaknesses.append({
                "type": "keywords",
                "severity": "high",
                "section": "ATS",
                "message":
                    "Keyword coverage is weak for technical roles."
            })

        elif keyword_data["score"] < 50:

            weaknesses.append({
                "type": "keywords",
                "severity": "medium",
                "section": "ATS",
                "message":
                    "Resume could use more role-specific keywords."
            })

        return weaknesses

    # ============================================================
    # SMART RECOMMENDATIONS
    # ============================================================

    def generate_smart_recommendations(
        self,
        text,
        skills,
        sections,
        email,
        phone,
        linkedin,
        github,
        weaknesses
    ):

        recommendations = []

        metrics = self.detect_metrics(text)

        if len(metrics) < 3:

            recommendations.append({
                "priority": "HIGH",
                "title":
                    "Add measurable achievements.",
                "description":
                    "Add numbers, percentages, scale, "
                    "performance improvements, users, "
                    "accuracy, revenue, or time saved "
                    "to demonstrate impact."
            })

        if len(skills) < 5:

            recommendations.append({
                "priority": "HIGH",
                "title":
                    "Strengthen your technical skills.",
                "description":
                    "Add relevant technical skills "
                    "that match your target roles."
            })

        if not email:

            recommendations.append({
                "priority": "HIGH",
                "title":
                    "Add a professional email.",
                "description":
                    "Recruiters need a reliable way "
                    "to contact you."
            })

        if not phone:

            recommendations.append({
                "priority": "HIGH",
                "title":
                    "Add your phone number.",
                "description":
                    "Include a professional contact number."
            })

        if (
            "Projects" not in sections
            or "Projects"
            in self.detect_weak_sections(
                text,
                sections
            )
        ):

            recommendations.append({
                "priority": "MEDIUM",
                "title":
                    "Improve project descriptions.",
                "description":
                    "Describe what you built, "
                    "which technologies you used, "
                    "what problem you solved, "
                    "and what result you achieved."
            })

        weak_verbs = (
            self.detect_weak_action_verbs(
                text
            )
        )

        if weak_verbs:

            recommendations.append({
                "priority": "MEDIUM",
                "title":
                    "Replace weak action verbs.",
                "description":
                    "Replace words such as "
                    + ", ".join(weak_verbs[:5])
                    + " with stronger action verbs."
            })

        if not linkedin:

            recommendations.append({
                "priority": "MEDIUM",
                "title":
                    "Add your LinkedIn profile.",
                "description":
                    "Include a professional LinkedIn URL "
                    "in your contact information."
            })

        if not github:

            recommendations.append({
                "priority": "MEDIUM",
                "title":
                    "Add your GitHub profile.",
                "description":
                    "Showcase coding projects, repositories "
                    "and technical contributions."
            })

        recommendations.append({
            "priority": "LOW",
            "title":
                "Add role-specific keywords.",
            "description":
                "Tailor your resume keywords to the "
                "job description before applying."
        })

        if self.detect_generic_descriptions(text):

            recommendations.append({
                "priority": "LOW",
                "title":
                    "Reduce generic descriptions.",
                "description":
                    "Replace generic phrases with "
                    "specific evidence and outcomes."
            })

        return recommendations

    # ============================================================
    # ACTION PLAN
    # ============================================================

    def generate_action_plan(
        self,
        recommendations
    ):

        action_plan = []

        priority_order = [
            "HIGH",
            "MEDIUM",
            "LOW"
        ]

        step = 1

        for priority in priority_order:

            for item in recommendations:

                if item["priority"] != priority:
                    continue

                action_plan.append({
                    "step": step,
                    "priority": priority,
                    "action": item["title"],
                    "details": item["description"]
                })

                step += 1

        return action_plan

    # ============================================================
    # SIMPLE SUGGESTIONS
    # ============================================================

    def generate_suggestions(
        self,
        text,
        skills,
        sections,
        email,
        phone
    ):

        suggestions = []

        if not email:
            suggestions.append(
                "Add a professional email address."
            )

        if not phone:
            suggestions.append(
                "Add a valid phone number."
            )

        if "Education" not in sections:
            suggestions.append(
                "Add a clear Education section."
            )

        if "Skills" not in sections:
            suggestions.append(
                "Add a dedicated Technical Skills section."
            )

        if "Projects" not in sections:
            suggestions.append(
                "Add relevant projects with technologies and outcomes."
            )

        if "Experience" not in sections:
            suggestions.append(
                "Add internship, work or practical experience if available."
            )

        if "Certifications" not in sections:
            suggestions.append(
                "Add relevant certifications and credentials."
            )

        if len(skills) < 5:
            suggestions.append(
                "Add more role-relevant technical skills."
            )

        word_count = len(text.split())

        if word_count < 250:
            suggestions.append(
                "Add more detail about projects, experience and achievements."
            )

        metrics = self.detect_metrics(text)

        if not metrics:
            suggestions.append(
                "Add measurable achievements using numbers or percentages."
            )

        weak_verbs = (
            self.detect_weak_action_verbs(
                text
            )
        )

        if weak_verbs:
            suggestions.append(
                "Replace weak action verbs with stronger verbs such as "
                "developed, implemented, optimized or automated."
            )

        if not suggestions:
            suggestions.append(
                "Your resume has a strong structure. "
                "Tailor keywords and achievements for each job description."
            )

        return suggestions

    # ============================================================
    # SCORE LABEL
    # ============================================================

    def get_score_label(self, score):

        if score >= 90:
            return "Excellent"

        if score >= 80:
            return "Strong"

        if score >= 70:
            return "Good"

        if score >= 55:
            return "Needs Improvement"

        return "Needs Optimization"

    # ============================================================
    # RESUME HEALTH
    # ============================================================

    def build_resume_health(
        self,
        overall_score,
        ats_score,
        content_quality,
        skills_strength,
        achievement_strength
    ):

        return {

            "overall_resume": {
                "score": overall_score,
                "label":
                    self.get_score_label(
                        overall_score
                    )
            },

            "ats_compatibility": {
                "score": ats_score,
                "label":
                    self.get_score_label(
                        ats_score
                    )
            },

            "content_quality": {
                "score": content_quality,
                "label":
                    self.get_score_label(
                        content_quality
                    )
            },

            "skills_strength": {
                "score": skills_strength,
                "label":
                    self.get_score_label(
                        skills_strength
                    )
            },

            "achievement_strength": {
                "score": achievement_strength,
                "label":
                    self.get_score_label(
                        achievement_strength
                    )
            }
        }

    # ============================================================
    # COMPLETE TEXT ANALYSIS
    # ============================================================

    def analyze_text(
        self,
        text,
        links=None
    ):

        text = self.clean_text(text)

        if not text:

            return {
                "success": False,
                "message":
                    "No readable text found in the resume."
            }

        if links is None:
            links = []

        # --------------------------------------------------------
        # BASIC EXTRACTION
        # --------------------------------------------------------

        name = self.detect_name(text)

        email = self.detect_email(text)

        phone = self.detect_phone(text)

        # --------------------------------------------------------
        # PROFILE LINKS
        # --------------------------------------------------------

        linkedin = self.detect_linkedin(text)

        github = self.detect_github(text)

        embedded_linkedin = (
            self.detect_linkedin_from_links(
                links
            )
        )

        embedded_github = (
            self.detect_github_from_links(
                links
            )
        )

        if not linkedin and embedded_linkedin:
            linkedin = embedded_linkedin

        if not github and embedded_github:
            github = embedded_github

        # --------------------------------------------------------
        # SKILLS / SECTIONS
        # --------------------------------------------------------

        skills = self.detect_skills(text)

        sections = self.detect_sections(text)

        # --------------------------------------------------------
        # STATISTICS
        # --------------------------------------------------------

        word_count = len(text.split())

        character_count = len(text)

        # --------------------------------------------------------
        # SCORES
        # --------------------------------------------------------

        content_quality = (
            self.calculate_content_quality(
                text
            )
        )

        skills_strength = (
            self.calculate_skills_strength(
                skills
            )
        )

        achievement_strength = (
            self.calculate_achievement_strength(
                text
            )
        )

        ats_score = (
            self.calculate_ats_score(
                text,
                skills,
                sections,
                email,
                phone,
                linkedin,
                github
            )
        )

        overall_score = (
            self.calculate_overall_score(
                ats_score,
                content_quality,
                skills_strength,
                achievement_strength
            )
        )

        # --------------------------------------------------------
        # ADVANCED ANALYSIS
        # --------------------------------------------------------

        weaknesses = (
            self.detect_weaknesses(
                text,
                skills,
                sections,
                email,
                phone,
                linkedin,
                github
            )
        )

        recommendations = (
            self.generate_smart_recommendations(
                text,
                skills,
                sections,
                email,
                phone,
                linkedin,
                github,
                weaknesses
            )
        )

        action_plan = (
            self.generate_action_plan(
                recommendations
            )
        )

        # --------------------------------------------------------
        # KEYWORD ANALYSIS
        # --------------------------------------------------------

        keyword_coverage = (
            self.calculate_keyword_coverage(
                skills,
                text
            )
        )

        role_keyword_coverage = (
            self.calculate_role_keyword_coverage(
                text
            )
        )

        # --------------------------------------------------------
        # OTHER ANALYSIS
        # --------------------------------------------------------

        missing_sections = (
            self.detect_missing_sections(
                sections
            )
        )

        weak_sections = (
            self.detect_weak_sections(
                text,
                sections
            )
        )

        weak_action_verbs = (
            self.detect_weak_action_verbs(
                text
            )
        )

        generic_descriptions = (
            self.detect_generic_descriptions(
                text
            )
        )

        metrics = (
            self.detect_metrics(
                text
            )
        )

        # --------------------------------------------------------
        # LINK STATISTICS
        # --------------------------------------------------------

        embedded_links = [
            link
            for link in links
            if link.get(
                "embedded",
                False
            )
        ]

        visible_links = [
            link
            for link in links
            if not link.get(
                "embedded",
                False
            )
        ]

        link_types = list(
            dict.fromkeys(
                link.get(
                    "type",
                    "Website"
                )
                for link in links
            )
        )

        high_priority_count = len([
            weakness
            for weakness in weaknesses
            if weakness.get("severity") == "high"
        ])

        medium_priority_count = len([
            weakness
            for weakness in weaknesses
            if weakness.get("severity") == "medium"
        ])

        # --------------------------------------------------------
        # RETURN
        # --------------------------------------------------------

        return {

            "success": True,

            # PERSONAL INFORMATION
            "name": name,
            "detected_name": name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,

            # LINKS
            "links": links,
            "embedded_links": embedded_links,
            "visible_links": visible_links,
            "link_count": len(links),
            "embedded_link_count":
                len(embedded_links),
            "visible_link_count":
                len(visible_links),
            "link_types": link_types,

            # RESUME DATA
            "skills": skills,
            "skill_count": len(skills),
            "sections": sections,
            "section_count": len(sections),

            # SCORES
            "resume_strength_score":
                overall_score,

            "strength_score":
                overall_score,

            "ats_score":
                ats_score,

            "strength_label":
                self.get_score_label(
                    overall_score
                ),

            "ats_label":
                self.get_score_label(
                    ats_score
                ),

            # HEALTH
            "resume_health":
                self.build_resume_health(
                    overall_score,
                    ats_score,
                    content_quality,
                    skills_strength,
                    achievement_strength
                ),

            "content_quality":
                content_quality,

            "skills_strength":
                skills_strength,

            "achievement_strength":
                achievement_strength,

            # WEAKNESSES
            "weaknesses": weaknesses,
            "weakness_count":
                len(weaknesses),

            "high_priority_count":
                high_priority_count,

            "medium_priority_count":
                medium_priority_count,

            "missing_sections":
                missing_sections,

            "weak_sections":
                weak_sections,

            "missing_achievements":
                len(metrics) == 0,

            "metrics":
                metrics,

            "metric_count":
                len(metrics),

            "weak_action_verbs":
                weak_action_verbs,

            "generic_descriptions":
                generic_descriptions,

            "missing_github":
                not bool(github),

            "missing_linkedin":
                not bool(linkedin),

            # KEYWORDS
            "keyword_coverage":
                keyword_coverage,

            "keyword_coverage_score":
                keyword_coverage.get(
                    "score",
                    0
                ),

            "role_keyword_coverage":
                role_keyword_coverage,

            # RECOMMENDATIONS
            "recommendations":
                recommendations,

            "smart_recommendations":
                recommendations,

            # ACTION PLAN
            "action_plan":
                action_plan,

            # SUGGESTIONS
            "suggestions":
                self.generate_suggestions(
                    text,
                    skills,
                    sections,
                    email,
                    phone
                ),

            # STATISTICS
            "word_count":
                word_count,

            "character_count":
                character_count,

            # UI FLOW
            "analysis_flow": [
                "AI ANALYSIS",
                "SCORE",
                "WEAKNESSES",
                "RECOMMENDATIONS",
                "ACTION PLAN"
            ]
        }

    # ============================================================
    # CLEAN TEXT
    # ============================================================

    def clean_text(self, text):

        if not text:
            return ""

        text = self._safe_text(text)

        text = text.replace(
            "\x00",
            " "
        )

        text = text.replace(
            "\r\n",
            "\n"
        )

        text = text.replace(
            "\r",
            "\n"
        )

        # Fix common PDF extraction artifacts
        text = text.replace(
            "\u00a0",
            " "
        )

        text = text.replace(
            "\u200b",
            ""
        )

        text = text.replace(
            "\ufeff",
            ""
        )

        bullet_characters = [
            "•",
            "▪",
            "●",
            "◦",
            "‣",
            "➢",
            "➤",
            "►"
        ]

        for bullet in bullet_characters:

            text = text.replace(
                bullet,
                " "
            )

        # Normalize tabs/spaces
        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        text = re.sub(
            r"\n[ \t]+",
            "\n",
            text
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        return text.strip()

    # ============================================================
    # ANALYZE FILE
    # ============================================================

    def analyze_file(self, file_path):

        # Extract text
        text = self.extract_text(
            file_path
        )

        # Extract visible + embedded links
        links = self.extract_links(
            file_path,
            text
        )

        # Analyze
        result = self.analyze_text(
            text,
            links
        )

        result["resume_file"] = (
            os.path.basename(
                file_path
            )
        )

        return result


# ================================================================
# DIRECT TEST
# ================================================================

if __name__ == "__main__":

    analyzer = ResumeAnalyzer()

    print("=" * 70)

    print(
        "                 AI CAREER COPILOT"
    )

    print(
        "                ADVANCED RESUME COPILOT"
    )

    print("=" * 70)

    print(
        "Resume Analyzer module loaded successfully."
    )

    print(
        "Supported formats: PDF | DOCX | TXT"
    )

    print(
        f"Skills database: "
        f"{len(analyzer.skill_database)} skills"
    )

    print(
        f"Role profiles: "
        f"{len(analyzer.role_keywords)}"
    )

    print("=" * 70)