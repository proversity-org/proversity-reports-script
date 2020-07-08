"""
Module that contains common functions to perform external request.
"""
import requests


def request_handler(request_url, request_data, request_type, request_headers, query_params):
    """
    Request the provided data.

    Args:
        request_url: URL of the API endpoint to request the report generation or report data.
        request_data: Dict that contains the request body.
        request_type: POST or GET request.
        request_headers: Dict that contains the request headers.
        query_params: Dict that contains the query params that will be included in the request.
    Returns:
        JSON response.
    """
    if request_type == 'POST':
        request_response = requests.post(
            request_url,
            headers=request_headers,
            json=request_data,
            params=query_params,
        )
    elif request_type == 'GET':
        request_response = requests.get(request_url, headers=request_headers, params=query_params)
    else:
        print('Request type {} not supported.'.format(request_type))
        exit()

    status_code = request_response.status_code

    if status_code in (202, 200):
        return request_response.json()

    print('Request to {} got an unexpected response {}'.format(
        request_url,
        status_code,
    ))
    exit()
