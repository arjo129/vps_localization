# Indoor Localization in An Era of Software 3.0

> **Disclaimer:**  
> This project was completed entirely on personal time and hardware. It is not 
> affiliated with, endorsed by, or representative of any institutions
> or organizations with which I am affiliated. The views and opinions expressed herein 
> are solely my own and do not represent those of my employer or any associated institutions.

LLMs and VLMs have been eating the world. Last week I decided to listen to a talk by
Andrej Kaparthy on his view of "software 3.0". Unlike the two extreme views which I seem to be
surrounded by, Andrej's talk actually is very optimistic without ignoring the pitfalls of LLMs.
This brought me back to the time that I took on my first paid gig in 2014. I was then in High School,
I had recently released a small arduino library that was doing waves. Between the recruiter mail and
all the noise, I found myself doing some freelance work before I recieved my call up for national service. 
My first customer wanted an "indoor location system" based on the use of BLE beacons. I charged the measly
sum of $500 (not knowing that I probably could have added 2 zeros to it if I had some business sense).
It was arelatively simple thing where a user would carry a bluetooth tag and on the server we would
read the BLE tag and perform a simple Decision Tree based classification and guess which room the tag was in.
The dashboard was written in PHP with XMPP being the protocol used between the iot sensors (PCDuinos if
I remember correctly).

This simple idea kind of folowed me around, in undergrad college I wrote a simple app that used AR to show
directions within our school of computing. It was very far from a working solution as we did not have an accurate
map to work and align with. Now fast forward to 2025 and I am now married and have to go shopping for gifts. While my wife
was shopping in a big Shopping Mall in Singapore. I was bored in a corner, so I decided to see if I could vibe code
something on my phone. Particularly, I was curious if it was possible to try to perform localization in the shopping mall
with our new found VLM based technologies.

## VLMs and reading maps

Generally if a user looks at a map in a shopping mall, he or she is greeted with something like this:

![floorplan](test_floorplan.webp)

This floorplan is sufficient for humans to navigate. So what about machines? Is there a way for them to use VLMs 
for localization purposes. Lets start simply: What features are on these maps? Well, there are markings for corridors,
shops and toilets. For simplicity's sake lets start with shops:

![gemini](docs/images/gemini_convo.png)

This got my head spinning. Maybe we could simply code out a localization system that uses semantic maps for
figuring out where a user is within a building. So I got prototyping over the weekend. I vibed out an annotation tool
and a tool for parsing the annotated files. The annotation tool is available [here](editor/corridor_annotation.html).
It looks something like this:

![annot_tool](docs/images/floorplan_annotator.png)

It was amazing that I could do this in two prompts. In general I've found vibe coding to be great for building such one-of tools. After that we post-process the annotations. For each point on the corridor we sample potential locations where the list of shops are visible.

```python
def preprocess_visible_shops(annotations, grid, grid_info, radius=100):
    """
    Go through all the corridor points and find visible shops.
    """
    visible_shops = {}
    explored = set()
    for annotation in annotations:
        if annotation.get('type') != 'corridor':
            continue
        
        points = annotation.get('points', [])
        if not points:
            continue
        
        for point in points:
            cx = int(point['x'])
            cy = int(point['y'])
            if (cx, cy) in explored:
                continue
            explored.add((cx, cy))
            # Sample visible shops in all directions
            for dir in range(0, 360, 30):  # Sample every 30 degrees
                shops = sample_grid_visible_shops(grid, grid_info, cx, cy, dir, fov=60, radius=radius)
                if shops in visible_shops:
                    visible_shops[shops].append((cx, cy, dir))
                else:
                    visible_shops[shops] = [(cx, cy, dir)]
    
    return visible_shops
```

Next we write a small API to query the shapes and return a potential pose

```python
async def upload_image(file: UploadFile = File(...)):
    # You can process the file here (e.g., save, analyze, etc.)
    contents = await file.read()
    # Forward the image contents to Gemini with a prompt template
    image_part = {
        "mime_type": file.content_type,
        "data": contents
    }

    # The google.generativeai (Gemini) API is synchronous as of now.
    # You cannot use async/await directly with it.
    # If you want to avoid blocking, run it in a thread pool:

    def call_gemini():
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
        #return response.text

    gemini_result = await asyncio.to_thread(call_gemini)
    return JSONResponse({
        search_and_mathc_shops(

        )
    })
```