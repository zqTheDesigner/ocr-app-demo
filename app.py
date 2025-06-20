import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import ast
from itertools import chain
from textwrap import wrap
import io

csv_data = None
original_image = None
annotated_image = None
boxes_visible = True  # default to show boxes

def load_csv(file):
    global csv_data
    # Load CSV into DataFrame
    csv_data = pd.read_csv(file.name)
    return csv_data

def draw_boxes_on_image(img, df, show_boxes=True):
    if not show_boxes or df is None or img is None:
        return img

    img = img.convert("RGBA")
    base = Image.new("RGBA", img.size, (0,0,0,0))  # Transparent layer
    draw = ImageDraw.Draw(base)

    # font = ImageFont.truetype("Helvetica.ttf", size=12)
    font = ImageFont.truetype('STHeiti Light.ttc', size=36)

    for _, row in df.iterrows():
        polygon = ast.literal_eval(row["polygon"])
        text_id = str(row.get("text_id", ""))
        text = str(row.get("text", ""))
        full_text = f"{text_id}\n{text}"

        # Calculate bounding box of the polygon
        xs, ys = zip(*polygon)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Estimate text size
        text_lines = list(full_text)
        line_height = 36
        text_block_height = line_height * len(text_lines)
        text_block_width = max(36 for line in text_lines)

        # Fit within polygon bounds
        text_x = min_x + 5
        text_y = min_y + 5

        # Background box (20% opacity white)
        bg_box = [text_x - 5, text_y - 2, text_x + text_block_width + 5, text_y + text_block_height + 2]
        draw.rectangle(bg_box, fill=(100, 255, 255, 64))

        # Draw text
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * line_height), line, fill=(0, 0, 0, 255), font=font)
            
        b_box = list(chain.from_iterable(polygon))
        # Draw polygon box outline
        draw.polygon(b_box, outline="red", width=2)

    return Image.alpha_composite(img, base)

def process_image(image):
    global original_image, csv_data, annotated_image, boxes_visible
    original_image = image
    annotated_image = draw_boxes_on_image(image, csv_data, show_boxes=boxes_visible)
    return annotated_image


def toggle_boxes():
    global boxes_visible, original_image, csv_data
    boxes_visible = not boxes_visible
    img = draw_boxes_on_image(original_image, csv_data, show_boxes=boxes_visible)
    return img

def update_csv(edited_df):
    global csv_data
    csv_data = edited_df
    return edited_df

def store_images(images):
    global image_storage
    image_storage = images  # store the list of images
    return f"{len(images)} image(s) stored."


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            image_input = gr.Image(label="Upload Image", type="pil")
            annotate_button = gr.Button("Annotate Text")
            toggle_button = gr.Button("Toggle Bounding Boxes")
        with gr.Column():
            csv_input = gr.File(label="Upload CSV File", file_types=['.csv'])
            table_output = gr.DataFrame(label="Editable CSV Table", interactive=True)
            save_button = gr.Button("Save CSV")
            
            def save_csv():
                file_path = "./tmp/output.csv"  # Temp file path
                csv_data.to_csv(file_path)
                return gr.File(value='./tmp/output.csv')


    image_display = gr.Image(label="Annotated Image", type="pil")

    csv_input.change(fn=load_csv, inputs=csv_input, outputs=table_output)
    annotate_button.click(fn=process_image, inputs=image_input, outputs=image_display)
    toggle_button.click(fn=toggle_boxes, outputs=image_display)
    table_output.change(fn=update_csv, inputs=table_output, outputs=table_output)
    save_button.click(fn=save_csv, outputs=csv_input)
demo.launch()