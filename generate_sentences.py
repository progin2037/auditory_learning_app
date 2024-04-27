import torch
import transformers
import re
import pickle


def generate_words(model_name: str,
                   torch_dtype: torch.dtype,
                   n_words: int,
                   level: str,
                   save_output: bool) -> list:
    """
    Generate English words for the selected CEFR level using
    specified model.

    Args:
        model_name (str): Hugging Face model name
        torch_dtype (torch.dtype): Dtype of parameters in inference
        n_words (int): Number of words to generate
        level (str): CEFR level for generated words
        save_output (bool): Save generated words (True) or not (False)
    Returns:
        generated_words_list (list): A list of generated words
    """
    # Initialize inference pipeline for the specified model
    pipeline = transformers.pipeline(
        "text-generation",
        model=model_name,
        model_kwargs={"torch_dtype": torch_dtype},
        device="cuda"
    )
    # Generate system and user prompts
    messages = [
        {"role": "system", "content": "You are a helpful assistant. You have to strictly follow the instructions."},
        {"role": "user", "content": f"""
        Generate top {n_words} most commonly used words in everyday life intended for {level} CEFR level.
        The generated words should be diverse.
        Don't use words from CEFR levels lower than {level}.
        Use different parts of speech, including adjectives.
        You have to print all the generated words.
        Don't create words alphabetically.
        """}]
    # Apply chat template
    prompt = pipeline.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    # Get LLM output
    outputs = pipeline(
        prompt,
        max_new_tokens=10000,
        do_sample=False,
        repetition_penalty=1.2  # Enough to not repeat the same words
    )
    # Keep only newly generated text from the output
    generated_words = outputs[0]["generated_text"][len(prompt):]
    # Capture only generated words.
    # The generated words should be listed numerically.
    # Get ([digit][.][0 or more spaces])([0 or more characters])([0 or more whitespaces]).
    # The 1st and the 3rd group aren't captured, so only generated words remain in the output
    generated_words_list = re.findall('(?:\d\.\s*)(.*)(?:\s*)', generated_words, re.IGNORECASE)
    # Lowercase generated words
    generated_words_list = [x.lower() for x in generated_words_list]
    # Save generated words
    if save_output:
        with open("generated_words", "wb") as fp:
            pickle.dump(generated_words_list, fp)
    return generated_words_list


MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
TORCH_DTYPE = torch.bfloat16
N_WORDS = 200
LEVEL = 'C1'
SAVE_OUTPUT = True

words = generate_words(model_name=MODEL_NAME,
                       torch_dtype=TORCH_DTYPE,
                       n_words=N_WORDS,
                       level=LEVEL,
                       save_output=SAVE_OUTPUT)
