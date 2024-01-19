from django.urls import path
from .views import *

urlpatterns = [
    path('register/', register ,name='register'),
    path('check/', check_eligibility ,name='check_eligibility'),
    path('create-loan/', create_loan,name='create_loan('),
    path('view-loan/<int:loan_id>/', view_loan, name='view_loan'),
    path('view-loans/<int:customer_id>/', view_loans_by_customer, name='view_loans_by_customer'),

]