from django.db import models

class Company(models.Model):
    id = models.BigAutoField(primary_key=True)  # Primary key field for unique ID
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    year_founded = models.IntegerField(null=True, blank=True)
    industry = models.CharField(max_length=255)
    size_range = models.CharField(max_length=50)
    locality = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    linkedin_url = models.URLField(max_length=500)
    current_employee_estimate = models.IntegerField(null=True, blank=True)
    total_employee_estimate = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name



