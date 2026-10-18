# Final Submission Guide - Milestone 4

## 📦 What You're Submitting

For Milestone 4 (Due: 30.01.2025), you need to submit:

1. **Docker Container** - Complete voice assistant in a Docker image
2. **Evaluation Report** - Max 2 pages + title sheet with team members

---

## ✅ Pre-Submission Checklist

### 1. Code Completion
- [ ] All 7 required commands work
- [ ] Weather API integration complete
- [ ] Calendar API CRUD operations complete
- [ ] Conversation history tracking works
- [ ] Context resolution (references to "there", "previously") works

### 2. Docker Container
- [ ] Dockerfile builds successfully
- [ ] Container runs in text mode
- [ ] Unique calendar ID configured for your team
- [ ] All tests pass inside container
- [ ] Image size is reasonable (<5GB)

### 3. Documentation
- [ ] README.md updated with team member details
- [ ] Evaluation report completed (2 pages + title)
- [ ] All team members listed with matriculation IDs

### 4. Testing
- [ ] Run `python test_commands.py` - all tests pass
- [ ] Run `docker build -t voice-assistant .` - builds successfully
- [ ] Run `docker run -it voice-assistant` - starts correctly
- [ ] Test all 7 required commands manually

---

## 🐳 Docker Container Submission

### Step 1: Build the Final Container

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"

# Build with your team's calendar ID
docker build -t voice-assistant:final .
```

### Step 2: Test the Container

```bash
# Run in interactive mode
docker run -it voice-assistant:final

# Test with sample commands
# You: What will the weather be like today in Marburg?
# You: Where is my next appointment?
# You: exit
```

### Step 3: Export the Container

```bash
# Save to a tar file
docker save voice-assistant:final > voice-assistant-team-NAME.tar

# Compress it (optional, reduces size)
gzip voice-assistant-team-NAME.tar
```

### Step 4: Verify Export

```bash
# Check file size
ls -lh voice-assistant-team-NAME.tar.gz

# Expected size: 1-2 GB compressed
```

---

## 📝 Evaluation Report

### Structure

**Page 1: Title Sheet**
```
Voice Assistant Evaluation Report
Natural Language Systems - Winter Semester 2025

Team Members:
- Name 1 (Matriculation ID: XXXXXXXX)
- Name 2 (Matriculation ID: XXXXXXXX)
- Name 3 (Matriculation ID: XXXXXXXX)
- Name 4 (Matriculation ID: XXXXXXXX)

Date: [Submission Date]
```

**Pages 2-3: Evaluation Content** (Max 2 pages)

Use the template in `evaluation_report_template.md` and fill in:

1. **System Overview** (0.5 pages)
   - Architecture description
   - Technologies used
   - Design decisions

2. **Evaluation Methodology** (0.5 pages)
   - How you evaluated the system
   - Metrics used (accuracy, F1-score, task completion rate, etc.)
   - Test dataset description

3. **Results** (0.5 pages)
   - Intent recognition accuracy
   - Entity extraction performance
   - Task completion rates
   - Example successes and failures

4. **Error Analysis & Conclusions** (0.5 pages)
   - Common errors
   - Limitations
   - Future improvements
   - Lessons learned

### Tips for Evaluation

**1. Create a Test Dataset**
```python
test_commands = [
    "What will the weather be like today in Marburg?",
    "What will the weather be on Friday in Frankfurt?",
    "Will it rain there on Saturday?",
    "Where is my next appointment?",
    "Add an appointment titled Meeting for tomorrow.",
    "Delete the previously created appointment.",
    "Change the location for my appointment tomorrow.",
    # Add 10-20 more varied commands
]
```

**2. Run Automated Tests**
```bash
# Inside Docker
docker run voice-assistant python test_commands.py

# Or locally
python test_commands.py
```

**3. Manual Testing**
- Test each of the 7 required commands
- Test edge cases (unknown locations, invalid dates, etc.)
- Test context resolution ("there", "that", "previously")
- Document successes and failures

**4. Calculate Metrics**
- **Intent Accuracy**: Correct intents / Total commands
- **Entity F1**: Precision and recall for entities
- **Task Completion**: Successfully completed / Total tasks
- **Context Resolution**: Correctly resolved references / Total references

---

## 🚀 Submission Steps

### 1. Update Team Information

Edit [README.md](README.md) lines 172-178:
```markdown
## Team Members

- Alice Smith (Matriculation ID: 12345678)
- Bob Jones (Matriculation ID: 23456789)
- Carol White (Matriculation ID: 34567890)
- David Brown (Matriculation ID: 45678901)
```

### 2. Set Unique Calendar ID

Edit [modules/calendar_api.py](modules/calendar_api.py) line 15:
```python
def __init__(self, api_url="...", calenderid="team_YOUR_NAME_2026"):
```

Or use environment variable/command line argument.

### 3. Run Final Tests

```bash
# Test locally
python test_commands.py

# Test in Docker
docker build -t voice-assistant:final .
docker run voice-assistant:final python test_commands.py
```

### 4. Complete Evaluation Report

Use the template:
```bash
cp evaluation_report_template.md evaluation_report_FINAL.md
# Edit evaluation_report_FINAL.md with your results
```

Convert to PDF:
```bash
# Using pandoc (if installed)
pandoc evaluation_report_FINAL.md -o evaluation_report.pdf

# Or use an online converter
# Or copy content to Word/Google Docs and export as PDF
```

### 5. Package Everything

Create a submission folder:
```bash
mkdir submission
cp evaluation_report.pdf submission/
docker save voice-assistant:final | gzip > submission/voice-assistant.tar.gz
```

### 6. Submit

Follow your course's submission guidelines:
- Upload Docker image (tar.gz file)
- Upload evaluation report (PDF)
- Include any additional documentation requested

---

## 🔍 Quality Checks

Before submitting, verify:

### Docker Container
```bash
# Build fresh
docker build --no-cache -t voice-assistant:final .

# Run and test
docker run -it voice-assistant:final
```

Inside the container, test:
```
You: What's the weather in Marburg today?
You: Add an appointment titled Test for tomorrow.
You: Delete the previously created appointment.
You: exit
```

### Documentation
- [ ] README has team member names and IDs
- [ ] All 7 required commands documented
- [ ] Calendar ID is unique
- [ ] Evaluation report is 2 pages + title
- [ ] Report includes metrics and analysis

### Code Quality
- [ ] No hardcoded credentials
- [ ] No print debugging statements
- [ ] Clean, commented code
- [ ] All modules work independently

---

## 📊 Example Evaluation Metrics

Here are example metrics you might include:

**Intent Recognition**:
- weather_query: 93% accuracy (14/15)
- get_appointment: 90% accuracy (9/10)
- create_appointment: 80% accuracy (8/10)
- update_appointment: 75% accuracy (6/8)
- delete_appointment: 100% accuracy (7/7)
- **Overall: 88% accuracy** (44/50)

**Entity Extraction**:
- Place: 92% F1 (Precision: 95%, Recall: 90%)
- Day/Date: 87% F1 (Precision: 88%, Recall: 85%)
- Title: 87% F1 (Precision: 85%, Recall: 90%)

**Task Completion**:
- Weather queries: 93% (14/15)
- Appointment operations: 83% (30/36)
- **Overall: 88% task completion**

**Context Resolution**:
- Anaphoric references: 80% (8/10)
- Previous turn references: 85% (11/13)

---

## 🆘 Common Issues & Solutions

### Issue: Docker build fails
**Solution**: Check internet connection, try `--no-cache`:
```bash
docker build --no-cache -t voice-assistant:final .
```

### Issue: Tests fail in Docker but work locally
**Solution**: Ensure all files are copied to Docker:
```bash
# Check .dockerignore doesn't exclude needed files
cat .dockerignore
```

### Issue: Calendar API conflicts with other teams
**Solution**: Use a unique calendar ID:
```bash
docker run -it voice-assistant:final python main.py --text --calendar-id team_YOUR_UNIQUE_NAME_2025
```

### Issue: Evaluation report is too long
**Solution**: Be concise, use bullet points, remove unnecessary details

---

## 📅 Timeline

**2 Weeks Before Deadline**:
- [ ] Complete all code
- [ ] Run comprehensive tests
- [ ] Start evaluation report

**1 Week Before Deadline**:
- [ ] Finalize Docker container
- [ ] Complete evaluation with metrics
- [ ] Review everything

**3 Days Before Deadline**:
- [ ] Final testing
- [ ] Proofread evaluation report
- [ ] Export Docker image

**Submission Day**:
- [ ] Upload files
- [ ] Verify submission
- [ ] Celebrate! 🎉

---

## 🎯 Success Criteria

Your submission should demonstrate:

1. **Functionality**: All requirements met
2. **Quality**: Clean, well-documented code
3. **Analysis**: Thoughtful evaluation with metrics
4. **Professionalism**: Complete documentation
5. **Reproducibility**: Docker container works everywhere

---

**Good luck with your submission!** 🚀

For questions, check:
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Detailed usage
- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Docker specifics
- [IMPLEMENTATION_DETAILS.md](IMPLEMENTATION_DETAILS.md) - Technical details
