import json


def read_file_lines(filepath, start=0, limit=None):
    with open(filepath, 'r') as file:
        lines = file.readlines()
        if limit:
            return [line.strip() for line in lines[start:start + limit]]
        return [line.strip() for line in lines[start:]]


def create_jsonl_entry(record, is_correct):
    return {"messages": [{"role": "system", "content": "Verify the result"}, {"role": "user", "content": record},
                         {"role": "assistant", "content": "CORRECT" if is_correct else "INCORRECT"}]}


def write_jsonl(filename, correct_records, incorrect_records):
    with open(filename, 'w') as outfile:
        # Process correct records
        for record in correct_records:
            jsonl_entry = create_jsonl_entry(record, True)
            outfile.write(json.dumps(jsonl_entry) + '\n')

        # Process incorrect records
        for record in incorrect_records:
            jsonl_entry = create_jsonl_entry(record, False)
            outfile.write(json.dumps(jsonl_entry) + '\n')


# Process training data (first 150 records)
training_correct = read_file_lines('Lab Data S04E02/correct.txt', start=0, limit=192)
training_incorrect = read_file_lines('Lab Data S04E02/incorrect.txt', start=0, limit=192)
write_jsonl('training_output.jsonl', training_correct, training_incorrect)

# Process verification data (records 150-190)
verify_correct = read_file_lines('Lab Data S04E02/correct.txt', start=150, limit=40)
verify_incorrect = read_file_lines('Lab Data S04E02/incorrect.txt', start=150, limit=40)
write_jsonl('verify_output.jsonl', verify_correct, verify_incorrect)
