import os
import glob
import gradio as gr
from openai import OpenAI

openai_key = os.environ.get("OPENAI_API_KEY", None)
if not openai_key:
    raise RuntimeError("❌ Please set the OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=openai_key)

chapter_paths = sorted(glob.glob("chapter_*.txt") + glob.glob("Chapter_*.txt"))
if not chapter_paths:
    raise RuntimeError("❌ No files matching 'chapter_*.txt' or 'Chapter_*.txt' found.")

chapter_contexts = {}
for path in chapter_paths:
    with open(path, "r", encoding="utf-8") as f:
        chapter_contexts[os.path.basename(path)] = f.read()

def format_chat_prompt(user_message, history, max_convo_length=5):
    prompt = ""
    for (u, b) in history[-max_convo_length:]:
        prompt += f"User: {u}\nAssistant: {b}\n"
    prompt += f"User: {user_message}\nAssistant:"
    return prompt

def respond(user_message, chat_history, selected_chapter):
    chapter_text = chapter_contexts.get(selected_chapter, "")
    if not chapter_text:
        return "", chat_history

    system_msg = (
        "You are a reflective reading assistant. Only use the chapter below to answer.\n"
        "Help the user reflect deeply, make connections to life, think critically, and explore key ideas.\n"
        "Do not use any external knowledge. If unsure or irrelevant, respond: 'I don't know.'\n\n"
        f"Chapter Context:\n{chapter_text}"
    )
    prompt_text = format_chat_prompt(user_message, chat_history)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt_text}
        ]
    )

    assistant_reply = response.choices[0].message.content.strip()
    chat_history.append((user_message, assistant_reply))
    return "", chat_history

css = """
/* Container around everything */
#container {
  background-color: white;
  border: 2px solid #4B2E83;  /* NYU purple */
  border-radius: 8px;
  padding: 16px;
  max-width: 800px;
  margin: auto;
}

/* Center the logo */
#logo img {
  object-fit: contain;
  max-width: 300px;
  display: block;
  margin-left: auto;
  margin-right: auto;
}

/* Title styling */
#title {
  color: #000000;
  text-align: center;
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 12px;
}

/* Dropdown styling */
#chapter_selector {
  border: 2px solid #4B2E83;
  border-radius: 6px;
  margin-bottom: 12px;
}

/* Chatbot area wrapper */
#chatbot {
  background-color: #F9F9FB;
  border: 2px solid #4B2E83;
  border-radius: 6px;
  padding: 8px;
  height: 400px;        /* same as height=400 above */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* iMessage‐style user bubble (right‐aligned) */
.chatbot .chatbot-message.user {
  align-self: flex-end;
  background-color: #EDE5F8;   /* very light purple */
  color: #000000;
  border-radius: 20px 20px 5px 20px;
  padding: 8px 12px;
  margin: 4px 8px;
  max-width: 70%;
  word-wrap: break-word;
}

/* iMessage‐style assistant bubble (left‐aligned) */
.chatbot .chatbot-message.assistant {
  align-self: flex-start;
  background-color: #4B2E83;   /* deep NYU purple */
  color: #FFFFFF;
  border-radius: 20px 20px 20px 5px;
  padding: 8px 12px;
  margin: 4px 8px;
  max-width: 70%;
  word-wrap: break-word;
}

/* Input textbox styling */
#textbox textarea {
  border: 2px solid #4B2E83;
  border-radius: 6px;
  background-color: #FFFFFF;
}

/* Buttons styling */
#submit_btn, #clear_btn {
  background-color: #4B2E83;
  color: white;
  border: none;
  border-radius: 6px;
  margin-top: 8px;
  padding: 8px 16px;
  font-size: 14px;
}

/* Hover effect for buttons */
#submit_btn:hover, #clear_btn:hover {
  background-color: #5C3F9E;
}
"""

# ─── 6) Build the Gradio interface ───
with gr.Blocks(css=css) as demo:
    with gr.Column(elem_id="container"):
        # Display the NYU logo (use "value" instead of "source")
        gr.Image(value="NYU_Logo.png", elem_id="logo", interactive=False)

        # Title
        gr.Markdown(
            "### Reflective Chatbot for **The Power of Us**",
            elem_id="title"
        )

        # Chapter dropdown
        chapter_selector = gr.Dropdown(
            choices=chapter_paths,
            value=chapter_paths[0],
            label="Choose Chapter",
            elem_id="chapter_selector"
        )

        # Chatbot display (wrapped in a div with id="chatbot")
        chatbot = gr.Chatbot(
            value=[],
            label=None,      # we’re not using a label here
            elem_id="chatbot",
            container=False  # disable Gradio’s default container so our CSS applies
        )

        # User input textbox
        msg = gr.Textbox(
            placeholder="Type your reflection question here…",
            label="Your question",
            elem_id="textbox"
        )

        # Buttons
        submit_btn = gr.Button("Submit", elem_id="submit_btn")
        clear_btn = gr.ClearButton(
            components=[msg, chatbot],
            value="Clear",
            elem_id="clear_btn"
        )

        # Wire up the response
        submit_btn.click(
            respond,
            inputs=[msg, chatbot, chapter_selector],
            outputs=[msg, chatbot]
        )
        msg.submit(
            respond,
            inputs=[msg, chatbot, chapter_selector],
            outputs=[msg, chatbot]
        )

    demo.launch()
