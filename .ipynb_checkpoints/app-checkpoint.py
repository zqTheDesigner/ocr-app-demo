import gradio as gr

with gr.Blocks() as demo:
    with gr.Row() as row:
        gr.Text('test')

demo.launch()