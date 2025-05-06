import json
import boto3
import base64
from urllib.parse import parse_qs

BUCKET_NAME = 's3-image-clipper-bucket'
s3 = boto3.client('s3')

def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    path = event.get("path", "")

    if method == "POST" and path == "/upload":
        return handle_upload(event)
    elif method == "POST" and path == "/delete":
        return handle_delete(event)
    else:
        return render_gallery()


def handle_upload(event):
    try:
        print("UPLOAD EVENT:", json.dumps(event))
        body = json.loads(event['body'])
        filename = body['filename']
        file_data = base64.b64decode(body['fileData'])
        content_type = body.get('contentType', 'image/jpeg')

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=file_data,
            ContentType=content_type
        )

        return {
            "statusCode": 200,
            "headers": {
                "Location": "/",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": json.dumps({"message": "Upload success"})
        }

    except Exception as e:
        print("UPLOAD ERROR:", str(e))
        return {
            "statusCode": 500,
            "body": f"Upload failed: {str(e)}"
        }


def handle_delete(event):
    try:
        print("DELETE EVENT:", event)
        body = event["body"]
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode()

        parsed = parse_qs(body)
        keys = parsed.get("delete_keys", [])

        for key in keys:
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)

        return {
            "statusCode": 302, 
            "headers": {
                "Location": "https://oscm2ugtg6.execute-api.ap-northeast-1.amazonaws.com/prod/image-clipper-page",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            },
            "body": ""
        }

    except Exception as e:
        print("DELETE ERROR:", str(e))
        return {
            "statusCode": 500,
            "body": f"Delete failed: {str(e)}"
        }


def render_gallery():
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
    contents = objects.get('Contents')
    image_keys = []

    if contents:
        image_keys = [obj['Key'] for obj in contents if obj['Key'].lower().endswith(('jpg', 'jpeg', 'png'))][:100]

    image_tags = ""
    for key in image_keys:
        url = f"https://{BUCKET_NAME}.s3.ap-northeast-1.amazonaws.com/{key}"
        image_tags += """
        <div class="image-container">
            <input type="checkbox" class="delete-checkbox" name="delete_keys" value="{key}" style="display: none;">
            <img src="{url}" alt="{key}" onclick="enlargeImage(this)">
        </div>
        """.format(key=key, url=url)

    html_template = """
    <html>
    <head>
        <title>My Image Memo</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; }}
            .image-container {{ display: inline-block; margin: 10px; position: relative; }}
            img {{ width: 150px; height: 150px; object-fit: cover; cursor: pointer; border: 1px solid #ccc; border-radius: 8px; }}
            .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.8); }}
            .modal-content {{ margin: 5% auto; display: block; max-width: 90vw; max-height: 90vh; border-radius: 8px; box-shadow: 0 0 10px #fff;}}
        </style>
        <script>
            function toggleDeleteMode() {{
                const checkboxes = document.querySelectorAll('.delete-checkbox');
                const isVisible = checkboxes[0] && checkboxes[0].style.display === 'inline-block';
                checkboxes.forEach(cb => cb.style.display = isVisible ? 'none' : 'inline-block');
                document.getElementById('delete-submit').style.display = isVisible ? 'none' : 'inline-block';
            }}

            function enlargeImage(img) {{
                const modal = document.getElementById('modal');
                const modalImg = document.getElementById('modal-img');
                modal.style.display = 'block';
                modalImg.src = img.src;
            }}

            function closeModal() {{
                document.getElementById('modal').style.display = 'none';
            }}

            //Upload button addEventListener
            function generateFilename(mimeType) {{
                const ext = mimeType.split('/')[1] || 'jpg';
                const uuid = crypto.randomUUID(); // UUID creation
                return `photo-${{uuid}}.${{ext}}`;
            }}
            
            document.addEventListener("DOMContentLoaded", function() {{
                const form = document.getElementById("uploadForm");
                const fileInput = document.getElementById("fileInput");
                const fileNameDisplay = document.getElementById("fileName");
             
                fileInput.addEventListener("change", function() {{
                     if (fileInput.files.length > 0) {{
                        const file = fileInput.files[0];
                        let nameToDisplay = file.name;
        
                        if (!nameToDisplay || nameToDisplay.toLowerCase() === "image.jpg") {{
                            nameToDisplay = generateFilename(file.type);
                        }}
        
                        fileInput.dataset.generatedFilename = nameToDisplay;
                        fileNameDisplay.textContent = `Selected file: ${{nameToDisplay}}`;
                     }} else {{
                         fileNameDisplay.textContent = "No file selected";
                     }}
                }});
                 
                form.addEventListener("submit", async function(e) {{
                    e.preventDefault();
                    const fileInput = document.getElementById("fileInput");
                    if (!fileInput.files.length) return alert("Please select a file.");
                    const file = fileInput.files[0];
                    const reader = new FileReader();

                    reader.onload = async function() {{
                        if (!reader.result) {{
                            alert("Failed to read file");
                            return;
                        }}
                        const base64Data = reader.result.split(',')[1];
                        const res = await fetch("https://oscm2ugtg6.execute-api.ap-northeast-1.amazonaws.com/prod/upload", {{
                            method: "POST",
                            headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify({{
                                filename: file.name,
                                contentType: file.type,
                                fileData: base64Data
                            }})
                        }});
                        if (res.ok) {{
                            window.location.reload();
                        }} else {{
                            alert("Upload failed.");
                        }}
                    }};
                    reader.readAsDataURL(file);
                }});
            }});
        </script>
    </head>
    <body>
        <h1>Image Clipper</h1>

        <form id="uploadForm">
            <input type="file" id="fileInput" name="file" accept="image/*;capture=camera">
            <p id="fileName">No file selected</p>
            <button type="submit">Upload Image</button>
        </form>

        <button onclick="toggleDeleteMode()">Delete Images</button>

        <form action="https://oscm2ugtg6.execute-api.ap-northeast-1.amazonaws.com/prod/delete" method="POST">
            <div>{image_tags}</div>
            <button id="delete-submit" type="submit" style="display: none;">Confirm Delete</button>
        </form>

        <div id="modal" class="modal" onclick="closeModal()">
            <img class="modal-content" id="modal-img">
        </div>
    </body>
    </html>
    """

    html_content = html_template.format(image_tags=image_tags)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': html_content
    }
