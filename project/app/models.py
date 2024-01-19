from django.db import models
# Create your models here.

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=15)
    monthly_salary = models.IntegerField()
    approved_limit = models.IntegerField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Loan(models.Model):
    customer_id = models.CharField(max_length=255)  # Add customer_id field
    loan_id = models.AutoField(primary_key=True)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    emis_paid_on_time = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"Loan ID: {self.loan_id}, Customer ID: {self.customer_id}"