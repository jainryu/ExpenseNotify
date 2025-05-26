def read_prompt(prompt_file: str) -> str:
    with open(prompt_file, 'r') as file:
        prompt = file.read()
    
    return prompt