from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class for the admin panel to allow flexible page sizes
    while maintaining a safe upper limit.
    """

    # The default number of items to return per page.
    page_size = 20

    # The query parameter that allows the client to set the page size.
    # e.g., /api/v1/.../?page_size=1000
    page_size_query_param = "page_size"

    # The maximum number of items the client is allowed to request per page.
    # This is a crucial safeguard against performance issues or DoS attacks.
    max_page_size = 1000
