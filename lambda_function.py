import json
import boto3
import os

# Replace with your actual bucket name
BUCKET_NAME = 'summerhill-s3-image-bucket'

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # List image files from S3 (limit to 100)
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
    # image_keys = [obj['Key'] for obj in objects.get('Contents', []) if obj['Key'].lower().endswith(('jpg', 'jpeg', 'png'))][:100]

    # Safely get the list of image keys (if any)
    contents = objects.get('Contents')
    image_keys = []

    if contents:
    image_keys = [obj['Key'] for obj in contents if obj['Key'].lower().endswith(('jpg', 'jpeg', 'png'))][:100]


    # Build image HTML
    image_tags = ""
    for key in image_keys:
        url = f"https://{BUCKET_NAME}.s3.ap-northeast-1.amazonaws.com/{key}"
        image_tags += f"""
        <div class="image-container">
            <input type="checkbox" class="delete-checkbox" name="delete_keys" value="{key}" style="display: none;">
            <img src="{url}" alt="{key}" onclick="enlargeImage(this)">
        </div>
        """

    # Build HTML response
    html_content = f"""
    <html>
    <head>
        <title>My Image Memo</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; }}
            .image-container {{ display: inline-block; margin: 10px; position: relative; }}
            img {{ width: 150px; height: 150px; object-fit: cover; cursor: pointer; border: 1px solid #ccc; border-radius: 8px; }}
            .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.8); }}
            .modal-content {{ margin: 5% auto; display: block; max-width: 80%; }}
        </style>
        <script>
            // Toggle delete checkboxes
            function toggleDeleteMode() {{
                const checkboxes = document.querySelectorAll('.delete-checkbox');
                const isVisible = checkboxes[0] && checkboxes[0].style.display === 'inline-block';
                checkboxes.forEach(cb => cb.style.display = isVisible ? 'none' : 'inline-block');
                document.getElementById('delete-submit').style.display = isVisible ? 'none' : 'inline-block';
            }}

            // Show image in fullscreen modal
            function enlargeImage(img) {{
                const modal = document.getElementById('modal');
                const modalImg = document.getElementById('modal-img');
                modal.style.display = 'block';
                modalImg.src = img.src;
            }}

            function closeModal() {{
                document.getElementById('modal').style.display = 'none';
            }}
        </script>
    </head>
    <body>
        <h1>My Image Memo</h1>

        <form action="/upload" method="POST" enctype="multipart/form-data">
            <input type="file" name="file">
            <button type="submit">Upload Image</button>
        </form>

        <button onclick="toggleDeleteMode()">Delete Images</button>

        <form action="/delete" method="POST">
            <div>{image_tags}</div>
            <button id="delete-submit" type="submit" style="display: none;">Confirm Delete</button>
        </form>

        <div id="modal" class="modal" onclick="closeModal()">
            <img class="modal-content" id="modal-img">
        </div>
    </body>
    </html>
    """

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': html_content
    }
