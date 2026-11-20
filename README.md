# Product Recall Alert API

A REST API that lets users register products they sell or own and checks them against U.S. Consumer Product Safety Commission (CPSC) recalls.

Built with Python and FastAPI. Recall data comes from the public CPSC Recalls API (https://www.saferproducts.gov/RestWebServices/Recall).

## Team

| Team Member | Part |
|---|---|
| Sneha (Member 1) | Products: product model, storage, CRUD |
| Abhirup (Member 2) | CPSC integration: recall model, CPSC client, caching, recall search |
| Swathi (Member 3) | Matching and alerts: product recalls, alerts |



## Endpoints

| Method | Endpoint | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/` | Welcome message and links to every resource | 200 | |
| POST | `/products` | Register a product | 201 | 400, 409, 415 |
| GET | `/products?category=&brand=&offset=0&limit=20` | List products, filtered and paged | 200 | 400 |
| GET | `/products/{id}` | Get one product | 200 | 404 |
| PUT | `/products/{id}` | Update a product | 200 | 400, 404, 415 |
| DELETE | `/products/{id}` | Delete a product | 200 | 404 |
| GET | `/recalls?query=crib&offset=0&limit=20` | Search CPSC recalls by product name | 200 | 400, 502, 504 |




### Search recalls

`GET /recalls?query=crib&limit=1`

Response `200`:

```json
{
  "query": "crib",
  "total_found": 85,
  "returned": 1,
  "recalls": [
    {
      "recall_id": 10001,
      "recall_number": "25123",
      "title": "Example Crib Recall",
      "date": "2025-06-10",
      "hazard": "Fall hazard",
      "remedy": "Refund",
      "products": ["Baby crib"],
      "manufacturers": ["Example Co."],
      "url": "https://www.cpsc.gov/Recalls/..."
    }
  ]
}
```

(Values above are illustrative; real results come live from CPSC.)

## Errors

All errors return JSON in the form `{"detail": "message"}`.

| Code | When |
|---|---|
| 400 | Wrong format: missing or invalid field, empty name, query shorter than 2 characters, or trying to change a product's ID |
| 404 | Product not found |
| 409 | Product ID already exists |
| 415 | POST or PUT sent without `Content-Type: application/json` |
| 502 | CPSC service is down or returned bad data |
| 504 | CPSC service timed out (15 seconds) |
| 500 | Unexpected server error (returned as JSON, never a crash page) |




## Tests

```
pytest -v
```

The tests fake the CPSC API and keep products in memory, so they run offline and never change `products.json`.

<img width="1459" height="951" alt="Screenshot 2026-11-20 at 3 05 07 AM" src="https://github.com/user-attachments/assets/8c6f02ab-188f-448c-a2d6-b9059b697c4d" />

##POSTMAN TEST REUSLTS

search recalls

<img width="1275" height="901" alt="image" src="https://github.com/user-attachments/assets/b1dc3fac-d451-4fcf-a030-e6e5a216b9b4" />

next page

<img width="1275" height="901" alt="image" src="https://github.com/user-attachments/assets/9dfc29ce-1fd4-46a6-986a-0610c85b8b9c" />

wrong format

<img width="1275" height="901" alt="image" src="https://github.com/user-attachments/assets/040705cf-f445-4b3f-990c-670a5df16287" />

<img width="1275" height="901" alt="image" src="https://github.com/user-attachments/assets/071a236e-617f-4966-a1cd-922912383c28" />

the PUT fixed

<img width="1275" height="901" alt="image" src="https://github.com/user-attachments/assets/38492068-725d-49f6-a835-34a35afe94b0" />


