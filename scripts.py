import glob
import requests
from requests.auth import HTTPBasicAuth

from images.models import Image
from shared_models.models import Set
from shared_models.utils import get_active_cruise
from django.core.files.images import ImageFile

def get_biigle_photos():
    email = "ENTER@EMAIL.COM"
    token = "MY_BIIGLE_TOKEN"
    headers = {'Accept': 'application/json'}
    auth = HTTPBasicAuth(email, token)
    base_url ="https://biigle.de/api"

    volume_id = "VOLUME_ID"
    endpoint=f"/v1/volumes/{volume_id}/filenames"
    # get filenames
    response = requests.get(f"{base_url}{endpoint}", headers=headers, auth=auth)


    if not response.status_code==200: 
        print("bad response")
        exit()

    for img_id, filename in response.json().items():
        print(img_id)    
        print(filename)

        endpoint = f"/v1/images/{img_id}/file"
        response = requests.get(f"{base_url}{endpoint}", headers=headers, auth=auth)
        with open(filename, 'wb') as fp:
            fp.write(response.content)


def add_photos():

    cruise = get_active_cruise()
    
    for fname in glob.glob("andesOBIS/*.jpg"):
        set_num = fname.split("_")[1]

        # HACK for minagie
        mission = fname.split("_")[1]
        if mission=="16F":
            exit()
        set_num = fname.split("_")[2]

        set = Set.objects.get(set_number=set_num, cruise=cruise)

        with open(fname, 'rb') as fp:
            image_file = ImageFile(fp)
            if image_file:
                image = Image(set=set, andes_uuid=set.uuid, type='set',image=image_file)
                image.save(image_file.name, image_file)


if __name__ == "__main__":
    # get_biigle_photos()
    add_photos()
