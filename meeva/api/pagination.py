from rest_framework.pagination import PageNumberPagination


class OptionalPageNumberPagination(PageNumberPagination):
    """Paginate only if the request asks for it.

    - Default behavior (no `page` and no `page_size` query param): return full list (backward compatible).
    - If `page` is provided (or `page_size`), return a paginated response.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        has_page = request.query_params.get(self.page_query_param) is not None
        has_page_size = request.query_params.get(self.page_size_query_param) is not None
        if not has_page and not has_page_size:
            return None
        return super().paginate_queryset(queryset, request, view=view)
