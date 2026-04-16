import argparse
from flask import Flask
from flask import Response
from lrucache import LruCache



cache  = None
app    = Flask(__name__)
header = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization'
}


@app.route('/<path:video>/<path:path>')
def get_endpoint(video, path) -> Response:

    val, hit, status = cache.get(f'{video}/{path}', video)
    
    if hit:
        return Response(
            val,
            status=status,
            headers=header
        )
    elif status != 200:
        val = 'Error: Failed to retrieve data from the cloud server'

    return Response(
        val,
        status=status,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        }
    )

def create_parser():
    arg_parser = argparse.ArgumentParser(description="Edge Server")
    arg_parser.add_argument("--cache-size", type=int, default=2*1024*1024*1024)
    arg_parser.add_argument("--endpoint", type=str, default='http://10.0.1.51')

    return arg_parser

### MAIN
if __name__ == "__main__":
    parser = create_parser()
    args   = parser.parse_args()
    cache  = LruCache(max_size=args.cache_size, endpoit=args.endpoint)

    app.run(host='0.0.0.0', port=5000, debug=True)
### EOF