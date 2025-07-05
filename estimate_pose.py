import pickle
import os
import sys
from google.generativeai import GenerativeModel
import json
import google.generativeai as genai
from pydantic import BaseModel
from plot_polygons import plot_polygons_with_heatmap, load_annotations
import matplotlib.pyplot as plt       

class ShopsSeen(BaseModel):
    shop_name: str

def call_gemini(image_part):
    model = genai.GenerativeModel('gemini-2.0-flash')
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    # Request Gemini to return structured JSON output
    response = model.generate_content(
        [
        {
            "role": "user",
            "parts": [
            {
                "text": (
                "List the names of the shops in the image as a JSON array of strings. "
                )
            },
            image_part
            ]
        }
        ],
        generation_config={
        "response_mime_type": "application/json",
        "response_schema": list[ShopsSeen],
        }
    )
    # Parse the JSON output
    try:
        shop_list = json.loads(response.text)
    except Exception:
        shop_list = response.text
    return shop_list

def normalize_shop_name(shop_name):
    """
    Normalize the shop name by removing 'shop:' prefix, converting to lowercase,
    and replacing '|' with an empty string.
    """
    return shop_name.replace("shop:", "").lower().replace("|", "").replace("/", "")

def detect_shops_in_image(image_path):
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")

    with open(image_path, 'rb') as f:
        image_contents = f.read()

    image_part = {
        "mime_type": "image/jpeg",
        "data": image_contents
    }

    # Call Gemini API to detect shops
    gemini_result = call_gemini(image_part)

    # Convert the result to a list of shop names

    return sorted([normalize_shop_name(item["shop_name"]) for item in gemini_result])

if __name__ == "__main__":
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Usage: python estimate_pose.py <image_path> [Optional:gemini_api_key]")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' does not exist.")
        sys.exit(1)

    detected_shops = tuple(detect_shops_in_image(image_path))
    print("Detected shops:", detected_shops)
   

    pickle_file_path = 'visible_shops.pickle'

    with open(pickle_file_path, 'rb') as f:
        data = pickle.load(f)

    cleaned_shops = {}
    for key in data.keys():
        cleaned_keys = []
        for shop in key:
            cleaned_keys.append(normalize_shop_name(shop))
        cleaned_key = tuple(sorted(cleaned_keys))
        cleaned_shops[cleaned_key] = data[key]

    if detected_shops in cleaned_shops:
        print(f"Shops {detected_shops} are visible in the pickle file.")
        #print("Corresponding data:", cleaned_shops[detected_shops])
        all_cx_cy = []
        for (cx, cy, a) in cleaned_shops[detected_shops]:
            all_cx_cy.append((cx, cy))
       
        all_shops = []
        for file_type, file_path in [("shop","example/annotations.shop.json")]:
            print(f"Loading {file_type} annotations from: {file_path}")
            annotations = load_annotations(file_path)
            
            # Add file type to annotations if not present
            for annotation in annotations:
                if 'type' not in annotation:
                    annotation['type'] = file_type

            # Remove all annotations of type 'corridor'
            annotations = [a for a in annotations if a.get('type') != 'corridor']
            all_shops.extend(annotations)
            print(f"Loaded {len(annotations)} {file_type} annotations")
    
        plot_polygons_with_heatmap(
            all_shops, 
            cleaned_shops[detected_shops],
            initial_particles=all_cx_cy,
            save_path="localization_probability.png"
        )