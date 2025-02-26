import streamlit as st
from transformers import T5ForConditionalGeneration, T5Tokenizer
import PyPDF2

@st.cache_resource
def load_model():
    try:
        model_name = "t5-small"
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
        return tokenizer, model
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None, None

tokenizer, model = load_model()

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("AI-Powered Chat Summarization")
st.write("Upload a .txt or .pdf file, or paste chat text below to get a summary.")

with st.form("chat_form"):
    text_input = st.text_area("Enter your chat text:")
    uploaded_file = st.file_uploader("Or upload a file (.txt or .pdf)", type=["txt", "pdf"])
    submit_button = st.form_submit_button("Summarize")

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except PyPDF2.errors.PdfReadError:
        st.error("Error reading PDF file. It might be corrupted or encrypted.")
        return None
    except Exception as e:
        st.error(f"Unexpected error processing PDF: {str(e)}")
        return None

if submit_button and (text_input.strip() or uploaded_file):
    input_text = ""
    
    if uploaded_file is not None:
        if uploaded_file.type == "text/plain":
            try:
                input_text = uploaded_file.getvalue().decode("utf-8")
            except UnicodeDecodeError:
                st.error("Error decoding text file. Please ensure it's UTF-8 encoded.")
        elif uploaded_file.type == "application/pdf":
            input_text = extract_text_from_pdf(uploaded_file)
            if input_text is None:
                input_text = ""
    else:
        input_text = text_input.strip()

    if not input_text:
        st.warning("No text found in the provided input. Please check your file or input.")
    else:
        # Truncate text to 512 tokens as per model limitation
        truncated_text = ' '.join(input_text.split()[:500])
        st.session_state.chat_history.append({"role": "user", "message": input_text})
        
        with st.spinner("Generating summary..."):
            try:
                input_prompt = "summarize: " + truncated_text
                inputs = tokenizer.encode(
                    input_prompt,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True
                )
                
                summary_ids = model.generate(
                    inputs,
                    max_length=150,
                    min_length=30,
                    length_penalty=2.0,
                    num_beams=4,
                    early_stopping=True
                )
                summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                st.session_state.chat_history.append({"role": "assistant", "message": summary})
            except Exception as e:
                st.error(f"Error generating summary: {str(e)}")

elif submit_button:
    st.warning("Please provide some text or upload a file.")

# Display chat history
st.markdown("### Chat History")
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        with st.expander("Original Text (Click to expand)"):
            st.write(chat['message'])
    else:
        st.markdown(f"**AI Summary:** {chat['message']}")

# Add clear button
if st.button("Clear History"):
    st.session_state.chat_history = []