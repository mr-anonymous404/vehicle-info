from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.json.sort_keys = False

apiKeys = {
    "test": "anon404"
}

def format_response(success: bool, data: dict, rc_number: str):
    return {
        "response": {
            "parameters": {
                "value": rc_number,
                "service": "rc info",
                "success": success
            },
            "data": [data] if data else []
        },
        "credit": "Mr. Anonymous"
    }

@app.route('/', methods=['GET'])
def root_instructions():
    response = {
        "response": {
            'status': 'active',
            'instructions': [{
                'service': 'rc info',
                'method': 'GET',
                'endpoint': '/rc?key=&rc='
            }]
        },
        "credit": "Mr. Anonymous"
    }
    return jsonify(response), 200

@app.route('/rc', methods=['GET'])
def get_rc_details():
    api_key = request.args.get('key')
    if not api_key or api_key not in apiKeys.values():
        error_data = {
            "error_code": 403,
            "message": "Access Forbidden: Invalid or Missing Api-Key"
        }
        return jsonify(format_response(False, error_data, "")), 403

    rc_number = request.args.get('rc')
    if not rc_number:
        error_data = {
            "error_code": 400,
            "message": "Missing 'rc' query parameter"
        }
        return jsonify(format_response(False, error_data, "")), 400

    rc = rc_number.strip().upper()
    url = f"https://vahanx.in/rc-search/{rc}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            final_data = {}
            cards = soup.select(".hrc-details-card")

            if not cards:
                error_data = {
                    "error_code": 404,
                    "message": f"RC details for '{rc}' not found or invalid RC"
                }
                return jsonify(format_response(False, error_data, rc)), 404

            for card in cards[:-1]:
                title_tag = card.find("h3")
                group_title = title_tag.get_text(strip=True) if title_tag else "General Information"
                
                group_data = {}
                columns = card.select(".row .col-sm-6")
                
                for col in columns:
                    key_tag = col.find("span")
                    value_tag = col.find("p")
                    
                    if key_tag and value_tag:
                        key = key_tag.get_text(strip=True)
                        value = value_tag.get_text(strip=True)
                        group_data[key] = value
                        
                if group_data:
                    final_data[group_title] = group_data

            return jsonify(format_response(True, final_data, rc)), 200

        elif response.status_code == 404:
            error_data = {
                "error_code": 404,
                "message": f"RC details for '{rc}' not found"
            }
            return jsonify(format_response(False, error_data, rc)), 404

        else:
            error_data = {
                "error_code": response.status_code,
                "message": f"Failed to fetch RC details for '{rc}'"
            }
            return jsonify(format_response(False, error_data, rc)), response.status_code

    except requests.RequestException as e:
        error_data = {
            "error_code": 500,
            "message": f"Internal server error: {str(e)}"
        }
        return jsonify(format_response(False, error_data, rc)), 500

if __name__ == '__main__':
    app.run(debug=True)
