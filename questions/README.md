# Questions Management

## CSV Upload Format

Upload questions in bulk using a CSV file with the following columns:

### Required Columns:
- `question_text` - The question text
- `question_type` - Either "single" or "multiple"
- `options` - Pipe-separated options (e.g., "Option A|Option B|Option C|Option D")
- `correct_answers` - Comma-separated correct answers (e.g., "Option A" or "Option A,Option B")
- `explanation` - Explanation for the correct answer
- `marks` - Number of marks (default: 1)
- `tags` - Comma-separated tags (e.g., "aws,cloud,architecture")

### Example CSV:

```csv
question_text,question_type,options,correct_answers,explanation,marks,tags
"What is AWS?","single","Amazon Web Services|A cloud platform|A database|A programming language","Amazon Web Services","AWS stands for Amazon Web Services, a comprehensive cloud computing platform.",1,"aws,cloud"
"Select cloud providers","multiple","AWS|Azure|Google Cloud|Oracle|IBM Cloud","AWS,Azure,Google Cloud","Major cloud providers include AWS, Azure, and Google Cloud.",1,"cloud,providers"
```

### Notes:
- Use quotes around text containing commas
- Options are separated by pipe (|) character
- Multiple correct answers are separated by commas
- Tags are separated by commas

