from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class RoleBasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_page_size(self, request, *args, **kwargs):

        raw_page_size = request.query_params.get(self.page_size_query_param)

        if raw_page_size is None:
            return self.page_size

        try:
            page_size = int(raw_page_size)
        except:
            return self.page_size

        user = request.user

        if not user.is_authenticated or (not user.is_staff and not user.is_superuser):
            max_allowed = 10
        else:
            max_allowed = 100

        if page_size > max_allowed:
            return max_allowed
        if page_size <= 0:
            return self.page_size

        return page_size


    def get_paginated_response(self, data):
        return Response(
            {
             'total_items': self.page.paginator.count,
             'total_pages': self.page.paginator.num_pages,
             'current_page': self.page.number,
             'next_page': self.get_next_link(),
             'previous_page': self.get_previous_link(),
             'results': data,
             }
        )

