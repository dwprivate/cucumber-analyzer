import streamlit as st
import os
import json
import tiktoken
from openai import OpenAI
from pydantic import BaseModel
from models.cucumber_jvm import CucumberReport,CucumberReportSummary, summarize_element, summarize_cucumber_report
from io import StringIO
def evaluate_size(object: BaseModel) -> int:
    return len(object.model_dump().__str__()) 

def compute_openai_cost(usage, input_cost=0.15, output_cost = 0.6) :
    return usage.prompt_tokens * input_cost / 1_000_000 + usage.completion_tokens * output_cost / 1_000_000
st.title("Cucumber Report Analyzer")

def evaluate_token_size(input, model_name="o3-mini"):
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(str(input))
    return len(tokens)

uploaded_file = st.file_uploader(
    "Upload a document (.txt or .md)", type=("json")
)
if not uploaded_file:
    st.stop()

stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
string_data = stringio.read()

st.write("filename:", uploaded_file.name)
data = json.loads(string_data)
st.write(f"Nombre de features: {len(data)}")

report = CucumberReport.model_validate(data)
st.write(f"{evaluate_size(report)=:,} chars")

summary = summarize_cucumber_report(report, only_errors = True)
st.write(f"Features en échec: {len(summary.root)}")
st.write(f"{evaluate_size(summary)=:,} chars")
st.write(f"{evaluate_token_size(summary)} token")


st.divider()

# summary = CucumberReportSummary(summary.root[:20])
# st.write(len(summary.root))
# st.write(f"{evaluate_size(summary)=:,} chars")

# st.stop()
openai_api_key = st.secrets.openai_api_key
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Let the user upload a file via `st.file_uploader`.
    # uploaded_file = st.file_uploader(
    #     "Upload a document (.txt or .md)", type=("txt", "md")
    # )

    # Ask the user for a question via `st.text_area`.
    question = st.text_area(
        "Now ask a question about the document!",
        value = "Regroupe les scénarios par étapes en échec, analyse les erreurs les plus fréquentes et renvoie un rapport de test résumé permettant à l'équipe de développement d'avoir un statut complet sur l'état du système et les problèmes à résoudre en priorité ",
        disabled=not summary,
    )

    if summary and question:

        # Process the uploaded file and question.
        document = summary
        messages = [
            {
                "role": "user",
                #"content": f"Here's a document: {document} \n\n---\n\n {question}",
                "content": f"Voici un résumé d'un rapport de test Cucumber ne comprennant que les étapes en échec: {document} \n\n---\n\n {question}",
            }
        ]

        input_token = evaluate_token_size(messages)
        st.write(f"Le coût d'entrée estimé est de {input_token} tokens, soit {input_token*1.1/1_000_000:.4f} USD")
        st.write(f"Le coût de sortie moyen est de 3000 tokens, soit {3000*4.4/1_000_000:.4f} USD")

        # Generate an answer using the OpenAI API.
        # stream = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=messages,
        #     stream=True,
        # )
        # st.write_stream(stream)

        if st.button("Ask"):
            with st.spinner(show_time=True):
                response = client.chat.completions.create(
                    # model="gpt-4o-mini",
                    model="o3-mini",
                    messages=messages,
                    stream=False,
                )

                st.write(response.choices[0].message.content)
                st.write(response.usage)
                st.write(f"Cost: {compute_openai_cost(response.usage, 1.1, 4.4):.4f} USD")




