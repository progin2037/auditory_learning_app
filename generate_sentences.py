import torch
import transformers
import re
import pickle
import pandas as pd
from tqdm import tqdm


def generate_words(model_name: str,
                   torch_dtype: torch.dtype,
                   n_words: int,
                   level: str,
                   save_output: bool) -> list:
    """
    Generate English words for the selected CEFR level using specified model.

    Args:
        model_name (str): Hugging Face model name
        torch_dtype (torch.dtype): Dtype of parameters in inference
        n_words (int): Number of words to generate
        level (str): CEFR level for words to generate
        save_output (bool): Save generated words to pickle (True) or not (False)
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
        Generating more than {n_words} is strictly forbidden.
        The generated words should be diverse.
        Don't use words from CEFR levels lower than {level}.
        Use different parts of speech.
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


def generate_sentences(model_name: str,
                       torch_dtype: torch.dtype,
                       generated_words: list,
                       n_sentences: int,
                       max_words_per_sen: int,
                       level_sen: str,
                       save_output: bool) -> pd.DataFrame:
    """
    Generate sentences containing provided words for the selected CEFR level using specified model.

    Args:
        model_name (str): Hugging Face model name
        torch_dtype (torch.dtype): Dtype of parameters in inference
        generated_words (list): A list of generated words
        n_sentences (int): Number of sentences to generate
        max_words_per_sen (int): Maximum number of words per sentence
        level_sen (str): CEFR level for sentences to generate
        save_output (bool): Save generated sentences to pickle (True) or not (False)
    Returns:
        sentences_df (pd.DataFrame): A DataFrame with generated words and sentences
    """
    # Initialize a list of words with examples of sentences
    words_sentences = []
    # Initialize inference pipeline for the specified model
    pipeline = transformers.pipeline(
        "text-generation",
        model=model_name,
        model_kwargs={"torch_dtype": torch_dtype},
        device="cuda"
    )
    # Iterate over different words
    for word in tqdm(generated_words):
        # Generate system and user prompts
        messages = [
            {"role": "system", "content": "You are a helpful assistant. You have to strictly follow the instructions."},
            {"role": "user", "content": f"""
            Create {n_sentences} full sentences using phrase {word}. {word} MUST be always used in the sentence.
            The sentences should be diverse. Try to use different vocabulary for each sentence.
            They should be optimal for using auditory learning techniques.
            Remember that phrase {word} is the most important. Other words are used only to create full sentences.
            Generated sentences must be logical - they will be used for learning English!
            The sentences should be adequate for {level_sen} CEFR level.
            Try to use commonly used vocabulary.
            Use no more than {max_words_per_sen} words per sentence.
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
            max_new_tokens=256,
            do_sample=True,
            temperature=1.0,
            top_p=0.95,
            pad_token_id=pipeline.tokenizer.eos_token_id
        )
        # Keep only newly generated text from the output
        output = outputs[0]["generated_text"][len(prompt):]
        # Capture only generated sentences
        output = re.findall('(?:\d\.\s*)(.*)(?:\s*)', output, re.IGNORECASE)
        # Append row to the list
        words_sentences.append([word] + [x for x in output])
    sentences_df = pd.DataFrame(words_sentences, columns=['word', 'sentence_1', 'sentence_2', 'sentence_3'])
    if save_output:
        sentences_df.to_pickle('words_with_sentences.pkl')
    return sentences_df


MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
TORCH_DTYPE = torch.bfloat16
N_WORDS = 300
N_SENTENCES = 3
MAX_WORDS_PER_SEN = 7
LEVEL = 'B1'
LEVEL_SEN = 'B1'

SAVE_OUTPUT = True

print('Generating words...')
words = generate_words(model_name=MODEL_NAME,
                       torch_dtype=TORCH_DTYPE,
                       n_words=N_WORDS,
                       level=LEVEL,
                       save_output=SAVE_OUTPUT)

print('Generating sentences...')
words_with_sentences = generate_sentences(model_name=MODEL_NAME,
                                          torch_dtype=TORCH_DTYPE,
                                          generated_words=words,
                                          n_sentences=N_SENTENCES,
                                          max_words_per_sen=MAX_WORDS_PER_SEN,
                                          level_sen=LEVEL_SEN,
                                          save_output=SAVE_OUTPUT)
