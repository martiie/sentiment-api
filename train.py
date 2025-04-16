import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score
import joblib

# Load data
df = pd.read_csv("data/reviews.csv")
X = df['review_text']
y = df['sentiment'].map({'positive': 1, 'negative': 0})

# Text vectorization
vectorizer = TfidfVectorizer(max_features=1000)
X_vec = vectorizer.fit_transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)

# Models to compare
models = {
    "Logistic Regression": LogisticRegression(),
    "Naive Bayes": MultinomialNB(),
    "Linear SVC": LinearSVC()
}

# Train and evaluate
best_model = None
best_accuracy = 0
best_model_name = ""

for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"{name} Accuracy: {acc:.4f}")
    if acc > best_accuracy:
        best_accuracy = acc
        best_model = model
        best_model_name = name

# Save best model
joblib.dump((best_model, vectorizer), "sentiment_model.pkl")
print(f"\n✅ Best model saved: {best_model_name} (Accuracy: {best_accuracy:.4f})")
