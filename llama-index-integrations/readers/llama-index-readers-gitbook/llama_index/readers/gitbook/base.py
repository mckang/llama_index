from typing import List, Optional

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from llama_index.readers.gitbook.gitbook_client import GitbookClient

VALID_METADATA_FIELDS = {"path", "title", "description", "parent"}


class SimpleGitbookReader(BaseReader):
    """Simple gitbook reader.

    Convert each gitbook page into Document used by LlamaIndex.

    Args:
        api_token (str): Gitbook API Token.
        api_url (str): Gitbook API Endpoint.
    """

    def __init__(self, api_token: str, api_url: str = None) -> None:
        """Initialize with parameters."""
        self.client = GitbookClient(api_token, api_url)

    def load_data(
        self,
        space_id: str,
        metadata_names: Optional[List[str]] = None,
        show_progress=False,
    ) -> List[Document]:
        """Load data from the input directory.

        Args:
            space_id (str): Gitbook space id
            metadata_names (Optional[List[str]]): names of the fields to be added
                to the metadata attribute of the Document.
                only 'path', 'title', 'description', 'parent' are available
                Defaults to None
            show_progress (bool, optional): Show progress bar. Defaults to False

        Returns:
            List[Document]: A list of documents.

        """
        if metadata_names:
            invalid_fields = set(metadata_names) - VALID_METADATA_FIELDS
            if invalid_fields:
                raise ValueError(
                    f"Invalid metadata fields: {', '.join(invalid_fields)}"
                )

        documents = []
        pages = self.client.list_pages(space_id)

        if show_progress:
            from tqdm import tqdm

            iterator = tqdm(pages, desc="Downloading pages")
        else:
            iterator = pages

        for page in iterator:
            id = page.get("id")
            content = self.client.get_page_markdown(space_id, id)
            if not content:
                print(f"Warning: No content found for page ID {id}. Skipping...")
                continue

            if metadata_names is None:
                documents.append(
                    Document(text=content, id_=id, metadata={"path": page.get("path")})
                )
            else:
                try:
                    metadata = {name: page.get(name) for name in metadata_names}
                except KeyError as err:
                    raise ValueError(
                        f"{err.args[0]} field is not available. Choose from {', '.join(VALID_METADATA_FIELDS)}"
                    ) from err
                documents.append(Document(text=content, id_=id, metadata=metadata))

        return documents
