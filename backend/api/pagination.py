from rest_framework.pagination import PageNumberPagination


class SubscriptionPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'limit'
