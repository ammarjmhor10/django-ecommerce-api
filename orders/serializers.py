from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer class for serializing order items
    """
    price = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'quantity',
                  'price', 'cost', 'created_at', 'updated_at', )
        read_only_fields = ('order', )

    def validate(self, validated_data):
        order_quantity = validated_data['quantity']
        product_quantity = validated_data['product'].quantity

        if(order_quantity > product_quantity):
            error = {'quantity': _('Ordered quantity is more than the stock.')}
            raise serializers.ValidationError(error)

        return validated_data

    def get_price(self, obj):
        return obj.product.price

    def get_cost(self, obj):
        return obj.cost


class OrderReadSerializer(serializers.ModelSerializer):
    """
    Serializer class for reading orders
    """
    buyer = serializers.CharField(source='buyer.get_full_name', read_only=True)
    order_items = OrderItemSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = ('id', 'buyer', 'order_items',
                  'status', 'created_at', 'updated_at')


class OrderWriteSerializer(serializers.ModelSerializer):
    """
    Serializer class for writing orders
    """
    buyer = serializers.HiddenField(default=serializers.CurrentUserDefault())
    order_items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ('id', 'buyer', 'status', 'order_items',
                  'created_at', 'updated_at',)

    def create(self, validated_data):
        orders_data = validated_data.pop('order_items')
        order = Order.objects.create(**validated_data)

        for order_data in orders_data:
            OrderItem.objects.create(order=order, **order_data)

        return order

    def update(self, instance, validated_data):
        orders_data = validated_data.pop('order_items', None)
        orders = list((instance.order_items).all())

        instance.status = validated_data.get('status', instance.status)
        instance.save()

        if orders_data:
            for order_data in orders_data:
                order = orders.pop(0)
                order.product = order_data.get('product', order.product)
                order.quantity = order_data.get('quantity', order.quantity)
                order.save()

        return instance