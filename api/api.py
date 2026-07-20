import os
from io import BytesIO
from PIL import Image
from .. import network

def load_brawlers_data():
    """Download brawler icons from Brawlify API. Safe to call at startup."""
    brawlers_url = "https://api.brawlify.com/v1/brawlers"
    try:
        response = network.get(brawlers_url)
        brawlers_data = response.json()['list']
    except Exception as e:
        print(f"Warning: Could not fetch brawler icons: {e}")
        return

    assets_dir = os.path.join(os.path.dirname(__file__), "assets", "brawler_icons2")
    os.makedirs(assets_dir, exist_ok=True)

    for brawler_obj in brawlers_data:
        try:
            icon_url = brawler_obj['imageUrl2']
            img_response = network.get(icon_url)
            image = Image.open(BytesIO(img_response.content))
            brawler_name = str(brawler_obj['name']).lower()
            brawler_name = os.path.basename(brawler_name).replace('.', '').replace('/', '').replace('\\', '')
            image.save(os.path.join(assets_dir, f"{brawler_name}.png"))
        except Exception as e:
            print(f"Warning: Could not download icon for {brawler_obj.get('name')}: {e}")
