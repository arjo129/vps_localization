# From Photos to Positions: Prototyping VLM-Based Indoor Maps


> **Disclaimer:**  
> This project was completed entirely on personal time and hardware. It is not 
> affiliated with, endorsed by, or representative of any institutions
> or organizations with which I am affiliated. The views and opinions expressed herein 
> are solely my own and do not represent those of my employer or any associated institutions.


> :warning: This code is no way near production ready. I don't intend it to be. IF you want to reproduce the experiment follow the instructions provided.


This is a proof-of-concept of an indoor positioning system based on the use of VLMs. It is the result of a bored husband waiting for his wife to finish shopping at sephora. Read more in the blog post [here](https://arjo129.github.io/blog/5-7-2025-From-Photos-To-Positions-Prototyping.html).

## To Create a Floorplan

There is an editor that allows you to create a floorplan:
![floorplananot](docs/images/floorplan_annotator.png)

To run this, simply go to the page:
https://arjo129.github.io/vps_localization/editor/corridor_annotation.html

## To create a pickle file

This is for converting the annotated map into something that can be used later for matching against the real world. The script essentially samples all points along a corridor and guesses which shops will be visible in a single camera frame. Its super hacky so you're likely going to have to edit hardcoded file paths inside.
```
uv run python plot_polygons.py
```

## To "localize" against your own image

You can simply run the following:
```
export GOOGLE_API_KEY=<YOUR_GEMINI_KEY>
uv run python estimate_pose.py test.jpg
```
