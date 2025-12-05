import json
import random
import uuid
import os
from datetime import datetime, timedelta
from faker import Faker
from src.config import DATA_DIR, DATA_FILE

fake = Faker()

# Configuration
NUM_ISSUES = 50
NUM_COMPONENTS = 10
NUM_PRODUCTS = 5
NUM_PEOPLE = 20
NUM_LABELS = 10
NUM_CHANNELS = 5
OUTPUT_FILE = DATA_FILE

# Enums / Constants
ISSUE_TYPES = ["Incident", "Bug", "Task", "Story"]
STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
RESOLUTIONS = ["Fixed", "Won't Fix", "Duplicate", "Cannot Reproduce", "Done"]
SEVERITIES = ["Sev1", "Sev2", "Sev3", "Sev4"]
IMPACTS = ["High", "Medium", "Low"]
ENV_TYPES = ["Production", "Staging", "Test", "Dev"]

def generate_reference_data():
    components = [{"name": f"Component-{i}", "id": str(uuid.uuid4())} for i in range(NUM_COMPONENTS)]
    products = [{"name": f"Product-{i}", "id": str(uuid.uuid4())} for i in range(NUM_PRODUCTS)]
    categories = [{"name": f"Category-{i}", "id": str(uuid.uuid4())} for i in range(5)]
    people = [{"display_name": fake.name(), "email": fake.email(), "account_id": str(uuid.uuid4())} for _ in range(NUM_PEOPLE)]
    labels = [{"name": word, "id": str(uuid.uuid4())} for word in fake.words(nb=NUM_LABELS, unique=True)]
    slack_channels = [{"url": f"https://slack.com/archives/{fake.bothify(text='C##########')}", "id": str(uuid.uuid4())} for _ in range(NUM_CHANNELS)]
    
    return components, products, categories, people, labels, slack_channels

def generate_issue(components, products, categories, people, labels, slack_channels):
    created_dt = fake.date_time_between(start_date="-1y", end_date="now")
    updated_dt = created_dt + timedelta(days=random.randint(0, 30))
    event_start = created_dt + timedelta(minutes=random.randint(0, 60))
    event_end = event_start + timedelta(minutes=random.randint(10, 300))
    duration_ms = int((event_end - event_start).total_seconds() * 1000)
    
    issue_id = str(uuid.uuid4())
    key = f"INC-{fake.unique.random_int(min=1000, max=9999)}"
    
    issue = {
        "id": issue_id,
        "key": key,
        "type": random.choice(ISSUE_TYPES),
        "status": random.choice(STATUSES),
        "resolution": random.choice(RESOLUTIONS) if random.random() > 0.3 else None,
        "severity": random.choice(SEVERITIES),
        "impact": random.choice(IMPACTS),
        "env_type": random.choice(ENV_TYPES),
        "customer_env": fake.company(),
        "event_start": event_start.isoformat(),
        "event_end": event_end.isoformat(),
        "event_duration_ms": duration_ms,
        "summary": fake.sentence(nb_words=10),
        "created": created_dt.isoformat(),
        "updated": updated_dt.isoformat(),
        "url": f"https://aconex.oracle.com/issue/{key}",
        
        # Relationships
        "components": random.sample(components, k=random.randint(1, 2)),
        "product": random.choice(products),
        "category": random.choice(categories),
        "reporter": random.choice(people),
        "assignee": random.choice(people),
        "labels": random.sample(labels, k=random.randint(0, 3)),
        "slack_channel": random.choice(slack_channels) if random.random() > 0.5 else None,
        "passages": []
    }
    
    # Generate Passages (for RAG)
    num_passages = random.randint(1, 3)
    for _ in range(num_passages):
        passage = {
            "id": str(uuid.uuid4()),
            "source_type": "Jira Comment",
            "source_id": str(uuid.uuid4()),
            "text": fake.paragraph(nb_sentences=3),
            "created": (created_dt + timedelta(minutes=random.randint(1, 100))).isoformat(),
            "url": issue["url"]
        }
        issue["passages"].append(passage)
        
    return issue

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    components, products, categories, people, labels, slack_channels = generate_reference_data()
    
    issues = []
    for _ in range(NUM_ISSUES):
        issues.append(generate_issue(components, products, categories, people, labels, slack_channels))
        
    # Add some links between issues
    for issue in issues:
        if random.random() > 0.8:
            target = random.choice(issues)
            if target["id"] != issue["id"]:
                issue["clones"] = target["key"] # Simple link for now
                
    with open(OUTPUT_FILE, "w") as f:
        json.dump(issues, f, indent=2)
        
    print(f"Generated {len(issues)} issues in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
