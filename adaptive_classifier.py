"""
Simplified Adaptive Classifier for AgenticSeek
This is a basic implementation to make the system functional
"""

import json
import os
from typing import List, Tuple, Dict, Any
import random

class AdaptiveClassifier:
    """
    Simplified adaptive classifier for AgenticSeek routing.
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.examples = []
        self.labels = []
        self.label_counts = {}
        
    @classmethod
    def from_pretrained(cls, path: str):
        """Load classifier from pretrained path."""
        classifier = cls(path)
        
        # Try to load examples if they exist
        examples_path = os.path.join(path, "examples.json")
        if os.path.exists(examples_path):
            with open(examples_path, 'r') as f:
                data = json.load(f)
                classifier.examples = data.get('examples', [])
                classifier.labels = data.get('labels', [])
        
        return classifier
    
    def add_examples(self, texts: List[str], labels: List[str]):
        """Add training examples."""
        self.examples.extend(texts)
        self.labels.extend(labels)
        
        # Count labels
        for label in labels:
            self.label_counts[label] = self.label_counts.get(label, 0) + 1
    
    def predict(self, text: str) -> List[Tuple[str, float]]:
        """
        Predict label for input text.
        Returns list of (label, confidence) tuples sorted by confidence.
        """
        if not self.examples:
            # Return default prediction if no examples
            return [("talk", 0.5)]
        
        # Simple similarity-based prediction
        text_lower = text.lower()
        text_words = set(text_lower.split())
        
        label_scores = {}
        
        # Compare with all examples
        for example, label in zip(self.examples, self.labels):
            example_words = set(example.lower().split())
            
            # Calculate word overlap similarity
            if len(text_words) == 0:
                similarity = 0.0
            else:
                overlap = len(text_words.intersection(example_words))
                similarity = overlap / max(len(text_words), len(example_words))
            
            # Accumulate scores by label
            if label not in label_scores:
                label_scores[label] = []
            label_scores[label].append(similarity)
        
        # Calculate average scores for each label
        final_scores = []
        for label, scores in label_scores.items():
            avg_score = sum(scores) / len(scores)
            
            # Add some randomness and bias based on label frequency
            label_frequency = self.label_counts.get(label, 1)
            frequency_bonus = min(0.1, label_frequency / sum(self.label_counts.values()))
            
            final_score = avg_score + frequency_bonus + random.uniform(-0.05, 0.05)
            final_scores.append((label, min(1.0, max(0.0, final_score))))
        
        # Sort by confidence (descending)
        final_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Ensure we always return at least one prediction
        if not final_scores:
            final_scores = [("talk", 0.5)]
        
        return final_scores
    
    def save(self, path: str):
        """Save classifier examples to file."""
        os.makedirs(path, exist_ok=True)
        examples_path = os.path.join(path, "examples.json")
        
        data = {
            'examples': self.examples,
            'labels': self.labels,
            'label_counts': self.label_counts
        }
        
        with open(examples_path, 'w') as f:
            json.dump(data, f, indent=2)

# For compatibility with the original router
def load_classifier(path: str):
    """Load classifier for compatibility."""
    return AdaptiveClassifier.from_pretrained(path)