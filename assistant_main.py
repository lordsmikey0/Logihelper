from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from threading import Thread
import torch
import os
import log_generator as log
import assistant_preprocessing as preprocessing

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

tokenizer = None


def init_model(model_name):
    """
    Initialize the model from parameter model_name
    """
    global tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="cuda"
    )
    return model


def generate_answer(model, query_raw, stream=False):
    """
    Generate the answer to the question
    """
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    query, detected_terms = preprocessing.normalize_user_query(query_raw)
    print("[LOGS] Filtered user query:", query)
    extracted_context = preprocessing.get_from_guide(query, detected_terms)

    system_prompt = (
        f"""
        You are a helpful and experienced tutor in digital circuitry and Logisim - an educational program for circuit engineering training.
        Your main task is to explain complex concepts in digital circuitry theory and practice clearly. You know digital circuity and cybernetics ONLY.

        1. Use ONLY the provided English context.
        2. Answer in Russian, be friendly and short.
        3. If no context provided, say you don't know.
        
        TRANSLATION RULES:gi
        - West = Запад (слева)
        - East = Восток (справа)
        - South = Юг (снизу)
        - North = Север (сверху)
        
        CRITICAL RENDERING RULES:
        1. NEVER draw ASCII art diagrams, schematics, or text boxes like "+---+". 
        2. If the user asks "how to build/wire" ("как собрать/подключить"), explain it strictly using a numbered text list.
        3. Clearly state which wire goes to which side (West/South/East/North) based ONLY on the provided context.

        {extracted_context}"""
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt"
    ).to("cuda")

    generation_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=1024,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=True,
        temperature=0.1
    )

    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    if stream:
        def token_generator():
            for new_token in streamer:
                yield new_token

            thread.join()

        return token_generator()

    generated_text = ""
    for new_token in streamer:
        generated_text += new_token

    thread.join()
    return {"generated_text": generated_text, "system_prompt": system_prompt}


if __name__ == "__main__":
    query_raw = input()

    model_name = "Qwen/Qwen2.5-Coder-3B-Instruct"
    model = init_model(model_name)

    model_output = generate_answer(model, query_raw)

    # Generating logs for model
    log.generate_log(model_output["system_prompt"],
                     model_name,
                     query_raw,
                     model_output["generated_text"])

    print("[ASSISTANT]:", model_output["generated_text"])