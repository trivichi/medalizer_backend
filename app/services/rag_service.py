from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from typing import List, Dict
from pathlib import Path
from app.config import settings
import json

class RAGService:
    def __init__(self):
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize or load vector store
        self.vector_store = self._init_vector_store()
        
        # Medical knowledge base
        self.knowledge_base = self._load_knowledge_base()
    
    def _init_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            # Try to load existing vector store
            vector_store = Chroma(
                persist_directory=str(settings.CHROMA_PERSIST_DIR),
                embedding_function=self.embeddings
            )
            return vector_store
        except:
            # Create new vector store if none exists
            return Chroma(
                persist_directory=str(settings.CHROMA_PERSIST_DIR),
                embedding_function=self.embeddings
            )
    
    def _load_knowledge_base(self) -> Dict:
        """Load medical knowledge base"""
        knowledge_file = settings.KNOWLEDGE_BASE_DIR / "blood_tests_knowledge.json"
        
        if knowledge_file.exists():
            with open(knowledge_file, 'r') as f:
                return json.load(f)
        else:
            # Create default knowledge base
            default_knowledge = {
                'hemoglobin': {
                    'description': 'Hemoglobin is a protein in red blood cells that carries oxygen throughout the body.',
                    'low_causes': ['Anemia', 'Blood loss', 'Nutritional deficiency'],
                    'high_causes': ['Dehydration', 'Lung disease', 'Living at high altitude'],
                    'recommendations': {
                        'low': ['Increase iron-rich foods', 'Consider iron supplements', 'Consult a doctor'],
                        'high': ['Stay hydrated', 'Avoid smoking', 'Consult a doctor']
                    }
                },
                'wbc': {
                    'description': 'White blood cells help fight infections and are part of the immune system.',
                    'low_causes': ['Viral infections', 'Autoimmune disorders', 'Bone marrow problems'],
                    'high_causes': ['Infection', 'Inflammation', 'Leukemia'],
                    'recommendations': {
                        'low': ['Avoid infections', 'Maintain good hygiene', 'Consult a doctor'],
                        'high': ['Monitor for infection', 'Consult a doctor immediately']
                    }
                },
                'glucose': {
                    'description': 'Blood glucose levels indicate how much sugar is in your blood.',
                    'low_causes': ['Excessive insulin', 'Skipped meals', 'Excessive exercise'],
                    'high_causes': ['Diabetes', 'Insulin resistance', 'Stress'],
                    'recommendations': {
                        'low': ['Eat regular meals', 'Monitor blood sugar', 'Consult a doctor'],
                        'high': ['Reduce sugar intake', 'Exercise regularly', 'Monitor glucose', 'Consult a doctor']
                    }
                }
            }
            
            # Save default knowledge base
            knowledge_file.parent.mkdir(parents=True, exist_ok=True)
            with open(knowledge_file, 'w') as f:
                json.dump(default_knowledge, f, indent=2)
            
            return default_knowledge
    
    def add_documents_to_vector_store(self, documents: List[str]):
        """Add medical documents to vector store"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        docs = [Document(page_content=doc) for doc in documents]
        splits = text_splitter.split_documents(docs)
        
        self.vector_store.add_documents(splits)
        self.vector_store.persist()
    
    def get_relevant_context(self, query: str, k: int = 3) -> List[str]:
        """Retrieve relevant context from vector store"""
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        except:
            return []
    
    def generate_recommendations(self, metrics: List[Dict]) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []
        
        for metric in metrics:
            param_name = metric['name'].lower().replace(' ', '_')
            status = metric.get('status', 'normal')
            
            if status == 'normal':
                continue
            
            # Get knowledge for this parameter
            knowledge = self.knowledge_base.get(param_name, {})
            
            if knowledge:
                # Add description
                desc = knowledge.get('description', '')
                if desc:
                    recommendations.append(f"ℹ️ {metric['name']}: {desc}")
                
                # Add specific recommendations based on status
                recs = knowledge.get('recommendations', {}).get(status, [])
                for rec in recs:
                    recommendations.append(f"• {metric['name']} ({status}): {rec}")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("✓ All values appear to be within normal ranges.")
            recommendations.append("• Maintain a balanced diet and regular exercise.")
            recommendations.append("• Stay hydrated and get adequate sleep.")
        else:
            recommendations.append("• Follow up with your healthcare provider for personalized advice.")
        
        return recommendations
    
    def generate_summary(self, metrics: List[Dict]) -> str:
        """Generate a summary of the blood test results"""
        total = len(metrics)
        normal = sum(1 for m in metrics if m.get('status') == 'normal')
        low = sum(1 for m in metrics if m.get('status') == 'low')
        high = sum(1 for m in metrics if m.get('status') == 'high')
        
        if normal == total:
            return f"All {total} tested parameters are within normal ranges."
        else:
            issues = []
            if low > 0:
                issues.append(f"{low} parameter(s) below normal")
            if high > 0:
                issues.append(f"{high} parameter(s) above normal")
            
            issue_text = " and ".join(issues)
            return f"Out of {total} parameters tested, {normal} are normal. {issue_text.capitalize()}."