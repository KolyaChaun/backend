from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet

from order.models import Basket, BasketItem
from order.serializers import BasketItemSerializer, BasketSerializer
from products.models import IN_STOCK, WarehouseItem


class CreateBasket(mixins.CreateModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = BasketSerializer
    lookup_url_kwarg = "basket_id"
    queryset = Basket.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.is_authenticated:
            try:
                user_basket = Basket.objects.get(user=request.user)
                return Response(
                    {
                        "basket_id": user_basket.id,
                        "user_id": request.user.id,
                    },
                    status=HTTP_201_CREATED,
                )
            except Basket.DoesNotExist:
                serializer.save(user=request.user)
                return Response(
                    {
                        "basket_id": serializer.instance.id,
                        "user_id": request.user.id,
                    },
                    status=HTTP_201_CREATED,
                )
        else:
            serializer.save()
        return Response(
            {
                "basket_id": serializer.instance.id,
            },
            status=HTTP_201_CREATED,
        )


def _check_warehouse_availability(data):
    product_id = data.get("product")
    color_id = data.get("color")
    size_id = data.get("size")
    quantity = data.get("quantity")
    available_stock = WarehouseItem.objects.filter(
        product_id=product_id,
        color_id=color_id,
        size_id=size_id,
        status=IN_STOCK,
    ).count()
    if available_stock < quantity:
        return Response(
            {"detail": "Sorry, but this product is out of stock"},
            status=HTTP_400_BAD_REQUEST,
        )


class RetrieveUpdateDestroyBasketAPIView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = BasketItemSerializer
    queryset = BasketItem.objects.all()
    lookup_url_kwarg = "basket_item_id"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        existing_item = BasketItem.objects.filter(
            product=serializer.validated_data["product"],
            color=serializer.validated_data["color"],
            size=serializer.validated_data["size"],
            basket=kwargs["basket_id"],
        ).first()
        if existing_item:
            if warehouse_check_response := _check_warehouse_availability(
                {
                    **serializer.validated_data,
                    "quantity": serializer.validated_data["quantity"]
                    + existing_item.quantity,
                }
            ):
                return warehouse_check_response
            existing_item.quantity += serializer.validated_data["quantity"]
            existing_item.save()
            serializer = self.get_serializer(existing_item)
            return Response(serializer.data, status=HTTP_201_CREATED)
        else:
            if warehouse_check_response := _check_warehouse_availability(
                serializer.validated_data
            ):
                return warehouse_check_response
            serializer.save(**kwargs)
            return Response(serializer.data, status=HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        warehouse_check_response = _check_warehouse_availability(
            serializer.validated_data
        )
        if warehouse_check_response:
            return warehouse_check_response
        serializer.save(**kwargs)
        return Response(serializer.data, status=HTTP_200_OK)
