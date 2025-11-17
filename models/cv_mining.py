import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load SpaCy NER model
nlp = spacy.load("en_core_web_sm")  # Make sure to install it: pip install spacy && python -m spacy download en_core_web_sm

def apply_ner(cv_text):
    """Apply Named Entity Recognition to extract key entities"""
    doc = nlp(cv_text)
    entities = {"PERSON": [], "ORG": [], "GPE": [], "SKILL": []}  # You can add more categories as needed
    
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["PERSON"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["ORG"].append(ent.text)
        elif ent.label_ == "GPE":  # Geopolitical entity (places)
            entities["GPE"].append(ent.text)
    
    # Manually add skill extraction if you want specific skills (can be extended to use more advanced methods like spaCy custom NER)
    skills = ['python', 'java', 'javascript', 'machine learning', 'data analysis']  # Example skills list
    for skill in skills:
        if skill.lower() in cv_text.lower():
            entities["SKILL"].append(skill)
    
    return entities


def apply_tfidf_cosine_similarity(cv_text, job_description):
    """Calculate cosine similarity using TF-IDF"""
    # Combine CV text and job description for comparison
    documents = [cv_text, job_description]
    
    # Vectorize the text using TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    # Compute the cosine similarity between the CV and job description
    similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)
    return similarity_matrix[0][1]  # Cosine similarity score between CV and job description
