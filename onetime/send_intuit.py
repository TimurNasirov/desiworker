from requests import post

post('https://nta.desicarscenter.com/webhook/intuit', json={
    "eventNotifications": [
        {
            "realmId": "310687",
            "dataChangeEvent": {
                "entities": [
                    {
                        "id": "4243",
                        "operation": "Update",
                        "name": "Invoice",
                        "lastUpdated": "2025-05-25T17:14:26.387Z"
                    }
                ]
            }
        }
    ]
})