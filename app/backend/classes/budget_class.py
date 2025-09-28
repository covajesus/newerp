import requests

class BudgetClass:
    def get_total(user_inputs):
        url = "https://jisparking.com/api/budget/supervisortotal/"+ str(user_inputs['rol_id']) +"/"+ str(user_inputs['rut']) +"?api_token="+ str(user_inputs['api_token']) +""

        payload={}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.text
