import json

def lambda_handler(event, context):
    html_content = """
    <html>
        <head>
            <title>Lambda Web Page</title>
        </head>
        <body>
            <h1>Welcome to my Lambda-powered Web Page!</h1>
            <pHi theree!</p>
        </body>
    </html>
    """

    response = {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': html_content
    }

    return response
