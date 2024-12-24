import time
from lseg.data.delivery import endpoint_request

class EndpointRequest:
    @staticmethod
    def make_request(url, method="GET", body_params=None):
        method = endpoint_request.RequestMethod.GET if method == "GET" else endpoint_request.RequestMethod.POST
        request = endpoint_request.Definition(
            method=method,
            url=url,
            header_parameters={"Content-Type": "application/json"},
            body_parameters=body_params
        )
        response = request.get_data()
        if response.raw.status_code in [200, 202]:
            return response
        else:
            raise Exception(f"Error: {response.raw.status_code} - {response.raw.text}")
    
    @staticmethod
    def wait_for_response(response):
        status_url = response.raw.headers["location"]
        status = "not_started"
        while status != "succeeded" and status != "failed":
            status_response = EndpointRequest.make_request(status_url).data.raw
            status = status_response["status"]
            time.sleep(1)
        response_url = status_response["resourceLocation"]
        res_status = False
        while not res_status:
            response = EndpointRequest.make_request(response_url)
            res_status = response.is_success
            time.sleep(1)
        return response.data.raw