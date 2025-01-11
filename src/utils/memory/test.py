# Add Block
import requests
import json

url = "https://api.notion.com/v1/blocks/17830c2067b481d7aea4c6cb8e27ed45/children"

payload = json.dumps({
  "children": [
    {
      "object": "block",
      "type": "heading_2",
      "heading_2": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Lacinato kale"
            }
          }
        ]
      }
    },
    {
      "object": "block",
      "type": "paragraph",
      "paragraph": {
        "rich_text": [
          {
            "type": "text",
            "text": {
              "content": "Lacinato kale is a variety of kale with a long tradition in Italian cuisine, especially that of Tuscany.",
              "link": {
                "url": "https://en.wikipedia.org/wiki/Lacinato_kale"
              }
            }
          }
        ]
      }
    }
  ]
})
headers = {
  'Authorization': 'Bearer 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',
  'Content-Type': 'application/json',
  'Notion-Version': '2022-06-28'
}

response = requests.request("PATCH", url, headers=headers, data=payload)

print(response.text)