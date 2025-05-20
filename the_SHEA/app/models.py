from django.db import models

class Product(models.Model):
    website = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    sale = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sizes = models.CharField(max_length=255, null=True, blank=True)
    colors = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    images = models.TextField(null=True, blank=True)
    path = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"