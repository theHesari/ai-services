from typing import Dict, Any, List
import requests
from abc import ABC, abstractmethod
from config.logging_config import get_logger


class CMSConnector(ABC):
    """Abstract base class for CMS connectors"""

    @abstractmethod
    def publish_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to CMS"""
        pass

    @abstractmethod
    def save_draft(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Save content as draft in WordPress"""

        post_data = {
            "title": content["title"],
            "content": content["content"],
            "status": "draft",
            "meta_description": content.get("meta_description", ""),
            "tags": content.get("tags", []),
        }

        try:
            response = requests.post(
                f"{self.api_url}/posts",
                json=post_data,
                auth=(self.username, self.password),
            )

            if response.status_code == 201:
                return {
                    "success": True,
                    "draft_id": response.json()["id"],
                    "edit_url": f"{self.site_url}/wp-admin/post.php?post={response.json()['id']}&action=edit",
                }
            else:
                return {"success": False, "error": response.text}

        except Exception as e:
            return {"success": False, "error": str(e)}


class NotionCMSConnector(CMSConnector):
    def __init__(self, notion_config: Dict[str, str]):
        self.logger = get_logger(__name__)
        self.token = notion_config["token"]
        self.database_id = notion_config["database_id"]
        self.api_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self.logger.info("Notion CMS Connector initialized")

    def publish_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Publish content to Notion"""
        self.logger.info(
            f"Publishing content to Notion: {content.get('title', 'Untitled')}"
        )
        result = self._create_notion_page(content, published=True)
        if result.get("success"):
            self.logger.info(
                f"✅ Content published successfully to Notion: {result.get('page_id')}"
            )
        else:
            self.logger.error(
                f"❌ Failed to publish content to Notion: {result.get('error')}"
            )
        return result

    def save_draft(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Save content as draft in Notion"""
        self.logger.info(f"Saving draft to Notion: {content.get('title', 'Untitled')}")
        result = self._create_notion_page(content, published=False)
        if result.get("success"):
            self.logger.info(
                f"✅ Draft saved successfully to Notion: {result.get('page_id')}"
            )
        else:
            self.logger.error(
                f"❌ Failed to save draft to Notion: {result.get('error')}"
            )
        return result

    def _create_notion_page(
        self, content: Dict[str, Any], published: bool = False
    ) -> Dict[str, Any]:
        """Create page in Notion database"""
        self.logger.debug(
            f"Creating Notion page: {content.get('title')} (published: {published})"
        )

        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": content["title"]}}]},
                "Status": {"select": {"name": "Published" if published else "Draft"}},
                "Word Count": {"number": content.get("word_count", 0)},
                "Tags": {
                    "multi_select": [{"name": tag} for tag in content.get("tags", [])]
                },
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": content["content"]}}
                        ]
                    },
                }
            ],
        }

        try:
            self.logger.debug("Sending request to Notion API...")
            response = requests.post(
                f"{self.api_url}/pages", json=page_data, headers=self.headers
            )

            if response.status_code == 200:
                self.logger.debug(
                    f"Notion API response successful: {response.status_code}"
                )
                return {
                    "success": True,
                    "page_id": response.json()["id"],
                    "url": response.json()["url"],
                }
            else:
                self.logger.error(
                    f"Notion API error: {response.status_code} - {response.text}"
                )
                return {"success": False, "error": response.text}

        except Exception as e:
            self.logger.error(f"Notion API request failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
