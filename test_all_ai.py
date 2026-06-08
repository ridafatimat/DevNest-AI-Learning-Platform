import requests
import json

BASE_URL = "http://localhost:8000"

# Test data
test_user = "user-123"

# 1. Test Review Code
print("🧪 Testing reviewCode...")
review_data = {
    "submissionId": "test-review-001",
    "userId": test_user,
    "language": "python",
    "content": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total
"""
}
response = requests.post(f"{BASE_URL}/ai/review", json=review_data)
print("Review Result:", response.json())

# 2. Test Give Hint
print("\n💡 Testing giveHint...")
hint_data = {
    "submissionId": "test-hint-001", 
    "userId": test_user,
    "language": "python",
    "content": "How to reverse a string in Python?"
}
response = requests.post(f"{BASE_URL}/ai/hint", json=hint_data)
print("Hint Result:", response.json())

# 3. Test Explain Question
print("\n📚 Testing explainQuestion...")
explain_data = {
    "submissionId": "test-explain-001",
    "userId": test_user, 
    "language": "python",
    "content": "What is recursion and how does it work?"
}
response = requests.post(f"{BASE_URL}/ai/explain", json=explain_data)
print("Explanation Result:", response.json())

# 4. Test Study Plan
print("\n📅 Testing generateStudyPlan...")
study_data = {
    "submissionId": "test-study-001",
    "userId": test_user,
    "language": "python", 
    "content": "Machine Learning basics"
}
response = requests.post(f"{BASE_URL}/ai/studyplan", json=study_data)
print("Study Plan Result:", response.json())

# 5. Test Analytics
print("\n📊 Testing Analytics...")
response = requests.get(f"{BASE_URL}/analytics/user/{test_user}")
print("Analytics Result:", response.json())

print("\n🎉 All AI functions tested!")