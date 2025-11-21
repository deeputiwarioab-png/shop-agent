import httpx
import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ShopifyClient:
    def __init__(self, shop_url: str, access_token: str):
        """
        Initialize the Shopify Client.
        
        :param shop_url: The URL of the Shopify store (e.g., "my-shop.myshopify.com").
        :param access_token: The Admin API access token.
        """
        self.shop_url = shop_url.replace("https://", "").replace("http://", "").strip("/")
        self.access_token = access_token
        self.base_url = f"https://{self.shop_url}/admin/api/2024-01/graphql.json"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

    async def fetch_all_products(self) -> List[Dict[str, Any]]:
        """
        Fetch all products from the Shopify store using cursor-based pagination.
        """
        products = []
        has_next_page = True
        cursor = None

        query = """
        query ($cursor: String) {
          products(first: 50, after: $cursor) {
            edges {
              node {
                id
                title
                descriptionHtml
                handle
                tags
                vendor
                productType
                totalInventory
                priceRangeV2 {
                  minVariantPrice {
                    amount
                    currencyCode
                  }
                }
                images(first: 1) {
                  edges {
                    node {
                      url
                      altText
                    }
                  }
                }
                variants(first: 10) {
                  edges {
                    node {
                      id
                      title
                      price
                      sku
                      availableForSale
                    }
                  }
                }
              }
              cursor
            }
            pageInfo {
              hasNextPage
            }
          }
        }
        """

        async with httpx.AsyncClient() as client:
            while has_next_page:
                variables = {"cursor": cursor}
                try:
                    response = await client.post(
                        self.base_url,
                        json={"query": query, "variables": variables},
                        headers=self.headers,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if "errors" in data:
                        logger.error(f"Shopify GraphQL Errors: {data['errors']}")
                        break

                    products_data = data.get("data", {}).get("products", {})
                    edges = products_data.get("edges", [])
                    
                    for edge in edges:
                        products.append(edge["node"])
                        cursor = edge["cursor"]

                    has_next_page = products_data.get("pageInfo", {}).get("hasNextPage", False)
                    logger.info(f"Fetched {len(products)} products so far...")

                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error occurred: {e}")
                    break
                except Exception as e:
                    logger.error(f"An error occurred: {e}")
                    break

        return products
