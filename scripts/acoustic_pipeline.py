# scripts/acoustic_pipeline.py

from scripts.llm_calls import extract_variables, build_answer
from scripts.sql_calls import query_or_recommend
from utils.format_interpreter import standardize_input

def run_pipeline(user_input: dict, user_question: str = "") -> dict:
    """
    Given structured user_input, run the full acoustic pipeline.
    Returns a dict with both raw results and LLM summary.
    """
    user_input = standardize_input(user_input)
    result = query_or_recommend(user_input)

    try:
        summary = build_answer(user_question or str(user_input), result)
    except Exception as e:
        summary = f"[LLM Summary Error] {e}"

    return {
        "input": user_input,
        "result": result,
        "summary": summary
    }

def run_from_free_text(question: str) -> dict:
    """
    Alternative entry: run the pipeline from a free-form LLM question.
    """
    user_input = extract_variables(question)
    if not user_input:
        return {"error": "Could not extract parameters from question."}
    return run_pipeline(user_input, question)

def run_from_free_text(question):
    extracted = extract_variables(question)
    if not extracted:
        return {"error": "Both zone and apartment_type are required"}
    
    user_input = standardize_input(extracted)
    result = query_or_recommend(user_input)

    summary = build_answer(question, result)
    return {"summary": summary}