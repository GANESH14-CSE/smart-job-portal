"""
AI keyword matching, ATS scoring, fake job detection, skill extraction.
No heavy setup needed. Works with TF-IDF fallback if BERT not installed.
"""
import re, math
from typing import List

SKILLS_DB = {
    'python','java','javascript','typescript','c','c++','c#','go','rust','swift','kotlin',
    'ruby','php','scala','r','matlab','bash','dart','html','html5','css','css3',
    'react','reactjs','vue','angular','next.js','svelte','bootstrap','tailwind','jquery',
    'sass','webpack','redux','graphql','ajax','json','django','flask','fastapi',
    'node.js','express','spring','spring boot','laravel','rails','asp.net','.net',
    'sql','mysql','postgresql','sqlite','mongodb','redis','cassandra','oracle',
    'firebase','dynamodb','elasticsearch','nosql','mariadb',
    'aws','azure','gcp','google cloud','heroku','docker','kubernetes','jenkins',
    'ci/cd','terraform','ansible','linux','ubuntu','nginx','apache','git','github','gitlab',
    'devops','microservices','machine learning','ml','deep learning','artificial intelligence',
    'neural networks','nlp','natural language processing','computer vision',
    'tensorflow','keras','pytorch','scikit-learn','sklearn','pandas','numpy',
    'matplotlib','seaborn','opencv','bert','gpt','llm','spacy','nltk','xgboost',
    'data analysis','data science','tableau','power bi','jupyter',
    'android','ios','react native','flutter','xamarin',
    'selenium','pytest','junit','jest','cypress','postman','unit testing','tdd',
    'agile','scrum','kanban','jira','confluence','rest api','restful',
    'excel','figma','photoshop','blockchain','hadoop','spark','kafka',
}

SKILL_RESOURCES = {
    'python':'https://www.learnpython.org/',
    'django':'https://docs.djangoproject.com/en/stable/intro/',
    'machine learning':'https://www.coursera.org/learn/machine-learning',
    'react':'https://react.dev/learn',
    'sql':'https://www.w3schools.com/sql/',
    'aws':'https://aws.amazon.com/training/',
    'docker':'https://docs.docker.com/get-started/',
    'javascript':'https://javascript.info/',
    'data science':'https://www.kaggle.com/learn',
    'nlp':'https://huggingface.co/course/chapter1',
    'tensorflow':'https://www.tensorflow.org/tutorials',
    'git':'https://learngitbranching.js.org/',
}

FREE_EMAIL_DOMAINS = {
    'gmail.com','yahoo.com','hotmail.com','outlook.com',
    'rediffmail.com','ymail.com','aol.com','icloud.com','live.com',
}

SUSPICIOUS_KEYWORDS = [
    'no experience needed','guaranteed income','easy money','earn from home',
    'data entry from home','registration fee','advance fee','pay to work',
    'no interview','no resume required','copy paste jobs','earn per click',
    'multi level marketing','mlm',
]


def extract_skills(text: str) -> List[str]:
    if not text: return []
    found = set()
    t = text.lower()
    for skill in SKILLS_DB:
        pattern = r'\b' + re.escape(skill) + r'\b' if len(skill) <= 3 else re.escape(skill)
        if re.search(pattern, t):
            found.add(skill.title())
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(text[:3000])
        for ent in doc.ents:
            if ent.label_ in ('ORG','PRODUCT') and ent.text.lower().strip() in SKILLS_DB:
                found.add(ent.text.strip())
    except Exception:
        pass
    return sorted(found)


def get_missing_skills(resume_skills: List[str], jd_skills: List[str]) -> List[str]:
    low = {s.lower() for s in resume_skills}
    return [s for s in jd_skills if s.lower() not in low]


def get_skill_resources(missing: List[str]) -> List[dict]:
    result = []
    for s in missing:
        k = s.lower()
        url = SKILL_RESOURCES.get(k, f'https://www.google.com/search?q=learn+{k.replace(" ","+")}')
        result.append({'skill': s, 'url': url, 'label': f'Learn {s}'})
    return result


def _tfidf_cosine(t1: str, t2: str) -> float:
    STOP = {'the','a','an','and','or','in','on','at','to','for','of','with','is','are',
            'was','we','you','it','they','our','your','not','this','that','be','by'}
    def tf(text):
        words = [w for w in re.findall(r'\b[a-z]{3,}\b', text.lower()) if w not in STOP]
        n = len(words) or 1
        return {w: words.count(w)/n for w in set(words)}
    f1, f2 = tf(t1), tf(t2)
    if not f1 or not f2: return 0.0
    vocab = set(f1) | set(f2)
    dot = sum(f1.get(w,0)*f2.get(w,0) for w in vocab)
    m1 = math.sqrt(sum(v**2 for v in f1.values()))
    m2 = math.sqrt(sum(v**2 for v in f2.values()))
    return dot/(m1*m2) if m1 and m2 else 0.0


def compute_semantic_similarity(t1: str, t2: str) -> float:
    if not t1 or not t2: return 0.0
    try:
        from sentence_transformers import SentenceTransformer, util
        model = SentenceTransformer('all-MiniLM-L6-v2')
        e1 = model.encode(t1[:1000], convert_to_tensor=True)
        e2 = model.encode(t2[:1000], convert_to_tensor=True)
        return max(0.0, min(1.0, util.pytorch_cos_sim(e1, e2).item()))
    except Exception:
        return _tfidf_cosine(t1, t2)


def compute_skill_match(resume_skills: List[str], jd_skills: List[str]) -> float:
    if not jd_skills: return 0.0
    low = {s.lower() for s in resume_skills}
    return sum(1 for s in jd_skills if s.lower() in low) / len(jd_skills)


def compute_keyword_density(resume: str, jd: str) -> float:
    STOP = {'the','a','an','and','or','in','on','at','to','for','of','with','is','are',
            'work','good','experience','years','skills','job','required','team','company'}
    words = re.findall(r'\b[a-z]{3,}\b', jd.lower())
    kws = [w for w in words if w not in STOP]
    if not kws: return 0.0
    r = resume.lower()
    return min(1.0, sum(1 for kw in set(kws) if kw in r) / len(set(kws)))


def calculate_ats_score(sm: float, ss: float, kd: float) -> float:
    return round((0.5*sm + 0.3*ss + 0.2*kd)*100, 2)


def run_full_analysis(resume: str, jd: str, r_skills: List[str], j_skills: List[str]) -> dict:
    sm = compute_skill_match(r_skills, j_skills)
    ss = compute_semantic_similarity(resume, jd)
    kd = compute_keyword_density(resume, jd)
    return {
        'ats_score':           calculate_ats_score(sm, ss, kd),
        'match_percentage':    round(sm*100, 2),
        'skill_match_score':   round(sm*100, 2),
        'semantic_similarity': round(ss*100, 2),
        'keyword_density':     round(kd*100, 2),
    }


def predict_success(ats: float, match: float = 0, missing: int = 0) -> dict:
    if ats >= 80:
        base, level = 70+(ats-80), 'High'
        expl = f"ATS score {ats:.0f} is excellent! Strong match for this role."
    elif ats >= 60:
        base, level = 40+(ats-60)*1.5, 'Medium'
        expl = f"ATS score {ats:.0f} is moderate. Improve missing skills to boost chances."
    else:
        base, level = max(5, ats*0.6), 'Low'
        expl = f"ATS score {ats:.0f} is below threshold. Focus on skill gaps."
    prob = round(max(2.0, min(95.0, base - min(15, missing*2))), 1)
    tips = []
    if missing > 0: tips.append(f"Add {missing} missing skill(s) to your resume.")
    if ats < 70:    tips.append("Use more keywords from the job description.")
    if match < 50:  tips.append("Low skill overlap — consider upskilling first.")
    if ats >= 80:   tips.append("Strong profile! Prepare confidently for interviews.")
    return {'success_probability': prob, 'level': level, 'explanation': expl, 'tips': tips}


def get_ats_grade(s: float) -> str:
    if s>=90: return 'A+'
    if s>=80: return 'A'
    if s>=70: return 'B+'
    if s>=60: return 'B'
    if s>=50: return 'C'
    return 'D'


def get_success_color(level: str) -> str:
    return {'High':'success','Medium':'warning','Low':'danger'}.get(level,'secondary')


def detect_fake_job(company, company_email, company_website,
                    description, requirements, location,
                    salary_min, salary_max) -> dict:
    reasons, score = [], 0.0
    if not company_email:
        reasons.append("No company email provided."); score += 25
    else:
        try:
            domain = company_email.split('@')[1].lower()
            if domain in FREE_EMAIL_DOMAINS:
                reasons.append(f"Free email domain ({domain}) used instead of corporate email."); score += 25
        except: reasons.append("Invalid email format."); score += 15
    full = f"{description} {requirements}".lower()
    hits = [k for k in SUSPICIOUS_KEYWORDS if k in full]
    if hits:
        reasons.append(f"Suspicious phrases: {', '.join(hits[:3])}"); score += min(35, len(hits)*10)
    miss = []
    if not company or len(company.strip()) < 3: miss.append("company name")
    if not company_website: miss.append("company website")
    if not description or len(description.strip()) < 50: miss.append("job description")
    if not location or len(location.strip()) < 3: miss.append("location")
    if miss:
        reasons.append(f"Missing info: {', '.join(miss)}."); score += min(25, len(miss)*7)
    if salary_max > 200:
        reasons.append(f"Unrealistic salary ₹{salary_max} LPA."); score += 15
    elif salary_max > 0 and salary_min > 0 and salary_max/salary_min > 10:
        reasons.append("Suspiciously wide salary range."); score += 8
    prob = round(min(100.0, score), 2)
    level = 'High' if prob >= 60 else ('Medium' if prob >= 30 else 'Low')
    return {
        'fake_probability': prob, 'risk_level': level,
        'reasons': reasons or ['No suspicious indicators found.'],
        'is_suspicious': prob >= 40,
    }
