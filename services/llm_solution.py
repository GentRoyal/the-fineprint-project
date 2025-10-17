from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from prompts.all_prompts import harmful_prompt

import os
from dotenv import load_dotenv
load_dotenv()   

class HarmfulClause(BaseModel):
    id: int
    clause_text: str
    reason: str
    severity: str

class HarmfulClauses(BaseModel):
    clauses: list[HarmfulClause]

def harmful_clause_analysis():
    system_prompt = harmful_prompt()

    prompt = ChatPromptTemplate.from_template(system_prompt)

    model = ChatGroq(
        model=os.getenv("GROQ_MODEL"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7
    )

    chain = prompt | model.with_structured_output(HarmfulClauses)

    return chain